#!/bin/sh
set -e

UPSTREAM_COMMIT="$(grep -m1 "UPSTREAM_COMMIT=" Dockerfile | cut -d'=' -f2)"
UPSTREAM_REPO="$(sed -n 's/.*git clone.* \(https:[^ ]*\).*/\1/p' Dockerfile | head -n1)"

if [ ! -d build ]
then
    git clone "$UPSTREAM_REPO" build
fi

cd build
git fetch "$UPSTREAM_REPO" "$UPSTREAM_COMMIT"
git clean -fd
git reset --hard "$UPSTREAM_COMMIT"
cd ..

echo "Replace fork simple theme definitions."
cp -v src/less/*.less build/client/simple/src/less/
mkdir -p build/client/simple/src/less/themes && cp -v src/less/themes/* build/client/simple/src/less/themes/
mkdir -p build/client/simple/src/less/result_types && cp -v src/less/result_types/* build/client/simple/src/less/result_types/
cp -v src/js/autocomplete.ts build/client/simple/src/js/main/autocomplete.ts

echo "Enable privacy page."
if ! grep -q '@import "privacypage.less";' build/client/simple/src/less/style.less; then
  sed -i 's/@import "definitions.less";/@import "definitions.less";\n@import "privacypage.less";/' build/client/simple/src/less/style.less
fi

echo "Enable donation page styles."
if ! grep -q '@import "donationpage.less";' build/client/simple/src/less/style.less; then
  sed -i 's/@import "privacypage.less";/@import "privacypage.less";\n@import "donationpage.less";/' build/client/simple/src/less/style.less
fi

echo "Enable captcha page styles."
if ! grep -q '@import "captchapage.less";' build/client/simple/src/less/style.less; then
  sed -i 's/@import "donationpage.less";/@import "donationpage.less";\n@import "captchapage.less";/' build/client/simple/src/less/style.less
fi

echo "Build static files."
cd build
make themes.all
cd ..

echo "Copy build files into output folder."
rm -rf out/*
cp -r -v build/searx/static/themes/simple/* out/
