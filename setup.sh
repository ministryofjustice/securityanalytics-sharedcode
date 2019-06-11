#!/bin/sh

if [ $# -ne 2 ]
then
    echo "Syntax: setup.sh <app_name> <tf_workspace>"
    sleep 30
    exit
fi

export PIPENV_VENV_IN_PROJECT=true
pipenv install --dev --clear

# since the terraform step uses python code, it requires we run in an activated venv
pipenv run `pwd`/terraform.sh $1 $2

wait