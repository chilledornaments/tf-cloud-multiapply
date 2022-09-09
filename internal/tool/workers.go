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

func timeoutExpired(deadline time.Time) bool {
	return time.Until(deadline) <= 0
}

func (m *MultiApply) Work(ctx context.Context, timeout int, wg *sync.WaitGroup) {
	defer wg.Done()

	done := false

	for !done {
		work := m.nextInQueue()

		var applyErr error

		// TODO - I didn't want to spend any more time trying to abuse context timeouts, so I opted to take
		// a simpler path
		start := time.Now()
		deadlineTimeOut := start.Add(time.Duration(timeout) * time.Second)

		if work == nil {
			done = true
		} else {
			m.Logger.WithFields(logrus.Fields{"workspace_name": work.WorkspaceName, "force": work.Force, "run_id": work.RunID}).Info("starting work")

			applyErr = m.apply(ctx, work.RunID)

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
				if timeoutExpired(deadlineTimeOut) {
					m.Logger.WithFields(logrus.Fields{"workspace_name": work.WorkspaceName, "force": work.Force, "run_id": work.RunID}).Error("timed out waiting for apply")
					break
				}
				applyFinished, applyErr = m.checkStatus(ctx, work.RunID)

				if applyErr != nil {
					m.Logger.WithFields(logrus.Fields{"run_id": work.RunID, "workspace_name": work.WorkspaceName}).Error("run failed to apply")
				}
			}

			m.Logger.WithFields(logrus.Fields{"run_id": work.RunID, "workspace_name": work.WorkspaceName}).Info("run finished")
		}

	}
}
