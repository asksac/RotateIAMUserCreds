#!/bin/bash -xe

SRC_BASE='./src/lambdas/RotateIAMUserCreds'
DIST_BASE='./dist/lambdas/RotateIAMUserCreds'

# create dist package directory
mkdir -p "$DIST_BASE"

# copy source files 
cp "$SRC_BASE"/*.py "$DIST_BASE"

# install required packages 
pip install -r "$SRC_BASE/requirements.txt" -t "$DIST_BASE"
