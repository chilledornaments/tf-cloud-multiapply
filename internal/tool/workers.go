package tool

import (
	"context"
	"sync"
	"time"

	"github.com/sirupsen/logrus"
)

func NewWorkerGroup() *sync.WaitGroup {
	return &sync.WaitGroup{}
}

func (m *MultiApply) Work(ctx context.Context, timeout int, wg *sync.WaitGroup) {
	defer wg.Done()

	done := false

	for !done {
		work := m.nextInQueue()

		var applyErr error
		// TODO - double check this actually works as intended
		// This should move onto the next plan after <timeout> seconds have passed
		workerCtx, workerCtxCancelFunc := context.WithTimeout(ctx, time.Duration(timeout)*time.Second)
		defer workerCtxCancelFunc()

		if work == nil {
			done = true
		} else {
			m.Logger.WithFields(logrus.Fields{"workspace_name": work.WorkspaceName, "force": work.Force, "run_id": work.RunID}).Info("starting work")

			applyErr = m.apply(workerCtx, work.RunID)

			if applyErr != nil {
				m.Logger.WithFields(logrus.Fields{"workspace_name": work.WorkspaceName, "force": work.Force, "run_id": work.RunID, "err": applyErr}).Error("error queueing apply")
			}

			time.Sleep(5 * time.Second)

			var applyFinished bool

			applyFinished, applyErr = m.checkStatus(ctx, work.RunID)

			if applyErr != nil {
				m.Logger.WithFields(logrus.Fields{"run_id": work.RunID, "workspace_name": work.WorkspaceName}).Error("run failed to apply")
			}

			for !applyFinished {
				time.Sleep(5 * time.Second)
				applyFinished, applyErr = m.checkStatus(ctx, work.RunID)

				if applyErr != nil {
					m.Logger.WithFields(logrus.Fields{"run_id": work.RunID, "workspace_name": work.WorkspaceName}).Error("run failed to apply")
				}
			}

			m.Logger.WithFields(logrus.Fields{"run_id": work.RunID, "workspace_name": work.WorkspaceName}).Info("run finished")
		}

	}
}
