from tfc_tool.workspaces import Workspace

w = Workspace(organization=None, tfc_session=None, logger=None)


def test_clean_folder_name_absolute_trailing():
    fn = "./var/"

    assert w.clean_folder_name(fn) == "./var"


def test_clean_folder_name_absolute_no_trailing():
    fn = "./var"

    assert w.clean_folder_name(fn) == "./var"
