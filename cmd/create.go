package cmd

import (
	"context"
	"fmt"
	"os"

	"github.com/chilledornaments/tfc/internal/tool"
	"github.com/hashicorp/go-tfe"
	"github.com/spf13/cobra"
)

func createWorkspaceEntrypoint(cmd *cobra.Command, args []string) {
	initTool()

	ctx := context.TODO()

	w := tool.WorkspaceCreator{Tool: tfcTool}

	var varFileName string

	var newWorkspaceIDs []string

	for _, s := range settings.Create.Suffix {
		newWorkspaceName := fmt.Sprintf("%s-%s", settings.Prefix, s)
		// User hasn't supplied a var file prefix override
		if settings.Create.VariableFilePrefix == "" {
			varFileName = fmt.Sprintf("%s.tfvars", s)
		} else {
			varFileName = fmt.Sprintf("%s-%s.tfvars", tool.CleanVarFilePrefix(settings.Prefix), s)
		}

		w.Logger.WithField("workspace_name", newWorkspaceName).Info("creating workspace")

		workspaceID, err := w.Create(
			ctx,
			&tool.NewWorkspaceOptions{
				Name:               newWorkspaceName,
				Repo:               settings.Create.Repo,
				OAuthTokenID:       settings.Create.VCSOAuthTokenID,
				VariableFilePath:   fmt.Sprintf("%s/%s", tool.CleanFolderName(settings.Create.PathToVariableFiles), varFileName),
				VariableSetIds:     settings.Create.VariableSetSecretIDs,
				SkipPlanArgsEnvVar: settings.Create.SkipPlanArgsEnvVar,
				WorkingDir:         settings.Create.WorkingDir,
			},
		)

		if err != nil {
			panic(err)
			os.Exit(1)
		} else {
			newWorkspaceIDs = append(newWorkspaceIDs, *workspaceID)
		}
	}

	var tfeWorkspaces []*tfe.Workspace

	for _, ws := range newWorkspaceIDs {
		tfeWorkspaces = append(tfeWorkspaces, &tfe.Workspace{ID: ws})
	}

	// Do a little cleanup
	// If you strings.Split() an unset env var, Go doesn't create an empty list
	// It creates a list with a single empty string
	if settings.Create.VariableSetSecretIDs[0] == "" {
		settings.Create.VariableSetSecretIDs = settings.Create.VariableSetSecretIDs[1:]
	}

	for _, vs := range settings.Create.VariableSetSecretIDs {
		w.ShareVariableSetWithWorkspaces(ctx, tfeWorkspaces, vs)
	}

	w.Logger.Info("finished creating workspaces")
}
