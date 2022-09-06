import argparse
import os

DEFAULT_SUFFIXES = "dev,sit,pre,prd"


def setup_arguments():

    argument_parser = argparse.ArgumentParser()

    argument_parser.add_argument(
        "--debug", "-v", dest="debug", action="store_true", default=False
    )
    argument_parser.add_argument(
        "--prefix", "-p", dest="prefix", action="store", type=str
    )
    argument_parser.add_argument(
        "--token",
        "-t",
        dest="token",
        action="store",
        type=str,
        default=os.environ.get("TFC_TOKEN", None),
    )
    argument_parser.add_argument(
        "--parallel",
        "-w",
        dest="parallel",
        action="store",
        default=5,
        type=int,
        help="Number of worker threads to boot to do applies",
    )
    argument_parser.add_argument(
        "--auto-approve",
        dest="auto_approve",
        action="store_true",
        default=False,
        help="Don't prompt before starting applies",
    )
    argument_parser.add_argument(
        "--max-checks",
        "-m",
        default=10,
        type=int,
        action="store",
        dest="max_checks",
        help="Number of times to check the status of an operation before moving on",
    )
    argument_parser.add_argument(
        "--force",
        default=False,
        action="store_true",
        dest="force",
        help="Force run the latest run in a workspace",
    )
    argument_parser.add_argument(
        "--add-workspace",
        default=False,
        action="store_true",
        dest="add_workspace",
        help=f"Add workspaces",
    )
    argument_parser.add_argument(
        "--suffix",
        "-s",
        default=DEFAULT_SUFFIXES,
        # e.g. -s whiz bang
        action="extend",
        dest="suffix",
        help="Override suffix when creating workspace",
    )
    argument_parser.add_argument(
        "--repo",
        "-r",
        action="store",
        dest="vcs_repo",
        help="Name of repo to connect to new workspace",
    )

    return argument_parser.parse_args()
