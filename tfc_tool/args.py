import argparse
import os

DEFAULT_SUFFIXES = "dev,sit,pre,prd"


def setup_arguments():

    argument_parser = argparse.ArgumentParser()

    # Global args
    argument_parser.add_argument(
        "--debug", "-v", dest="debug", action="store_true", default=False
    )
    argument_parser.add_argument(
        "--token",
        "-t",
        dest="token",
        action="store",
        type=str,
        default=os.environ.get("TFC_TOKEN", None),
    )

    # Multi-apply args
    argument_parser.add_argument(
        "--prefix",
        "-p",
        dest="prefix",
        action="store",
        type=str,
        help="When multi-applying workspaces, any workspace with a name matching the prefix is applied. When creating workspaces, this combines with the --suffix argument to generate workspace names",
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

    # Add workspace args
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
        # Don't store our default here: https://bugs.python.org/issue16399
        default=[],
        # e.g. -s whiz bang
        action="extend",
        nargs="+",
        dest="new_workspace_suffix",
        help=f"Override suffix when creating workspace. Defaults to '{' '.join(DEFAULT_SUFFIXES.split(','))}'",
    )
    argument_parser.add_argument(
        "--repo",
        "-r",
        action="store",
        dest="new_workspace_vcs_repo",
        help="Name of repo to connect to new workspace",
    )
    argument_parser.add_argument(
        "--oauth-token-id",
        "-o",
        action="store",
        default=os.environ.get("TFC_OAUTH_TOKEN_ID", None),
        dest="new_workspace_oauth_token",
        help="ID of OAuth token that Terraform Cloud uses to connect to VCS. Can be found in Terraform Cloud version control settings",
    )
    argument_parser.add_argument(
        "--plan-file-prefix",
        "-pfp",
        dest="new_workspace_plan_file_prefix",
        action="store",
        default=None,
        help="Prefix of variable file names, will be combined with suffix. e.g. `-pfp hello-world` comes out to TF_CLI_ARGS_plan=./var/hello-world-dev.tfvars",
    )
    argument_parser.add_argument(
        "--var-file-folder",
        "-vff",
        dest="new_workspace_var_file_folder",
        action="store",
        default="./var",
        help="Path to variable files",
    )
    argument_parser.add_argument(
        "--variable-set-ids",
        "-vids",
        dest="new_workspace_variable_set_ids",
        default=[],
        action="append",
        help="A list of Terraform Cloud variable set IDs to share with this workspace. Variable Set IDs can be found under settings > Variable sets",
    )

    return argument_parser.parse_args()
