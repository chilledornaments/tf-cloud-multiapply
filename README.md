# tf-cloud-multiapply

## Installing

You must use Python 3.9 or later.

Run `python setup.py install`

To verify installation, run `tfc --help`


## Power User Instructions

Store the following env vars in a file that you `source` before using this tool:
- `TFC_DEFAULT_VARIABLE_SET_ID` (if creating workspaces)
    - This is a comma-separated list of variable set IDs to share with workspaces
- `TFC_OAUTH_TOKEN_ID` (if adding workspaces)
- `TFC_ORG_NAME` (if not Nutrien)
- `TFC_TOKEN` if you don't want to run `terraform login` or if you want to test against a specific account

### Adding Workspaces

Relevant flags:

- `--add-workspace`
- `--prefix` / `-p`: Prefix for workspace names
- `--suffix` / `-s`: Suffix for workspace names
- `--repo` / `-r`: Repository where Terraform code lives in the form of `<Organization>/<Repository name>`
- `--oauth-token-id` / `-o`: ID of the OAuth application used to connect to repo. Can be found under Settings > Providers
- `--plan-file-prefix` / `-pfp`: Prefix of plan file names. Defaults to `<suffix>.tfvars`. For example, `-pfp hello-world` would yield `hello-world-dev.tfvars`. Variable files must follow either naming scheme to be picked up correctly
- `--var-file-folder` / `-vff`: Path to variable files. Defaults to `./var`. Trailing `/` are removed
- `--variable-set-ids` / `-vids`: A list of variable set IDs to share with each new workspace


Additionally, there are the following environment variables:
- `TFC_DEFAULT_VARIABLE_SET_ID`: A comma-separated list of variable set IDs to share with each newly-created workspace
    - Example `TFC_DEFAULT_VARIABLE_SET_ID=varset-foo,varset-bar`
- `TFC_OAUTH_TOKEN_ID`: See `--oauth-token-id`. Should look something like `ot-XU...`


Workspace names are created by simply stuffing the prefix and suffix together, so `--prefix aws-foo-bar` `--suffix dev sit pre prd` will yield `aws-foo-bar-{dev,sit,pre,prd}`. If you need additional customization, you'll have to build a loop on top of the `tfc` commands. Something like `for i in "us-east-1 us-east-2"; do tfc --add-workspace --prefix aws-foo-bar-$i --suffix dev sit pre prd; done`.
