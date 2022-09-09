import os
import queue
import sys

# TODO - switch to multiprocessing
import threading
import time

import requests

from tfc_tool import args, credentials, helpers, tfc_logger, workspaces

# Parse args first
parsed_args = args.setup_arguments()

logger = tfc_logger.new(parsed_args.debug)


def new_session(token_from_args):
    s = requests.Session()

    if token_from_args is None:
        token_from_args = credentials.get_terraform_cloud_token()

    s.headers.update({"Authorization": f"Bearer {token_from_args}"})

    return s


tfc_session = new_session(parsed_args.token)

ws = workspaces.Workspace(
    organization=os.environ.get("TFC_ORG_NAME", "Nutrien"),
    tfc_session=tfc_session,
    logger=logger,
)


def create_workspaces_workflow():
    # Do default logic here
    # See comment on argument itself
    if len(parsed_args.new_workspace_suffix) == 0:
        parsed_args.new_workspace_suffix = args.DEFAULT_SUFFIXES

    # User hasn't set any so use default
    if len(parsed_args.new_workspace_variable_set_ids) == 0:
        # Try to grab the env var for default
        if os.environ.get("TFC_DEFAULT_VARIABLE_SET_ID", None) is not None:
            # Don't use .get() here because I want it to blow up
            parsed_args.new_workspace_variable_set_ids = os.environ[
                "TFC_DEFAULT_VARIABLE_SET_ID"
            ].split(",")

    for suffix in parsed_args.new_workspace_suffix:
        # No prefix override passed, so we can assume the file name is just "<suffix>.tfvars"
        if parsed_args.new_workspace_plan_file_prefix is None:
            plan_file_name = f"{suffix}.tfvars"
        else:
            plan_file_name = (
                f"{parsed_args.new_workspace_plan_file_prefix}-{suffix}.tfvars"
            )
            # Make `-pfp platform-` and `-pfp platform` equivalent
            if "--" in f"{parsed_args.new_workspace_plan_file_prefix}-{suffix}.tfvars":
                plan_file_name = (
                    f"{parsed_args.new_workspace_plan_file_prefix}{suffix}.tfvars"
                )

        var_file_folder_name = ws.clean_folder_name(
            parsed_args.new_workspace_var_file_folder
        )

        ws.create_workspace(
            parsed_args.prefix,
            suffix,
            parsed_args.new_workspace_vcs_repo,
            parsed_args.new_workspace_oauth_token,
            f"{var_file_folder_name}/{plan_file_name}",
            parsed_args.new_workspace_variable_set_ids,
        )


def multi_apply_workflow():
    _workspaces = ws.get_workspaces_by_prefix(parsed_args.prefix)

    logger.debug(f"retrieved {len(_workspaces)} workspaces")

    apply_queue = queue.Queue()

    for workspace_name, workspace_id in _workspaces.items():
        if parsed_args.force:
            logger.info(
                f"force is set, retrieving latest run for workspace {workspace_name}"
            )
            run_id = ws.get_workspace_latest_run_id(workspace_id, workspace_name)
            queue_item = {"id": run_id, "force": True, "workspace_name": workspace_name}
            apply_queue.put(queue_item, block=False)
            logger.warning(
                f"put item on queue for '{workspace_name}' - this run is forced and may produce unexpected behavior"
            )

        else:
            run_id = ws.get_workspace_current_run_id(workspace_name)
            queue_item = {"id": run_id, "force": False}

            if ws.can_apply_plan(run_id):
                apply_queue.put(queue_item, block=False)

                logger.debug(f"put item on queue for '{workspace_name}'")
            else:
                logger.warning(
                    f"no plans in a state that can be applied in workspace '{workspace_name}'"
                )

    if apply_queue.qsize() == 0:
        logger.info("no items to apply")
        sys.exit(0)

    print("\nworkspaces to apply:")
    for w in _workspaces.keys():
        print(f"- {w}")

    # Speak now or forever hold your peace
    if not parsed_args.auto_approve:
        helpers.prompt_for_input()
    else:
        logger.info("auto-approve flag set, proceeding with applies")

    applier_threads = []

    for _ in range(0, parsed_args.parallel):
        t = threading.Thread(
            target=ws.apply_plan,
            args=(apply_queue, parsed_args.max_checks, parsed_args.force),
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

    logger.info("\n\ndone")


def entrypoint():
    if not parsed_args.add_workspace:
        multi_apply_workflow()
    elif parsed_args.add_workspace:
        create_workspaces_workflow()


if __name__ == "__main__":
    entrypoint()
