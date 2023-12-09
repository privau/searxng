#!/bin/sh

echo "Building theme from master branch searxng/searxng."

echo "Cloning latest searxng/searxng"
if [ ! -d build ]
then
    git clone https://github.com/searxng/searxng.git build
else
    cd build
    git restore .
    git pull https://github.com/searxng/searxng.git
    cd ..
fi

echo "Replace fork simple theme definitions."
cp -v src/less/* build/searx/static/themes/simple/src/less/

echo "Build themes with upstream scripts."
cd build
make themes.all
cd ..

echo "Copy build files back to fork src folder."
rm -rf src/css/*
cp -r -v build/searx/static/themes/simple/css/* src/css/
