package tool

import (
	"os"

	"github.com/sirupsen/logrus"
	log "github.com/sirupsen/logrus"
)

// TODO - don't use debug
func NewLogger(debug bool) *log.Logger {
	logger := log.New()
	logger.Out = os.Stdout
	logger.Level = logrus.InfoLevel

	if debug {
		logger.Level = logrus.DebugLevel
	}

	return logger
}
