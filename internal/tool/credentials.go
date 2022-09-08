package tool

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/user"
)

type TFConfigFile struct {
	Credentials struct {
		App struct {
			Token string `json:"token"`
		} `json:"app.terraform.io"`
	} `json:"credentials"`
}

func GetTerraformCloudToken() (string, error) {

	if os.Getenv("TFC_TOKEN") != "" {
		return os.Getenv("TFC_TOKEN"), nil
	}

	u, _ := user.Current()
	credentialsFile := fmt.Sprintf("%s/.terraform.d/credentials.tfrc.json", u.HomeDir)

	f, err := os.Open(credentialsFile)

	defer f.Close()

	// TODO - don't panic
	if err != nil {
		panic(err)
	}

	fileContents, err := io.ReadAll(f)

	// TODO - don't panic
	if err != nil {
		panic(err)
	}

	c := TFConfigFile{}

	err = json.Unmarshal(fileContents, &c)

	// TODO - don't panic
	if err != nil {
		panic(err)
	}

	return c.Credentials.App.Token, nil

}
