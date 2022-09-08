package tool

import (
	"github.com/hashicorp/go-tfe"
	"github.com/sirupsen/logrus"
)

type Tool struct {
	client       tfe.Client
	organization string
	Logger       *logrus.Logger
}

func NewTool(token string, organization string, debug bool) Tool {

	// TODO - is it worth building and using a custom client?
	c := &tfe.Config{Token: token, RetryServerErrors: true}

	client, err := tfe.NewClient(c)

	if err != nil {
		panic(err)
	}

	return Tool{client: *client, organization: organization, Logger: NewLogger(debug)}
}

func NewQueue() []MultiApplyQueueItem {
	return make([]MultiApplyQueueItem, 0)
}
