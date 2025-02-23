#!/bin/sh

if [ ! -d build ]
then
    git clone https://github.com/return42/searxng.git build
    git reset --hard 032aac7d87e64cd4cbdf641ee169badefb3ea4c4
else
    cd build
    git restore .
    git pull https://github.com/return42/searxng.git
    git reset --hard 032aac7d87e64cd4cbdf641ee169badefb3ea4c4
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
