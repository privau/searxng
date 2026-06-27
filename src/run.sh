#!/bin/sh


# enable built in image proxy
if [ ! -z "${IMAGE_PROXY}" ]; then
    sed -i -e "/image_proxy:/s/false/true/g" \
    searx/settings.yml;
fi

# proxy config based on PROXY env var
if [ ! -z "${PROXY}" ]; then
    sed -i -e "s/  #  proxies:/  proxies:/g" \
    -e "s+  #    all://:+    all://:+g" \
    searx/settings.yml;
    echo "${PROXY}" | tr ',' '\n' | while read -r i; do
        sed -i -e "s+    all://:+    all://:\n      - ${i}+g" \
        searx/settings.yml;
    done
fi

# set redis if REDIS_URL contains URL
if [ ! -z "${REDIS_URL}" ]; then
    sed -i -e "s+  url: false+  url: ${REDIS_URL}+g" \
    searx/settings.yml;
fi

# enable limiter if LIMITER exists
if [ ! -z "${LIMITER}" ]; then
    sed -i -e "s+limiter: false+limiter: true+g" \
    searx/settings.yml;
fi

# set base_url and instance_name if BASE_URL is not empty
if [ ! -z "${BASE_URL}" ]; then
    sed -i -e "s+base_url: false+base_url: \"${BASE_URL}\"+g" \
    searx/settings.yml;
fi

# set instance name
if [ ! -z "${NAME}" ]; then
    sed -i -e "/instance_name:/s/SearXNG/${NAME}/g" \
    searx/settings.yml;
fi

# set privacy policy url
if [ ! -z "${PRIVACYPOLICY}" ]; then
    sed -i -e "s+privacypolicy_url: false+privacypolicy_url: ${PRIVACYPOLICY}+g" \
    searx/settings.yml;
fi

# set contact url
if [ ! -z "${CONTACT}" ]; then
    sed -i -e "s+contact_url: false+contact_url: ${CONTACT}+g" \
    searx/settings.yml;
fi

# set default search lang
if [ ! -z "${SEARCH_DEFAULT_LANG}" ]; then
    sed -i -e "s+default_lang: \"auto\"+default_lang: \"${SEARCH_DEFAULT_LANG}\"+g" \
    searx/settings.yml;
fi

# set issue url
if [ ! -z "${ISSUE_URL}" ]; then
    sed -i -e "s+issue_url: https://github.com/searxng/searxng/issues+issue_url: ${ISSUE_URL}+g" \
    -e "s+new_issue_url: https://github.com/searxng/searxng/issues/new+new_issue_url: ${ISSUE_URL}/new+g" \
    searx/settings.yml;
fi

# set git url
if [ ! -z "${GIT_URL}" ]; then
    sed -i -e "s+^GIT_URL = .*$+GIT_URL = \"${GIT_URL}\"+g" \
    searx/version_frozen.py; \
fi

# set git branch
if [ ! -z "${GIT_BRANCH}" ]; then
    sed -i -e "/GIT_BRANCH/s/\".*\"/\"${GIT_BRANCH}\"/g" \
    searx/version_frozen.py; \
fi

# set engine suspension timeout if a SearxEngineAccessDenied exception occours
if [ ! -z "${SEARCH_ENGINE_ACCESS_DENIED}" ]; then
    sed -i -e "/    SearxEngineAccessDenied/s/180/${SEARCH_ENGINE_ACCESS_DENIED}/g" \
    searx/settings.yml;
else # set to 60 seconds
    sed -i -e "/    SearxEngineAccessDenied/s/180/60/g" \
    searx/settings.yml;
fi

# set engine suspension timeout if a SearxEngineCaptcha exception occours
if [ ! -z "${SEARCH_ENGINE_CAPTCHA}" ]; then
    sed -i -e "/    SearxEngineCaptcha/s/3600/${SEARCH_ENGINE_CAPTCHA}/g" \
    searx/settings.yml;
else # set to 60 seconds
    sed -i -e "/    SearxEngineCaptcha/s/3600/60/g" \
    searx/settings.yml;
fi

# set engine request timeout (default: 2 seconds)
if [ -z "${ENGINE_TIMEOUT}" ]; then
    ENGINE_TIMEOUT=2
fi
sed -i -e "s/  request_timeout: .*/  request_timeout: ${ENGINE_TIMEOUT}/" \
-e "s/  #* *max_request_timeout: .*/  max_request_timeout: ${ENGINE_TIMEOUT}/" \
searx/settings.yml;

# enable public_instance mode
if [ ! -z "${PUBLIC_INSTANCE}" ]; then
    sed -i -e "/public_instance:/s/false/true/g" \
    searx/settings.yml;
fi

# auto gen random key for every unique container if SECRET_KEY not set
if [ -z "${SECRET_KEY}" ]; then
    sed -i -e "s/ultrasecretkey/$(head -c 24 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9')/g" \
    searx/settings.yml;
else # set SECRET_KEY
    sed -i -e "s/ultrasecretkey/${SECRET_KEY}/g" \
    searx/settings.yml;
fi

# set OPENMETRICS if exists
if [ ! -z "${OPENMETRICS}" ]; then
    sed -i -e "s+open_metrics: ''+open_metrics: ${OPENMETRICS}+g" \
    searx/settings.yml;
fi

# set BING_DEFAULT if exists
if [ ! -z "${BING_DEFAULT}" ]; then
    sed -i \
    -e "/shortcut: bi\$/{n;s/.*/    disabled: false/}" \
    -e "/shortcut: bii\$/{n;s/.*/    disabled: true/}" \
    -e "/shortcut: bin\$/{n;s/.*/    disabled: true/}" \
    -e "/shortcut: biv\$/{n;s/.*/    disabled: true/}" \
    searx/settings.yml;
else # set to disabled
    sed -i \
    -e "/shortcut: bi\$/{n;s/.*/    disabled: true/}" \
    -e "/shortcut: bii\$/{n;s/.*/    disabled: true/}" \
    -e "/shortcut: bin\$/{n;s/.*/    disabled: true/}" \
    -e "/shortcut: biv\$/{n;s/.*/    disabled: true/}" \
    searx/settings.yml;
fi

# toggle engines via *_DEFAULT env vars
set_engine_default() {
    engine_name="$1"
    env_value="$2"

    if [ ! -z "$env_value" ]; then
        disabled="false"
    else
        disabled="true"
    fi

    sed -i -e "/- name: ${engine_name}\$/,/^  - name: /s/disabled: .*/disabled: ${disabled}/" \
    -e "/- name: ${engine_name}\$/,/^  - name: /{/inactive:/d;}" \
    searx/settings.yml;
}

set_engine_default google "${GOOGLE_DEFAULT}"
set_engine_default startpage "${STARTPAGE_DEFAULT}"
set_engine_default brave "${BRAVE_DEFAULT}"
set_engine_default duckduckgo "${DUCKDUCKGO_DEFAULT}"
set_engine_default wikipedia "${WIKIPEDIA_DEFAULT}"
set_engine_default wikidata "${WIKIDATA_DEFAULT}"
set_engine_default "ddg definitions" "${DDG_DEFINITIONS_DEFAULT}"
set_engine_default luxxle "${LUXXLE_DEFAULT}"
set_engine_default iseek "${ISEEK_DEFAULT}"
set_engine_default swisscows "${SWISSCOWS_DEFAULT}"
set_engine_default presearch "${PRESEARCH_DEFAULT}"
set_engine_default yandex "${YANDEX_DEFAULT}"
set_engine_default dogpile "${DOGPILE_DEFAULT}"
set_engine_default privacywall "${PRIVACYWALL_DEFAULT}"
set_engine_default vuhuv "${VUHUV_DEFAULT}"
set_engine_default gmx "${GMX_DEFAULT}"
set_engine_default "duckduckgo web" "${DUCKDUCKGO_WEB_DEFAULT}"
set_engine_default resulthunter "${RESULTHUNTER_DEFAULT}"
set_engine_default tusksearch "${TUSKSEARCH_DEFAULT}"

# set Marginalia API key
if [ ! -z "${MARGINALIA_API}" ]; then
    sed -i -e "/- name: marginalia/,/inactive:/s/# api_key: .*/api_key: '${MARGINALIA_API}'/" \
    -e "/- name: marginalia/,/inactive:/s/inactive: true/inactive: false/" \
    searx/settings.yml;
fi

# set footer message
if [ ! -z "${FOOTER_MESSAGE}" ]; then
    sed -i "/<footer>/,/{{/ { /${FOOTER_MESSAGE}/! s|<p>[^{{]*|<p>${FOOTER_MESSAGE}| }" \
    searx/templates/simple/base.html
fi

# set donation url
if [ ! -z "${DONATE}" ]; then
    sed -i -e "s+donation_url: false+donation_url: ${DONATE}+g" searx/settings.yml;
fi

exec /usr/local/searxng/venv/bin/granian searx.privau_wsgi:app
