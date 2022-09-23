package tool

import (
	"context"
	"errors"
	"strings"
	"sync"

	"github.com/hashicorp/go-tfe"
	"github.com/sirupsen/logrus"
)

type MultiApply struct {
	// Extend Tool struct
	Tool
	lock  sync.RWMutex
	Queue []MultiApplyQueueItem
}

type MultiApplyQueueItem struct {
	RunID         string // run ID
	WorkspaceName string
	WorkspaceID   string
	Force         bool
}

func finalSuccessStates() []string {
	return []string{
		string(tfe.ApplyFinished),
		string(tfe.RunApplied),
	}
}

func finalErrorStates() []string {
	return []string{
		string(tfe.ApplyErrored),
		string(tfe.PlanErrored),
		string(tfe.RunErrored),
		string(tfe.RunCanceled),
		string(tfe.ApplyCanceled),
	}
}

func (m *MultiApply) AddToQueue(item *MultiApplyQueueItem) {
	m.lock.Lock()
	defer m.lock.Unlock()

	m.Logger.Debugf("adding item to queue %+v", item)

	m.Queue = append(m.Queue, *item)
}

func (m *MultiApply) nextInQueue() *MultiApplyQueueItem {
	m.lock.Lock()
	defer m.lock.Unlock()

	if len(m.Queue) > 0 {
		rv := m.Queue[0]
		m.Queue = m.Queue[1:]
		return &rv
	} else {
		m.Logger.Warning("queue is empty")
	}

	return nil
}

// Find returns all workspaces matching the specified prefix
func (m *MultiApply) Find(ctx context.Context, prefix string) (map[string]string, error) {
	m.Logger.Info("finding workspaces with prefix ", prefix)

	o := &tfe.WorkspaceListOptions{
		Search: prefix,
	}

	r := make(map[string]string)

	ws, err := m.Tool.client.Workspaces.List(ctx, m.Tool.organization, o)

	// TODO - handle err
	if err != nil {
		panic(err)
	}

	//paginate := false
	currentPage := ws.Pagination.CurrentPage
	nextPage := ws.Pagination.NextPage

	for _, w := range ws.Items {
		if strings.HasPrefix(w.Name, prefix) {
			r[w.Name] = w.ID
		}
	}

	for currentPage <= nextPage {
		o := &tfe.WorkspaceListOptions{
			Search:      prefix,
			ListOptions: tfe.ListOptions{PageNumber: nextPage},
		}
		ws, err := m.Tool.client.Workspaces.List(ctx, m.Tool.organization, o)

		if err != nil {
			panic(err)
		}

		currentPage = ws.CurrentPage
		nextPage = ws.NextPage

		for _, w := range ws.Items {
			if strings.HasPrefix(w.Name, prefix) {
				r[w.Name] = w.ID
			}
		}
	}

	return r, nil
}

// LatestRun retrieves the newest run for a workspace
func (m *MultiApply) LatestRun(ctx context.Context, name string, id string) (string, error) {
	v, err := m.client.Runs.List(
		ctx,
		id,
		&tfe.RunListOptions{},
	)

	if err != nil {
		m.Logger.WithFields(logrus.Fields{"workspace_name": name, "err": err.Error()}).Error("error getting latest run")
		return "", err
	}

	return v.Items[0].ID, nil
}

// CurrentRun retrieves the currently-planned run for a workspace
func (m *MultiApply) CurrentRun(ctx context.Context, name string, id string) (string, error) {
	v, err := m.client.Workspaces.ReadByID(ctx, id)

	if err != nil {
		m.Logger.WithFields(logrus.Fields{"workspace_name": name, "err": err.Error()}).Error("error getting latest run")
		return "", err
	}

	return v.CurrentRun.ID, nil

}

func (m *MultiApply) RunIsAppliable(ctx context.Context, id string) bool {
	v, err := m.client.Runs.Read(ctx, id)

	if err != nil {
		m.Logger.WithFields(logrus.Fields{"run_id": id, "err": err.Error()}).Error()
	}

	return v.Status == "pending" || v.Status == "planned"

}

func (m *MultiApply) ForceExecute(ctx context.Context, id string, workspaceName string) {}

// checkStatus checks the status of a run
// If the run is in a final state, the bool return value will be true and a nil error
// If the run errored, this will return true and a non-nil error
func (m *MultiApply) checkStatus(ctx context.Context, id string) (bool, error) {
	r, err := m.Tool.client.Runs.Read(ctx, id)

	if err != nil {
		m.Logger.WithField("err", err.Error()).Errorln("error checking run status")
		return true, err
	}

	m.Logger.WithFields(logrus.Fields{"run_id": id, "status": r.Status}).Debug("run not finished")

	for _, status := range finalSuccessStates() {
		if status == string(r.Status) {
			return true, nil
		}
	}

	for _, status := range finalErrorStates() {
		if status == string(r.Status) {
			return true, errors.New(status)
		}
	}

	return false, nil
}

// apply queues an apply for a run
func (m *MultiApply) apply(ctx context.Context, id string) error {
	// TODO, use a context that cancels after some amount of time
	return m.client.Runs.Apply(ctx, id, tfe.RunApplyOptions{})

}
