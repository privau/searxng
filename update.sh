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

echo "Copy javascript snippets"
cp -v src/js-snippets/* build/searx/static/themes/simple/src/js/main/

echo "Build static files."
cd build
make themes.all
cd ..

echo "Copy build files back to fork src folder."
rm -rf src/css/*
cp -r -v build/searx/static/themes/simple/css/* src/css/

cp -r -v build/searx/static/themes/simple/js/* src/js/
