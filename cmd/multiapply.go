package cmd

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/chilledornaments/tfc/internal/tool"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

func filterSkipped(workspaces map[string]string, logger logrus.Logger) map[string]string {
	rv := make(map[string]string)

	for name, id := range workspaces {
		keep := true

		for _, value := range settings.MultiApplySettings.Skip {
			if strings.Contains(name, value) {
				logger.Debugf("skipping workspace '%s' because it contains string '%s'", name, value)
				keep = false
				break
			}
		}

		if keep {
			rv[name] = id
		}

	}

	return rv
}

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

	filteredWorkspaces := filterSkipped(workspaces, *m.Logger)
	m.Logger.Infof("found %d workspaces", len(filteredWorkspaces))

	for name, id := range filteredWorkspaces {
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

	if len(m.Queue) == 0 {
		m.Logger.Error("no runs to queue")
		os.Exit(0)
	}

	if !settings.MultiApplySettings.AutoApprove {
		fmt.Println("** workspaces to apply:")
		for _, item := range m.Queue {
			fmt.Printf("- %s\n", item.WorkspaceName)
		}

		// Seems redundant if the build is gated, but this gives the user a chance to bail out if they typoed or something
		tool.PromptForInput()
	} else {
		m.Logger.Warn("automatic approval flag set, not prompting for input. This may result in unexpected changes!")
	}

	wg := tool.NewWorkerGroup()

	workerCtx, workerCtxCancel := context.WithCancel(ctx)
	defer workerCtxCancel()

	// Hacky, but it works
	if settings.MultiApplySettings.Gated {
		wg.Add(1)

		go m.Work(workerCtx, settings.MultiApplySettings.Timeout, settings.MultiApplySettings.Gated, wg)
	} else {

		for i := 0; i < settings.MultiApplySettings.Workers; i++ {
			wg.Add(1)

			go m.Work(workerCtx, settings.MultiApplySettings.Timeout, settings.MultiApplySettings.Gated, wg)
		}
	}

	wg.Wait()

	m.Logger.Info("done")
}
