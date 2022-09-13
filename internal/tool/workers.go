package tool

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/sirupsen/logrus"
)

func NewWorkerGroup() *sync.WaitGroup {
	return &sync.WaitGroup{}
}

func timeoutExpired(deadline time.Time) bool {
	return time.Until(deadline) <= 0
}

func (m *MultiApply) applyAndWait(ctx context.Context, timeout int, runID string, workspaceName string, force bool) {
	var applyErr error

	// Create a new function-scoped logger that has all of our relevant fields
	logger := m.Logger.WithFields(logrus.Fields{"workspace_name": workspaceName, "force": force, "run_id": runID})

	// TODO - I didn't want to spend any more time trying to abuse context timeouts, so I opted to take
	// a simpler path
	start := time.Now()
	deadlineTimeOut := start.Add(time.Duration(timeout) * time.Second)
	applyErr = m.apply(ctx, runID)

	if applyErr != nil {
		logger.WithFields(logrus.Fields{"err": applyErr}).Error("error queueing apply")
	}

	time.Sleep(5 * time.Second)

	var applyFinished bool

	applyFinished, applyErr = m.checkStatus(ctx, runID)

	if applyErr != nil {
		logger.WithField("err", applyErr.Error()).Error("run failed to apply")
	}

	for !applyFinished {
		time.Sleep(5 * time.Second)
		if timeoutExpired(deadlineTimeOut) {
			logger.Error("timed out waiting for apply")
			break
		}
		applyFinished, applyErr = m.checkStatus(ctx, runID)

		if applyErr != nil {
			logger.WithField("err", applyErr.Error()).Error("run failed to apply")
		}
	}

	logger.Info("run finished")
}

func (m *MultiApply) Work(ctx context.Context, timeout int, gated bool, wg *sync.WaitGroup) {
	defer wg.Done()

	done := false

	for !done {
		work := m.nextInQueue()

		if work == nil {
			done = true
		} else {
			if gated {
				fmt.Printf("\n** gated apply requires approval for workspace: \n '%s'", work.WorkspaceName)
				PromptForInput()
			}

			logger := m.Logger.WithFields(logrus.Fields{"workspace_name": work.WorkspaceName, "force": work.Force, "run_id": work.RunID})

			logger.Info("starting apply")

			m.applyAndWait(ctx, timeout, work.RunID, work.WorkspaceName, work.Force)
		}

	}
}
