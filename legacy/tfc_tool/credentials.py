import os
import json


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
    # Unknown error case
    except:
        raise
