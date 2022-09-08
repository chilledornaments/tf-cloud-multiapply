#!/usr/bin/env bash

mkdir -p artifacts

# Build AMD64
for os in windows darwin linux
do
 for arch in amd64 arm64
 do
    echo "Building ${os}-${arch} binary"
    GOARCH=$arch GOOS=$os go build -o tfc
    zip "${os}-${arch}.zip" tfc
    rm tfc
    mv "${os}-${arch}.zip" artifacts/
 done
done

