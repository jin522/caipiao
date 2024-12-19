#!/bin/bash

which_python="/home/manager/.conda/envs/manager/bin/python"
current_dir=$(dirname "$(dirname "$0")")
cmd=$1
${which_python} $current_dir/lib/main.py $cmd 2>&1 &
