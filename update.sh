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
mkdir -p build/client/simple/src/less/themes && cp -v src/less/themes/* build/client/simple/src/less/themes/
mkdir -p build/client/simple/src/less/result_types && cp -v src/less/result_types/* build/client/simple/src/less/result_types/
mkdir -p build/client/simple/src/js/plugin
cp -v src/js/plugin/AiOverview.ts build/client/simple/src/js/plugin/
cp -v src/js/autocomplete.ts build/client/simple/src/js/main/autocomplete.ts
sed -i '/import "..\/plugin\/AiOverview.ts";/d' build/client/simple/src/js/main/results.ts
if ! grep -q 'plugin/AiOverview' build/client/simple/src/js/router.ts; then
  sed -i '/if (settings.plugins?.includes("calculator"))/,/^  }$/{
    /^  }$/a\
\
  if (settings.plugins?.includes("aiOverview")) {\
    load(() => import("./plugin/AiOverview.ts").then(({ default: Plugin }) => new Plugin()), {\
      on: "endpoint",\
      where: [Endpoints.results]\
    });\
  }
  }' build/client/simple/src/js/router.ts
fi

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

echo "Enable AI overview styles."
if ! grep -q '@import "aioverview.less";' build/client/simple/src/less/style.less; then
  sed -i 's/@import "captchapage.less";/@import "captchapage.less";\n@import "aioverview.less";/' build/client/simple/src/less/style.less
fi

echo "Build static files."
cd build
make themes.all
cd ..

echo "Copy build files into output folder."
rm -rf out/*
cp -r -v build/searx/static/themes/simple/* out/
