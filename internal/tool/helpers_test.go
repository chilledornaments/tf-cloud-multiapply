package tool

import (
	"testing"
)

func Test_CleanFolderName(t *testing.T) {
	type args struct {
		name string
	}
	tests := []struct {
		name string
		args args
		want string
	}{
		{
			name: "Folder with trailing slash",
			args: args{name: "./test/"},
			want: "./test",
		},
		{
			name: "Folder with 2 trailing slashes",
			args: args{name: "./test//"},
			want: "./test",
		},
		{
			name: "Folder with no slashes",
			args: args{name: "test"},
			want: "test",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := CleanFolderName(tt.args.name); got != tt.want {
				t.Errorf("cleanFolderName() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestCleanVarFilePrefix(t *testing.T) {
	type args struct {
		path string
	}
	tests := []struct {
		name string
		args args
		want string
	}{
		{
			name: "trailing dash removed",
			args: args{path: "foo-"},
			want: "foo",
		},
		{
			name: "middle dash preserved with trailing",
			args: args{path: "hello-world-"},
			want: "hello-world",
		},
		{
			name: "middle dash preserved without trailing",
			args: args{path: "hello-world"},
			want: "hello-world",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := CleanVarFilePrefix(tt.args.path); got != tt.want {
				t.Errorf("CleanVarFilePrefix() = %v, want %v", got, tt.want)
			}
		})
	}
}
