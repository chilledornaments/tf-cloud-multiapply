package tool

import (
	"context"
	"fmt"

	"github.com/hashicorp/go-tfe"
	"github.com/sirupsen/logrus"
)

type WorkspaceCreator struct {
	Tool
}

type NewWorkspaceOptions struct {
	Name             string
	Repo             string
	OAuthTokenID     string
	VariableFilePath string
	VariableSetIds   []string
}

// Create creates a workspace, adds the TF_CLI_ARGS_plan env var to it, then returns the new workspace ID
func (w *WorkspaceCreator) Create(ctx context.Context, options *NewWorkspaceOptions) (*string, error) {
	r, err := w.client.Workspaces.Create(
		ctx, w.organization,
		tfe.WorkspaceCreateOptions{
			Type: "workspaces",
			Name: &options.Name,
			VCSRepo: &tfe.VCSRepoOptions{
				Identifier:   &options.Repo,
				OAuthTokenID: &options.OAuthTokenID,
			},
		},
	)

	if err != nil {
		w.Logger.WithFields(logrus.Fields{"err": err.Error(), "workspace": options.Name}).Error("error creating workspace")
		return nil, err
	}

	err = w.addVarFileArgument(ctx, r.ID, r.Name, options.VariableFilePath)

	return &r.ID, err
}

func (w WorkspaceCreator) addVarFileArgument(ctx context.Context, workspaceID string, workspaceName string, varFilePath string) error {
	_, err := w.client.Variables.Create(
		ctx,
		workspaceID,
		tfe.VariableCreateOptions{
			Key:      tfe.String("TF_CLI_ARGS_plan"),
			Value:    tfe.String(fmt.Sprintf("-var-file=%s", varFilePath)),
			Category: tfe.Category(tfe.CategoryEnv),
		},
	)

	if err != nil {
		w.Logger.WithFields(logrus.Fields{"err": err.Error(), "workspace": workspaceName}).Error("error adding TF_CLI_ARGS_plan to workspace")
	}

	return err
}

func (w WorkspaceCreator) ShareVariableSetWithWorkspaces(ctx context.Context, workspaces []*tfe.Workspace, variableSetID string) {
	err := w.client.VariableSets.ApplyToWorkspaces(
		ctx,
		variableSetID,
		&tfe.VariableSetApplyToWorkspacesOptions{
			Workspaces: workspaces,
		},
	)

	if err != nil {
		w.Logger.WithFields(logrus.Fields{"err": err.Error(), "variable_set_id": variableSetID}).Error("failed to add variable set to workspace")
	}

}
