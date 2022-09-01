import sys
import time
import requests
import json
import argparse
import os
import threading

# TODO - switch to multiprocessing
import queue

TFC_BASE_URL = "https://app.terraform.io/api/v2"
ORGANIZATION_NAME = os.environ.get("TFC_ORG_NAME", "Nutrien")

# TODO - build constants to hold OK, failed, etc statuses


argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("--prefix", dest="prefix", action="store", type=str)
argument_parser.add_argument(
    "--token",
    "-t",
    dest="token",
    action="store",
    type=str,
    default=os.environ.get("TFC_TOKEN", None),
)
argument_parser.add_argument(
    "--parallel", "-p", dest="parallel", action="store", default=5, type=int
)
argument_parser.add_argument(
    "--auto-approve", dest="auto_approve", action="store_true", default=False
)
argument_parser.add_argument(
    "--max-checks", "-m", default=10, type=int, action="store", dest="max_checks"
)
argument_parser.add_argument(
    "--force", default=False, action="store_true", dest="force"
)


def prompt_for_input():
    v = input("apply: [y/N] ")

    if v not in ["y", "Y"]:
        print(f"received '{v}', expecting 'y' or 'Y' - exiting")
        sys.exit(0)
    else:
        print("proceeding")


def get_terraform_cloud_token():
    credentials_file = f"{os.path.expanduser('~')}/.terraform.d/credentials.tfrc.json"

    try:
        with open(credentials_file, "r") as f:
            return json.loads(f.read())["credentials"]["app.terraform.io"]["token"]
    except FileNotFoundError:
        raise Exception(
            f"\n\n ** Did not find {credentials_file}. Please run `terraform login` before running this script",
        ) from None
    except KeyError:
        raise Exception(
            f"\n\n ** Did not find 'token' key in {credentials_file}. Please run `terraform login` before running this script",
        ) from None
    except:
        raise


def get_workspaces_by_prefix(session: requests.sessions.Session, prefix):
    # https://www.terraform.io/cloud-docs/api-docs/workspaces#list-workspaces
    workspaces = {}

    resp = session.get(
        f"{TFC_BASE_URL}/organizations/{ORGANIZATION_NAME}/workspaces",
        headers={"Content-Type": "application/vnd.api+json"},
        params={"search[name]": prefix},
    )

    j = json.loads(resp.text)

    next_page = j["meta"]["pagination"]["next-page"]

    for workspace in j["data"]:
        workspaces[workspace["attributes"]["name"]] = workspace["id"]

    while next_page is not None:
        resp = session.get(
            f"{TFC_BASE_URL}/api/v2/organizations/{ORGANIZATION_NAME}/workspaces",
            headers={"Content-Type": "application/vnd.api+json"},
            params={"search[name]": prefix, "page[number]": next_page},
        )

        j = json.loads(resp.text)

        next_page = j["meta"]["pagination"]["next-page"]

        for workspace in j["data"]:
            workspaces[workspace["attributes"]["name"]] = workspace["id"]

    return workspaces


def get_workspace_latest_run_id(
    session: requests.sessions.session, workspace_id: str, workspace_name: str
):
    # https://www.terraform.io/cloud-docs/api-docs/run#list-runs-in-a-workspace
    resp = session.get(
        f"{TFC_BASE_URL}/workspaces/{workspace_id}/runs", params={"page[size]": 1}
    )

    j = json.loads(resp.text)

    if len(j["data"]) == 0:
        print(f"no data for workspace '{workspace_name}")
        print(j)
        return None

    return j["data"][0]["id"]


def get_workspace_current_run_id(session: requests.sessions.session, name: str):
    # https://www.terraform.io/cloud-docs/api-docs/workspaces#show-workspace
    resp = session.get(
        f"{TFC_BASE_URL}/organizations/{ORGANIZATION_NAME}/workspaces/{name}"
    )

    j = json.loads(resp.text)

    return j["data"]["relationships"]["current-run"]["data"]["id"]


def can_apply_plan(session: requests.sessions.session, plan_id: str):
    resp = session.get(f"{TFC_BASE_URL}/runs/{plan_id}")

    j = json.loads(resp.text)

    return j["data"]["attributes"]["actions"]["is-confirmable"]


def force_execute_run(session: requests.sessions.session, run_id: str) -> bool:
    # https://www.terraform.io/cloud-docs/api-docs/run#forcefully-execute-a-run

    try:
        # First, make sure we actually can force-execute this plan
        print(f"checking to see if we can force execute '{run_id}'")

        resp = session.get(f"{TFC_BASE_URL}/runs/{run_id}")
        # If the run is pending then it's sitting in the queue waiting for another run to finish,
        # which means we can force execute it
        status = json.loads(resp.text)["data"]["attributes"]["status"]
        if status == "pending":
            print(f"run '{run_id}' can be force executed, doing so now")

            resp = session.post(
                f"{TFC_BASE_URL}/runs/{run_id}/actions/force-execute",
                headers={"Content-Type": "application/vnd.api+json"},
            )
            print(resp.text)
            time.sleep(5)

            counter = 0
            done = False

            # TODO - variable this
            while counter < 10 and not done:
                print(f"checking status of forcefully executed run '{run_id}'")
                resp = session.get(f"{TFC_BASE_URL}/runs/{run_id}")

                status = json.loads(resp.text)["data"]["attributes"]["status"]

                if status in ["planned", "planned_and_finished"]:
                    done = True
                    print(f"successfully planned run '{run_id}'")
                elif status in ["errored", "canceled", "discarded", "force_canceled"]:
                    # done = True
                    print(f"run '{run_id}' failed with status '{status}'")
                    return False
                else:
                    print(
                        f"run '{run_id}' is '{status}'. checking again in 5 seconds (total checks: {counter}, max checks: {10})"
                    )

                counter += 1

                time.sleep(5)

            return True
        elif status == "planned":
            print(f"latest run is already planned for workspace '{workspace_name}'")
            return True
        else:
            print(f"run {run_id} is '{status}', not 'pending', cannot force execute")
    except Exception as e:
        print(f"exception while force executing run - {e}")

    return False


def apply_plan(
    session: requests.sessions.session,
    run_queue: queue.Queue,
    max_checks: int,
    force: bool,
):
    # https://www.terraform.io/cloud-docs/api-docs/run#apply-a-run
    while True:
        try:
            print("pulling new run from queue")

            run_object = run_queue.get(block=True, timeout=1)

            run_id = run_object["id"]
            force = run_object["force"]

            print(f"pulled '{run_id}' off queue (force: {force})")

            proceed = True
            if force:
                if not force_execute_run(tfc_session, run_id):
                    print(f"force execute unsuccesful for workspace '{workspace_name}'")
                    proceed = False

            if proceed:
                resp = session.post(
                    f"{TFC_BASE_URL}/runs/{run_id}/actions/apply",
                    headers={"Content-Type": "application/vnd.api+json"},
                )

                if resp.text != "null":
                    print(f"resp.text is {resp.text}")
                    if not json.loads(resp.text).get("success", False):
                        print(f"error queuing apply - {resp.text}")

                        raise Exception("error")

                print(f"queued apply for run '{run_id}'")

                # Wait for terraform cloud to do stuff
                time.sleep(2)

                counter = 0
                done = False
                # TODO - handle success notification better

                # TODO - max counter configurable
                while counter < max_checks and not done:
                    resp = session.get(f"{TFC_BASE_URL}/runs/{run_id}")

                    status = json.loads(resp.text)["data"]["attributes"]["status"]

                    if status == "applied":
                        done = True
                        print(f"successfully applied run '{run_id}'")
                    elif status == "errored":
                        done = True
                        print(f"failed to apply run '{run_id}'")
                    else:
                        print(
                            f"run '{run_id}' is '{status}'. checking again in 5 seconds (total checks: {counter}, max checks: {max_checks})"
                        )

                    counter += 1

                    time.sleep(5)

                run_queue.task_done()
            else:
                print(
                    f"run '{run_id}' encountered an issue, marking item done and moving on"
                )
                run_queue.task_done()
        except queue.Empty:
            print("queue is empty")
            break

        except Exception as e:
            print(f"exception - {e}")
            return


parsed_args = argument_parser.parse_args()

tfc_session = requests.Session()

if parsed_args.token is None:
    parsed_args.token = get_terraform_cloud_token()

tfc_session.headers.update({"Authorization": f"Bearer {parsed_args.token}"})

workspaces = get_workspaces_by_prefix(tfc_session, parsed_args.prefix)

print(f"retrieved {len(workspaces)} workspaces")

apply_queue = queue.Queue()

for workspace_name, workspace_id in workspaces.items():
    if parsed_args.force:
        print(f"force is set, retrieving latest run for workspace {workspace_name}")
        run_id = get_workspace_latest_run_id(tfc_session, workspace_id, workspace_name)
        queue_item = {"id": run_id, "force": True}
        apply_queue.put(queue_item, block=False)
        print(
            f"put item on queue for '{workspace_name}' - this run is forced and may produce unexpected behavior"
        )

    else:
        run_id = get_workspace_current_run_id(tfc_session, workspace_name)
        queue_item = {"id": run_id, "force": False}

        if can_apply_plan(tfc_session, run_id):
            apply_queue.put(queue_item, block=False)

            print(f"put item on queue for '{workspace_name}'")
        else:
            print(f"unable to apply run for workspace '{workspace_name}'")


if apply_queue.qsize() == 0:
    print("no items to apply")
    sys.exit(0)

print("workspaces to apply:")
for w in workspaces.keys():
    print(f"- {w}")


# Speak now or forever hold your peace
if not parsed_args.auto_approve:
    prompt_for_input()
else:
    print(f"auto-approve flag set, proceeding with applies")

# sys.exit(0)


applier_threads = []

for i in range(0, parsed_args.parallel):
    t = threading.Thread(
        target=apply_plan,
        args=(tfc_session, apply_queue, parsed_args.max_checks, parsed_args.force),
        daemon=True,
    )

    applier_threads.append(t)

# Start worker threads
for t in applier_threads:
    t.start()

# Give worker threads some time to start working
# If we join() immediately, threads 2-N have problems starting
time.sleep(10)
for t in applier_threads:
    t.join()

print("\n\ndone")
