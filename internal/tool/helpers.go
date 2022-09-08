package tool

import (
	"fmt"
	"os"
	"strings"
)

func CleanFolderName(name string) string {
	return strings.TrimRight(name, "/")
}

func CleanVarFilePrefix(path string) string {
	return strings.TrimRight(path, "-")
}

func PromptForInput() {
	var ans string

	fmt.Print("\nProceed [y/N]: ")
	fmt.Scan(&ans)

	if ans != "y" {
		fmt.Println("only 'y' will proceed")
		os.Exit(0)
	}

}
