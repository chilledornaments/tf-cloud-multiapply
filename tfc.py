import sys
import time
import requests
import json
import argparse
import os

# TODO - switch to multiprocessing
import threading
import queue

from tfc_tool import credentials, workspaces, helpers, args

# TODO - build constants to hold OK, failed, etc statuses


tfc_session = requests.Session()

parsed_args = args.setup_arguments()

if parsed_args.token is None:
    parsed_args.token = credentials.get_terraform_cloud_token()

tfc_session.headers.update({"Authorization": f"Bearer {parsed_args.token}"})

ws = workspaces.Workspace(
    organization=os.environ.get("TFC_ORG_NAME", "Nutrien"), tfc_session=tfc_session
)

_workspaces = ws.get_workspaces_by_prefix(parsed_args.prefix)

print(f"retrieved {len(_workspaces)} workspaces")

apply_queue = queue.Queue()

for workspace_name, workspace_id in _workspaces.items():
    if parsed_args.force:
        print(f"force is set, retrieving latest run for workspace {workspace_name}")
        run_id = ws.get_workspace_latest_run_id(workspace_id, workspace_name)
        queue_item = {"id": run_id, "force": True, "workspace_name": workspace_name}
        apply_queue.put(queue_item, block=False)
        print(
            f"put item on queue for '{workspace_name}' - this run is forced and may produce unexpected behavior"
        )

    else:
        run_id = ws.get_workspace_current_run_id(workspace_name)
        queue_item = {"id": run_id, "force": False}

        if ws.can_apply_plan(run_id):
            apply_queue.put(queue_item, block=False)

            print(f"put item on queue for '{workspace_name}'")
        else:
            print(f"unable to apply run for workspace '{workspace_name}'")


if apply_queue.qsize() == 0:
    print("no items to apply")
    sys.exit(0)

print("workspaces to apply:")
for w in _workspaces.keys():
    print(f"- {w}")


# Speak now or forever hold your peace
if not parsed_args.auto_approve:
    helpers.prompt_for_input()
else:
    print(f"auto-approve flag set, proceeding with applies")


applier_threads = []

for i in range(0, parsed_args.parallel):
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

print("\n\ndone")
