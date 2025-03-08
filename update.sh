#!/bin/sh

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
cp -v src/less/* build/client/simple/src/less/
cp -v src/js/* build/client/simple/src/js/main/

echo "Enable privacy page."
if ! grep -q '@import "privacypage.less";' build/client/simple/src/less/style.less; then
  sed -i 's/@import "definitions.less";/@import "definitions.less";\n@import "privacypage.less";/' build/client/simple/src/less/style.less
fi

echo "Build static files."
cd build
make themes.all
cd ..

echo "Copy build files into output folder."
rm -rf out/css/*
rm -rf out/js/*
cp -r -v build/searx/static/themes/simple/css/* out/css/
cp -r -v build/searx/static/themes/simple/js/* out/js/
