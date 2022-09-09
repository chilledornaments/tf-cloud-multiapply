package cmd

import (
	"os"
	"strings"

	"github.com/chilledornaments/tfc/internal/tool"
	"github.com/spf13/cobra"
)

var (
	organization string
	tfcTool      tool.Tool
	prefix       string
	settings     = CLISettings{}
)

type CLISettings struct {
	Prefix             string
	Debug              bool
	MultiApplySettings struct {
		Workers     int
		Force       bool
		AutoApprove bool
		Timeout     int
		Skip        []string
		Gated       bool
	}
	Create struct {
		Suffix               []string
		VariableSetSecretIDs []string
		VariableFilePrefix   string
		PathToVariableFiles  string
		Repo                 string
		VCSOAuthTokenID      string
	}
}

var tfcCLI = &cobra.Command{
	Use:   "tfc",
	Short: "A CLI for working with Terraform Cloud",
	// Args:  tfcCliArgs,
}

var multiApplyCmd = &cobra.Command{
	Use:   "apply",
	Short: "Apply plans across multiple Terraform Cloud workspaces",
	Run:   multiapplyEntrypoint,
}

var createWorkspaceCmd = &cobra.Command{
	Use:   "create",
	Short: "Create multiple Terraform Cloud workspaces",
	Run:   createWorkspaceEntrypoint,
}

// func tfcCliArgs(cmd *cobra.Command, args []string) error {
// 	if len(args) < 1 {
// 		return errors.New("argument required")
// 	}

// 	return nil
// }

func initTool() {
	token, err := tool.GetTerraformCloudToken()

	if err != nil {
		panic(err)
	}

	tfcTool = tool.NewTool(token, organization, settings.Debug)
}

func init() {
	multiApplyCmd.Flags().StringVarP(&settings.Prefix, "prefix", "p", "", "Prefix to apply against")
	multiApplyCmd.Flags().IntVarP(&settings.MultiApplySettings.Workers, "workers", "w", 5, "Number of concurrent applies to run")
	multiApplyCmd.Flags().BoolVarP(&settings.MultiApplySettings.AutoApprove, "auto-approve", "a", false, "Automatically apply plans")
	multiApplyCmd.Flags().BoolVar(&settings.MultiApplySettings.Force, "force", false, "Force run the latest plan")
	multiApplyCmd.Flags().IntVarP(&settings.MultiApplySettings.Timeout, "timeout", "t", 300, "Number of seconds to wait for an apply to apply. If you're running this tool against workspaces with many resources, you will likely need to set this to a large value")
	multiApplyCmd.Flags().StringArrayVar(&settings.MultiApplySettings.Skip, "skip", []string{}, "Any workspace containing this string will be skipped. Useful for excluding certain environments")
	multiApplyCmd.Flags().BoolVarP(&settings.MultiApplySettings.Gated, "gated", "g", false, "When set, runs are performed one at a time and you are prompted for approval before each run. This allows you to check the outcome of a run manually before proceeding")
	// Prevent passing both gated and auto-approve
	multiApplyCmd.MarkFlagsMutuallyExclusive("gated", "auto-approve")

	createWorkspaceCmd.Flags().StringVarP(&settings.Prefix, "prefix", "p", "", "Prefix to use when creating workspaces")
	createWorkspaceCmd.Flags().StringArrayVarP(&settings.Create.Suffix, "suffix", "s", []string{}, "Suffix to use when creating workspaces")
	createWorkspaceCmd.Flags().StringArrayVarP(
		&settings.Create.VariableSetSecretIDs,
		"variable-set-ids", "v",
		strings.Split(os.Getenv("TFC_DEFAULT_VARIABLE_SET_ID"), ","),
		"A set of variable set IDs to share with the workspace",
	)
	createWorkspaceCmd.Flags().StringVarP(&settings.Create.PathToVariableFiles, "path-to-var-files", "f", "./var", "Path to variable files")
	createWorkspaceCmd.Flags().StringVarP(&settings.Create.VariableFilePrefix, "var-file-prefix", "x", "", "Combined with suffix to build variable file name for a given workspace")
	createWorkspaceCmd.Flags().StringVarP(&settings.Create.Repo, "repo", "r", "", "Repository name to connect to workspace. Must be in the form of <Repo owner>/<repo name>")
	createWorkspaceCmd.Flags().StringVarP(&settings.Create.VCSOAuthTokenID, "vcs-token-id", "i", "", "ID of OAuth token that Terraform Cloud uses to connect to VCS. Can be found in Terraform Cloud version control settings")

	tfcCLI.PersistentFlags().StringVarP(&organization, "organization", "o", os.Getenv("TFC_ORG_NAME"), "Terraform Cloud organization name")
	tfcCLI.PersistentFlags().BoolVar(&settings.Debug, "debug", false, "Enable debug logging")
	tfcCLI.AddCommand(multiApplyCmd)
	tfcCLI.AddCommand(createWorkspaceCmd)
}

func Execute() {

	if err := tfcCLI.Execute(); err != nil {
		panic(err)
	}
}
