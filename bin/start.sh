#!/bin/bash

versions=("python" "python2" "python3")

for version in "${versions[@]}"
do
    if command -v "$version" &> /dev/null
    then
        python_path=$(which "$version")
        python_dir=$(dirname "$python_path")
        which_python=$python_dir/$version
    fi
done

current_dir=$(dirname "$(dirname "$0")")
cmd=$1
${which_python} $current_dir/lib/main.py $cmd 2>&1 &
