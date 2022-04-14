#!/bin/sh

echo "building theme from master branch searxng/searxng"

echo "clone/pull latest searxng/searxng"
if [ ! -d build ]
then
    git clone https://github.com/searxng/searxng.git build
else
    cd build
    git restore .
    git pull https://github.com/searxng/searxng.git
    cd ..
fi

echo "delete upstream simple theme definitions"
rm -f build/searx/static/themes/simple/src/less/definitions.less build/searx/static/themes/simple/src/less/search.less

echo "copy fork simple theme definitions in place"
cp -v src/less/definitions.less build/searx/static/themes/simple/src/less/definitions.less
cp -v src/less/search.less build/searx/static/themes/simple/src/less/search.less

echo "build themes with upstream scripts"
cd build
make themes.all
cd ..

echo "delete old searxng logo"
rm -f build/searx/static/themes/simple/img/searxng.png

echo "copy new searxng logo in place"
cp -v src/images/searxng.png build/searx/static/themes/simple/img/

echo "cp build files back to fork src folder"
rm -rf src/css/*
cp -r -v build/searx/static/themes/simple/css/* src/css/
