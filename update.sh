#!/bin/sh

if [ ! -d build ]
then
    git clone https://github.com/return42/searxng.git build
    git reset --hard 7d08c6968ebf0ab6c73f637bf63033ce3c9f60c0
else
    cd build
    git restore .
    git pull https://github.com/return42/searxng.git
    git reset --hard 7d08c6968ebf0ab6c73f637bf63033ce3c9f60c0
    cd ..
fi

echo "Replace fork simple theme definitions."
cp -v src/less/* build/client/simple/src/less/
cp -v src/js/* build/client/simple/src/js/main/

echo "Build static files."
cd build
make themes.all
cd ..

echo "Copy build files into output folder."
rm -rf out/css/*
rm -rf out/js/*
cp -r -v build/searx/static/themes/simple/css/* out/css/
cp -r -v build/searx/static/themes/simple/js/* out/js/
