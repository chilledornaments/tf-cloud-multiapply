package cmd

import (
	"context"
	"fmt"
	"os"

	"github.com/chilledornaments/tfc/internal/tool"
	"github.com/spf13/cobra"
)

func multiapplyEntrypoint(cmd *cobra.Command, args []string) {
	if settings.Prefix == "" {
		fmt.Println("ERROR - setting prefix to a blank string is not allowed so as to avoid costly mistakes")
		os.Exit(1)
	}

	initTool()

	m := tool.MultiApply{Tool: tfcTool, Queue: tool.NewQueue()}

	ctx := context.TODO()

	workspaces, err := m.Find(ctx, settings.Prefix)

	if err != nil {
		panic(err)
	}

	m.Logger.Infof("found %d workspaces", len(workspaces))

	for name, id := range workspaces {
		if settings.MultiApplySettings.Force {
			// Get latest plan
			runID, err := m.LatestRun(ctx, name, id)

			if err == nil {

				if m.RunIsAppliable(ctx, runID) {
					// Add to queue
					m.AddToQueue(
						&tool.MultiApplyQueueItem{
							Force:         settings.MultiApplySettings.Force,
							WorkspaceID:   id,
							WorkspaceName: name,
							RunID:         runID,
						},
					)
				}
			}
		} else {
			// Get current plan
			runID, err := m.CurrentRun(ctx, name, id)
			canApply := true
			// Check if plan is apply-able
			if err == nil {
				canApply = m.RunIsAppliable(ctx, runID)
			}

			if canApply {
				m.AddToQueue(
					&tool.MultiApplyQueueItem{
						Force:         settings.MultiApplySettings.Force,
						WorkspaceID:   id,
						WorkspaceName: name,
						RunID:         runID,
					},
				)
			}
		}
	}

	m.Logger.Info("len queue", len(m.Queue))

	if len(m.Queue) == 0 {
		m.Logger.Error("no runs to queue")
		os.Exit(0)
	}

	if !settings.MultiApplySettings.AutoApprove {
		fmt.Println("** workspaces to apply:")
		for _, item := range m.Queue {
			fmt.Printf("- %s", item.WorkspaceName)
		}

		tool.PromptForInput()
	} else {
		m.Logger.Warn("automatic approval flag set, not prompting for input. This may result in unexpected changes!")
	}

	wg := tool.NewWorkerGroup()

	for i := 0; i < settings.MultiApplySettings.Workers; i++ {
		wg.Add(1)

		go m.Work(ctx, settings.MultiApplySettings.Timeout, wg)
	}

	wg.Wait()

	m.Logger.Info("done")
}
