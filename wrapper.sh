#!/bin/bash

script_dir=$(dirname $0)

mkdir $script_dir/sessions
python $script_dir/secretsanta.py 
