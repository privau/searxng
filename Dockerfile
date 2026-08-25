# alpine as base
FROM docker.io/library/python:3.13-alpine AS builder

ENV UPSTREAM_COMMIT=438c21ee66101c1cbbf1ea4298dc6e0edeace2a7

# build deps
RUN apk add --no-cache \
     build-base \
     brotli \
     git \
     # lxml
     libxml2-dev \
     libxslt-dev \
     zlib-dev

WORKDIR /usr/local/searxng/

RUN git config --global --add safe.directory /usr/local/searxng \
&& git clone --branch cffi https://github.com/vojkovic/searxng . \
&& git reset --hard ${UPSTREAM_COMMIT}

# freeze version string
RUN python -m venv ./venv \
&& . ./venv/bin/activate \
&& pip install -r requirements.txt -r requirements-server.txt \
&& python -m searx.version freeze

ARG SEARXNG_UID=977
ARG SEARXNG_GID=977

RUN grep -m1 root /etc/group > /tmp/.searxng.group \
&& grep -m1 root /etc/passwd > /tmp/.searxng.passwd \
&& echo "searxng:x:$SEARXNG_GID:" >> /tmp/.searxng.group \
&& echo "searxng:x:$SEARXNG_UID:$SEARXNG_GID:searxng:/usr/local/searxng:/bin/sh" >> /tmp/.searxng.passwd

# copy modified simple themes
COPY ./out/ searx/static/themes/simple/

# precompile static files
RUN python -m compileall -q searx; \
    find searx/static \
    \( -name '*.html' -o -name '*.css' -o -name '*.js' -o -name '*.svg' -o -name '*.ttf' -o -name '*.eot' \) \
    -type f -exec gzip -9 -k {} + -exec brotli --best {} +

FROM docker.io/library/python:3.13-alpine

WORKDIR /usr/local/searxng/

RUN apk add --no-cache \
    libxslt

COPY --chown=root:root --from=builder /tmp/.searxng.passwd /etc/passwd
COPY --chown=root:root --from=builder /tmp/.searxng.group /etc/group
COPY --chown=searxng:searxng --from=builder /usr/local/searxng/venv ./venv
COPY --chown=searxng:searxng --from=builder /usr/local/searxng/searx ./searx

# copy run.sh
COPY --chown=searxng:searxng ./src/run.sh /usr/local/bin/run.sh

# block larger prefixes
RUN sed -i \
-e 's/^ipv4_prefix = 32/ipv4_prefix = 24/' \
-e 's/^ipv6_prefix = 48/ipv6_prefix = 40/' \
searx/limiter.toml

# enable all favicon resolvers
RUN sed -i \
-e 's/^# \[favicons.proxy.resolver_map\]/[favicons.proxy.resolver_map]/' \
-e 's/^# \(".*" = "searx\.favicons\.resolvers\..*"\)/\1/' \
-e 's/^# HOLD_TIME = .*/HOLD_TIME = 5184000/' \
-e 's/^# LIMIT_TOTAL_BYTES = .*/LIMIT_TOTAL_BYTES = 2147483648/' \
searx/favicons/favicons.toml

# make our patches to searxng's code to allow for the custom theming
RUN sed -i "/'simple_style': EnumStringSetting(/,/center_alignment/ s/choices=\[\"\", \"auto\", \"light\", \"dark\", \"black\"\]/choices=[\"\", \"auto\", \"light\", \"dark\", \"black\", \"paulgo\", \"latte\", \"frappe\", \"macchiato\", \"mocha\", \"kagi\", \"brave\", \"moa\", \"night\", \"dracula\", \"gruvbox\", \"gruvboxmat\", \"everforest\", \"nord\", \"matcha\", \"evergarden\"]/" searx/preferences.py \
&& sed -i "s/SIMPLE_STYLE = ('auto', 'light', 'dark', 'black')/SIMPLE_STYLE = ('auto', 'light', 'dark', 'black', 'paulgo', 'latte', 'frappe', 'macchiato', 'mocha', 'kagi', 'brave', 'moa', 'night', 'dracula', 'gruvbox', 'gruvboxmat', 'everforest', 'nord', 'matcha', 'evergarden')/" searx/settings_defaults.py \
&& sed -i "s/{%- for name in \['auto', 'light', 'dark', 'black'\] -%}/{%- for name in \['auto', 'light', 'dark', 'black', 'paulgo', 'latte', 'frappe', 'macchiato', 'mocha', 'kagi', 'brave', 'moa', 'night', 'dracula', 'gruvbox', 'gruvboxmat', 'everforest', 'nord', 'matcha', 'evergarden'\] -%}/" searx/templates/simple/preferences/theme.html

# privacy policy and donation page templates
COPY --chown=searxng:searxng ./src/privacy-policy/privacy-policy.html searx/templates/simple/privacy-policy.html
COPY --chown=searxng:searxng ./src/donation/donation.html searx/templates/simple/donation.html

# include patches for captcha
COPY --chown=searxng:searxng ./src/captcha/captcha.py searx/captcha.py
COPY --chown=searxng:searxng ./src/captcha/captcha.html searx/templates/simple/captcha.html
RUN sed -i '/search_obj = searx.search.SearchWithPlugins(search_query, sxng_request, sxng_request.user_plugins)/i\        from searx.captcha import handle_captcha\n        if (captcha_response := handle_captcha(sxng_request, settings["server"]["secret_key"], raw_text_query, search_query, selected_locale)):\n            return captcha_response\n' searx/webapp.py \
&& sed -i "/return Response('OK', mimetype='text\/plain')/a \\\\n@app.route('/captcha', methods=['GET', 'POST'], endpoint='captcha')\\ndef captcha_view():\\n    from searx.captcha import captcha as captcha_page\\n    return captcha_page(sxng_request, settings['server']['secret_key'])" searx/webapp.py

# supplemental engine early timeout (wikipedia, wikidata, ddg definitions)
COPY --chown=searxng:searxng ./src/search/supplemental_timeout.py searx/search/supplemental_timeout.py
COPY --chown=searxng:searxng ./src/search/google_autocomplete_icons.py searx/search/google_autocomplete_icons.py
COPY --chown=searxng:searxng ./src/search/privau_wsgi.py searx/privau_wsgi.py

# set default settings
RUN sed -i -e "/safe_search:/s/0/1/g" \
-e '/^[[:space:]]*autocomplete:/s/:[[:space:]]*.*/: "google"/' \
-e "/autocomplete_min:/s/4/0/g" \
-e '/^[[:space:]]*favicon_resolver:/s/:[[:space:]]*.*/: "kagi"/' \
-e "/port:/s/8888/8080/g" \
-e "/simple_style:/s/auto/macchiato/g" \
-e '/searx\.plugins\.infinite_scroll\.SXNGPlugin:/{n;s/active: false/active: true/;}' \
-e "/query_in_title:/s/false/true/g" \
-e '/^[[:space:]]*default_lang:/s/:[[:space:]]*.*/: "en"/' \
-e "/http_protocol_version:/s/1.0/1.1/g" \
-e "/X-Content-Type-Options: nosniff/d" \
-e "/X-Robots-Tag: noindex, nofollow/d" \
-e "/Referrer-Policy: no-referrer/d" \
-e "/^  map:/d" \
-e "/^  files:/d" \
-e "/^  social media:/d" \
-e "/name: wikispecies/s/$/\n    disabled: true/g" \
-e "/name: wikinews/s/$/\n    disabled: true/g" \
-e "/name: wikibooks/s/$/\n    disabled: true/g" \
-e "/name: wikivoyage/s/$/\n    disabled: true/g" \
-e "/name: wikiversity/s/$/\n    disabled: true/g" \
-e "/name: wikiquote/s/$/\n    disabled: true/g" \
-e "/name: wikisource/s/$/\n    disabled: true/g" \
-e "/name: wikicommons.images/s/$/\n    disabled: true/g" \
-e "/name: wikicommons.videos/s/$/\n    disabled: true/g" \
-e "/name: pinterest/s/$/\n    disabled: true/g" \
-e "/name: piped/s/$/\n    disabled: true/g" \
-e "/name: public domain image archive/s/$/\n    disabled: true/g" \
-e "/name: piped.music/s/$/\n    disabled: true/g" \
-e "/name: bandcamp/s/$/\n    disabled: true/g" \
-e "/name: radio browser/s/$/\n    disabled: true/g" \
-e "/name: mixcloud/s/$/\n    disabled: true/g" \
-e "/name: hoogle/s/$/\n    disabled: true/g" \
-e "/name: currency/s/$/\n    disabled: false/g" \
-e "/name: qwant/s/$/\n    disabled: true/g" \
-e "/name: btdigg/s/$/\n    disabled: true/g" \
-e "/name: lucide/s/$/\n    disabled: true/g" \
-e "/name: devicons/s/$/\n    disabled: true/g" \
-e "/name: pexels/s/$/\n    disabled: true/g" \
-e "/name: docker hub/s/$/\n    disabled: true/g" \
-e "/name: github/s/$/\n    disabled: true/g" \
-e "/name: semantic scholar/s/$/\n    disabled: true/g" \
-e "/name: openairedatasets/s/$/\n    disabled: true/g" \
-e "/name: sepiasearch/s/$/\n    disabled: true/g" \
-e "/name: dailymotion/s/$/\n    disabled: true/g" \
-e "/name: deviantart/s/$/\n    disabled: true/g" \
-e "/name: vimeo/s/$/\n    disabled: true/g" \
-e "/name: openairepublications/s/$/\n    disabled: true/g" \
-e "/name: library of congress/s/$/\n    disabled: true/g" \
-e "/name: dictzone/s/$/\n    disabled: true/g" \
-e "/name: baidu/s/$/\n    disabled: true/g" \
-e "/name: lingva/s/$/\n    disabled: true/g" \
-e "/name: genius/s/$/\n    disabled: true/g" \
-e "/name: wallhaven/s/$/\n    disabled: true/g" \
-e "/name: artic/s/$/\n    disabled: true/g" \
-e "/name: flickr/s/$/\n    disabled: true/g" \
-e "/name: unsplash/s/$/\n    disabled: true/g" \
-e "/name: gentoo/s/$/\n    disabled: true/g" \
-e "/name: openverse/s/$/\n    disabled: true/g" \
-e "/name: google videos/s/$/\n    disabled: true/g" \
-e "/name: yahoo news/s/$/\n    disabled: true/g" \
-e "/name: bing news/s/$/\n    disabled: true/g" \
-e "/name: tineye/s/$/\n    disabled: true/g" \
-e "/name: google/s/$/\n    disabled: true/g" \
-e "/name: google cse/s/$/\n    disabled: true/g" \
-e "/name: google cse images/s/$/\n    disabled: true/g" \
-e "/name: startpage/s/$/\n    disabled: true/g" \
-e "/name: brave/s/$/\n    disabled: true/g" \
-e "/name: duckduckgo\$/s/$/\n    disabled: true/g" \
-e "/name: wikipedia/s/$/\n    disabled: true/g" \
-e "/name: wikidata/s/$/\n    disabled: true/g" \
-e "/name: luxxle/s/$/\n    disabled: true/g" \
-e "/name: iseek/s/$/\n    disabled: true/g" \
-e "/name: yandex/s/$/\n    disabled: true/g" \
-e "/name: swisscows/s/$/\n    disabled: true/g" \
-e "/name: dogpile\$/s/$/\n    disabled: true/g" \
-e "/name: dogpile images\$/s/$/\n    disabled: true/g" \
-e "/name: privacywall/s/$/\n    disabled: true/g" \
-e "/name: vuhuv/s/$/\n    disabled: true/g" \
-e "/name: gmx/s/$/\n    disabled: true/g" \
-e "/name: duckduckgo web/s/$/\n    disabled: true/g" \
-e "/name: resulthunter/s/$/\n    disabled: true/g" \
-e "/name: tusksearch/s/$/\n    disabled: true/g" \
-e "/name: ddg definitions/s/$/\n    disabled: true/g" \
-e "/name: jina$/s/$/\n    jina_engine: google/g" \
searx/settings.yml;

EXPOSE 8080

# set env
ENV GRANIAN_PROCESS_NAME="searxng" GRANIAN_INTERFACE="wsgi" GRANIAN_HOST="::" GRANIAN_PORT="8080" GRANIAN_WEBSOCKETS="false" GRANIAN_BLOCKING_THREADS="4" GRANIAN_WORKERS_KILL_TIMEOUT="30" GRANIAN_BLOCKING_THREADS_IDLE_TIMEOUT="300" \
IMAGE_PROXY=true PROXY= VALKEY_URL= REDIS_URL= LIMITER= BASE_URL= SECRET_KEY= CAPTCHA= MARGINALIA_API= JINA_API= NAME= SEARCH_DEFAULT_LANG= SEARCH_ENGINE_ACCESS_DENIED= SEARCH_ENGINE_CAPTCHA= ENGINE_TIMEOUT= PUBLIC_INSTANCE= \
GOOGLE_DEFAULT=true BING_DEFAULT= BRAVE_DEFAULT= DUCKDUCKGO_DEFAULT= STARTPAGE_DEFAULT= WIKIPEDIA_DEFAULT= WIKIDATA_DEFAULT= DDG_DEFINITIONS_DEFAULT= \
LUXXLE_DEFAULT= ISEEK_DEFAULT= YANDEX_DEFAULT= SWISSCOWS_DEFAULT= DOGPILE_DEFAULT= PRIVACYWALL_DEFAULT= VUHUV_DEFAULT= GMX_DEFAULT= DUCKDUCKGO_WEB_DEFAULT= RESULTHUNTER_DEFAULT= TUSKSEARCH_DEFAULT= GOOGLE_CSE_DEFAULT= \
OPENMETRICS= \
PRIVACYPOLICY= \
DONATE= \
CONTACT=https://vojk.au \
FOOTER_MESSAGE= \
ISSUE_URL=https://github.com/privau/searxng/issues GIT_URL=https://github.com/privau/searxng GIT_BRANCH=main

USER searxng
CMD ["run.sh"]
