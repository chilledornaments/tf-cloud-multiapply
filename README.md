# tf-cloud-multiapply

## Installing

- Download the appropriate release for your machine
- Unzip the release
- `chmod +x tfc`
- Move the binary into your PATH

### macOS Install Notes

If you run into an error like "Apple can’t check app for malicious software", run `xattr -d com.apple.quarantine /path/to/file`

## Power User Instructions

Store the following env vars in a file that you `source` before using this tool:
- `TFC_DEFAULT_VARIABLE_SET_ID` (if creating workspaces)
    - This is a comma-separated list of variable set IDs to share with workspaces
- `TFC_OAUTH_TOKEN_ID` (if adding workspaces)
- `TFC_ORG_NAME` (if not Nutrien)
- `TFC_TOKEN` if you don't want to run `terraform login` or if you want to test against a specific account

## Apply multiple workspaces

Command: `apply`

Flags:
- `--prefix` / `-p`: apply all workspaces with this prefix. Cannot be an empty string
- `--auto-approve` / `-a`: Don't prompt for approval before starting applies
- `--force`: Forcefully apply the most recent run in the workspace
- `--timeout` / `-t`: Number of seconds to wait for a given run to apply
- `--workers` / `-w`: Number of workers to boot up
- `--gated` / `-g`: Apply runs one-at-a-time, prompting for `y` before moving on. This can be used to give yourself a chance to manually check the outcome of an apply
- `--skip`: A list of . Can be used multiple times, e.g. `--skip prd --skip pre`

Example:

`tfc apply --prefix aws-ipam-latam`

Example skipping:

`tfc apply --prefix aws-ipam-latam --skip prd --skip pre`

## Create multiple workspaces

Command: `create`

Relevant Flags:
- `--prefix` / `-p`: Prefix for workspace names
- `--suffix` / `-s`: Suffix for workspace names
- `--repo` / `-r`: Repository where Terraform code lives in the form of `<Organization>/<Repository name>`
- `--oauth-token-id` / `-i`: ID of the OAuth application used to connect to repo. Can be found under Settings > Providers
- `--var-file-prefix` / `-x`: Prefix of plan file names. Defaults to `<suffix>.tfvars`. For example, `-pfp hello-world` would yield `hello-world-dev.tfvars`. Variable files must follow either naming scheme to be picked up correctly
- `--path-to-var-files` / `-f`: Path to variable files. Defaults to `./var`. Trailing `/` are removed
- `--variable-set-ids` / `-v`: A list of variable set IDs to share with each new workspace
- `skip-vars` : Do not set the `TF_CLI_ARGS_plan` env var


Additionally, there are the following environment variables:
- `TFC_DEFAULT_VARIABLE_SET_ID`: A comma-separated list of variable set IDs to share with each newly-created workspace
    - Example `TFC_DEFAULT_VARIABLE_SET_ID=varset-foo,varset-bar`
- `TFC_OAUTH_TOKEN_ID`: See `--oauth-token-id`. Should look something like `ot-XU...`
