#!/bin/bash

# Environment handling
Tagvar="latest-cicd"

if [ "$CI_ENVIRONMENT_NAME" == "production" ]; then
    echo "Deploying to Production Environment"
    echo "----- Publish -----"
    
    if [ -n "$CI_COMMIT_TAG" ]; then
        Tagvar="$CI_COMMIT_TAG"
    else
        echo "Invalid tag"
        exit 1
    fi
fi


export TAG=$Tagvar
echo "export TAG=$Tagvar"
sleep 1
echo
echo "------------"
echo "start build project with TAG=$Tagvar"
echo "------------"
echo
sleep 2
docker compose build
push() {
    if ! docker compose push; then
        echo "failed"
        sleep 1
        push
    fi
    return
}
push
echo "push is done"
