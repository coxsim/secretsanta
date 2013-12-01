#!/bin/bash -x

script_dir=$(dirname $0)

rsync -vaz $script_dir/* littleleathercompany.com:src/secretsanta/
