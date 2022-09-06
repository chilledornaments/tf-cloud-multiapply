import requests
import json
import time
import queue
import logging

TFC_BASE_URL = "https://app.terraform.io/api/v2"

# TODO - build constants to hold OK, failed, etc statuses


class Workspace:
    def __init__(
        self,
        organization: str,
        tfc_session: requests.sessions.Session,
        logger: logging.Logger,
    ):
        self.organization_name = organization
        self.tfc_session = tfc_session
        self.logger = logger

    def create_workspace(self, prefix: str, suffix: str):
        # https://www.terraform.io/cloud-docs/api-docs/workspaces#create-a-workspace
        pass

    def get_workspaces_by_prefix(self, prefix):
        # https://www.terraform.io/cloud-docs/api-docs/workspaces#list-workspaces
        w = {}

        resp = self.tfc_session.get(
            f"{TFC_BASE_URL}/organizations/{self.organization_name}/workspaces",
            headers={"Content-Type": "application/vnd.api+json"},
            params={"search[name]": prefix},
        )

        j = json.loads(resp.text)

        next_page = j["meta"]["pagination"]["next-page"]

        for workspace in j["data"]:
            w[workspace["attributes"]["name"]] = workspace["id"]

        while next_page is not None:
            resp = self.tfc_session.get(
                f"{TFC_BASE_URL}/api/v2/organizations/{self.organization_name}/workspaces",
                headers={"Content-Type": "application/vnd.api+json"},
                params={"search[name]": prefix, "page[number]": next_page},
            )

            j = json.loads(resp.text)

            next_page = j["meta"]["pagination"]["next-page"]

            for workspace in j["data"]:
                w[workspace["attributes"]["name"]] = workspace["id"]

        return w

    def get_workspace_latest_run_id(self, workspace_id: str, workspace_name: str):
        # https://www.terraform.io/cloud-docs/api-docs/run#list-runs-in-a-workspace
        resp = self.tfc_session.get(
            f"{TFC_BASE_URL}/workspaces/{workspace_id}/runs", params={"page[size]": 1}
        )

        j = json.loads(resp.text)

        if len(j["data"]) == 0:
            self.logger.error(f"no data for workspace '{workspace_name}")
            self.logger.debug(j)
            return None

        return j["data"][0]["id"]

    def get_workspace_current_run_id(self, name: str):
        # https://www.terraform.io/cloud-docs/api-docs/workspaces#show-workspace
        resp = self.tfc_session.get(
            f"{TFC_BASE_URL}/organizations/{self.organization_name}/workspaces/{name}"
        )

        j = json.loads(resp.text)

        return j["data"]["relationships"]["current-run"]["data"]["id"]

    def can_apply_plan(self, plan_id: str):
        resp = self.tfc_session.get(f"{TFC_BASE_URL}/runs/{plan_id}")

        j = json.loads(resp.text)

        return j["data"]["attributes"]["actions"]["is-confirmable"]

    def force_execute_run(self, run_id: str, workspace_name: str) -> bool:
        # https://www.terraform.io/cloud-docs/api-docs/run#forcefully-execute-a-run

        try:
            # First, make sure we actually can force-execute this plan
            self.logger.info(f"checking to see if we can force execute '{run_id}'")

            resp = self.tfc_session.get(f"{TFC_BASE_URL}/runs/{run_id}")
            # If the run is pending then it's sitting in the queue waiting for another run to finish,
            # which means we can force execute it
            status = json.loads(resp.text)["data"]["attributes"]["status"]
            if status == "pending":
                self.logger.info(f"run '{run_id}' can be force executed, doing so now")

                resp = self.tfc_session.post(
                    f"{TFC_BASE_URL}/runs/{run_id}/actions/force-execute",
                    headers={"Content-Type": "application/vnd.api+json"},
                )

                time.sleep(5)

                counter = 0
                done = False

                # TODO - variable this
                while counter < 10 and not done:
                    self.logger.info(
                        f"checking status of forcefully executed run '{run_id}'"
                    )
                    resp = self.tfc_session.get(f"{TFC_BASE_URL}/runs/{run_id}")

                    status = json.loads(resp.text)["data"]["attributes"]["status"]

                    if status in ["planned", "planned_and_finished"]:
                        done = True
                        self.logger.info(f"successfully planned run '{run_id}'")
                    elif status in [
                        "errored",
                        "canceled",
                        "discarded",
                        "force_canceled",
                    ]:
                        # done = True
                        self.logger.error(
                            f"run '{run_id}' failed with status '{status}'"
                        )
                        return False
                    else:
                        self.logger.info(
                            f"run '{run_id}' is '{status}'. checking again in 5 seconds (total checks: {counter}, max checks: {10})"
                        )

                    counter += 1

                    time.sleep(5)

                return True
            elif status == "planned":
                self.logger.info(
                    f"latest run is already planned for workspace '{workspace_name}'"
                )
                return True
            else:
                self.logger.warning(
                    f"run {run_id} is '{status}', not 'pending', cannot force execute"
                )
        except Exception as e:
            self.logger.error(f"exception while force executing run - {e}")

        return False

    def apply_plan(self, run_queue: queue.Queue, max_checks: int, force: bool):
        # https://www.terraform.io/cloud-docs/api-docs/run#apply-a-run
        while True:
            try:
                self.logger.debug("pulling new run from queue")

                run_object = run_queue.get(block=True, timeout=1)

                run_id = run_object["id"]
                force = run_object["force"]
                workspace_name = run_object["workspace_name"]

                self.logger.debug(f"pulled '{run_id}' off queue (force: {force})")

                proceed = True
                if force:
                    if not self.force_execute_run(run_id, workspace_name):
                        self.logger.error(
                            f"force execute unsuccesful for workspace '{workspace_name}'"
                        )
                        proceed = False

                if proceed:
                    resp = self.tfc_session.post(
                        f"{TFC_BASE_URL}/runs/{run_id}/actions/apply",
                        headers={"Content-Type": "application/vnd.api+json"},
                    )

                    # Something has gone wrong if resp.text != null
                    if resp.text != "null":
                        self.logger.debug(f"resp.text is {resp.text}")
                        if not json.loads(resp.text).get("success", False):
                            self.logger.error(f"error queuing apply - {resp.text}")

                            raise Exception("error")

                    self.logger.info(f"queued apply for run '{run_id}'")

                    # Wait for terraform cloud to do stuff
                    time.sleep(2)

                    counter = 0
                    done = False
                    # TODO - handle success notification better

                    # TODO - max counter configurable
                    while counter < max_checks and not done:
                        resp = self.tfc_session.get(f"{TFC_BASE_URL}/runs/{run_id}")

                        status = json.loads(resp.text)["data"]["attributes"]["status"]

                        if status == "applied":
                            done = True
                            self.logger.info(f"successfully applied run '{run_id}'")
                        elif status == "errored":
                            done = True
                            self.logger.error(f"failed to apply run '{run_id}'")
                        else:
                            self.logger.info(
                                f"run '{run_id}' is '{status}'. checking again in 5 seconds (total checks: {counter}, max checks: {max_checks})"
                            )

                        counter += 1

                        time.sleep(5)

                    run_queue.task_done()
                else:
                    self.logger.error(
                        f"run '{run_id}' encountered an issue, marking item done and moving on"
                    )
                    run_queue.task_done()
            except queue.Empty:
                self.logger.warning("queue is empty")
                break

            except Exception as e:
                self.logger.error(f"exception - {e}")
                return
