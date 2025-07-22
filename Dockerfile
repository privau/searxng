# use alpine as base for searx and set workdir as well as env vars
FROM docker.io/library/python:3.13-alpine AS builder

ENV UPSTREAM_COMMIT=5cbf42262189c2329fdd950b519b61dd83ae7977

# install build deps
RUN apk add --no-cache \
     build-base \
     brotli \
     git \
     # lxml
     libxml2-dev \
     libxslt-dev \
     zlib-dev

WORKDIR /usr/local/searxng/

# git clone searxng as well, install python deps and freeze version
RUN git config --global --add safe.directory /usr/local/searxng \
&& git clone https://github.com/searxng/searxng . \
&& git reset --hard ${UPSTREAM_COMMIT}

RUN python -m venv ./venv \
&& . ./venv/bin/activate \
&& pip install -r requirements.txt \
&& pip install "granian~=2.0" \
&& python -m searx.version freeze

ARG SEARXNG_UID=977
ARG SEARXNG_GID=977

RUN grep -m1 root /etc/group > /tmp/.searxng.group \
&& grep -m1 root /etc/passwd > /tmp/.searxng.passwd \
&& echo "searxng:x:$SEARXNG_GID:" >> /tmp/.searxng.group \
&& echo "searxng:x:$SEARXNG_UID:$SEARXNG_GID:searxng:/usr/local/searxng:/bin/sh" >> /tmp/.searxng.passwd

# copy custom simple themes
COPY ./out/css/* searx/static/themes/simple/css/
COPY ./out/js/* searx/static/themes/simple/js/

#precompile static theme files
RUN python -m compileall -q searx; \
    find searx/static \
    \( -name '*.html' -o -name '*.css' -o -name '*.js' -o -name '*.svg' -o -name '*.ttf' -o -name '*.eot' \) \
    -type f -exec gzip -9 -k {} + -exec brotli --best {} +

FROM docker.io/library/python:3.13-alpine

WORKDIR /usr/local/searxng/

RUN apk add --no-cache \
    # lxml (ARMv7)
    libxslt

COPY --chown=root:root --from=builder /tmp/.searxng.passwd /etc/passwd
COPY --chown=root:root --from=builder /tmp/.searxng.group /etc/group
COPY --chown=searxng:searxng --from=builder /usr/local/searxng /usr/local/searxng

# copy run.sh, limiter.toml and favicons.toml
COPY --chown=searxng:searxng ./src/run.sh /usr/local/bin/run.sh
COPY --chown=searxng:searxng ./src/limiter.toml /etc/searxng/limiter.toml
COPY --chown=searxng:searxng ./src/favicons.toml /etc/searxng/favicons.toml

# make our patches to searxng's code to allow for the custom theming
RUN sed -i "/'simple_style': EnumStringSetting(/,/choices=\['', 'auto', 'light', 'dark', 'black'\]/s/choices=\['', 'auto', 'light', 'dark', 'black'\]/choices=\['', 'auto', 'light', 'dark', 'black', 'paulgo', 'latte', 'frappe', 'macchiato', 'mocha', 'kagi', 'brave', 'moa', 'night', 'dracula'\]/" searx/preferences.py \
&& sed -i "s/SIMPLE_STYLE = ('auto', 'light', 'dark', 'black')/SIMPLE_STYLE = ('auto', 'light', 'dark', 'black', 'paulgo', 'latte', 'frappe', 'macchiato', 'mocha', 'kagi', 'brave', 'moa', 'night', 'dracula')/" searx/settings_defaults.py \
&& sed -i "s/{%- for name in \['auto', 'light', 'dark', 'black'\] -%}/{%- for name in \['auto', 'light', 'dark', 'black', 'paulgo', 'latte', 'frappe', 'macchiato', 'mocha', 'kagi', 'brave', 'moa', 'night', 'dracula'\] -%}/" searx/templates/simple/preferences/theme.html

# make patch to allow the privacy policy page
COPY --chown=searxng:searxng ./src/privacy-policy/privacy-policy.html searx/templates/simple/privacy-policy.html
RUN sed -i "/@app\.route('\/client<token>\.css', methods=\['GET', 'POST'\])/i \ \n@app.route('\/privacy', methods=\['GET'\])\ndef privacy_policy():return render('privacy-policy.html')\n" searx/webapp.py

# include patches for captcha
COPY --chown=searxng:searxng ./src/captcha/captcha.html searx/templates/simple/captcha.html
COPY --chown=searxng:searxng ./src/captcha/captcha.py searx/captcha.py
RUN sed -i '/search_obj = searx.search.SearchWithPlugins(search_query, sxng_request, sxng_request.user_plugins)/i\        from searx.captcha import handle_captcha\n        if (captcha_response := handle_captcha(sxng_request, settings["server"]["secret_key"], raw_text_query, search_query, selected_locale, render)):\n            return captcha_response\n' searx/webapp.py

# include patches for authorized api access
COPY --chown=searxng:searxng ./src/auth/auth.py searx/auth.py
RUN sed -i -e "/if output_format not in settings\\['search'\\]\\['formats'\\]:/a\\        from searx.auth import valid_api_key\\n        if (not valid_api_key(sxng_request)):" -e 's|flask.abort(403)|    flask.abort(403)|' searx/webapp.py \
&& sed -i "/return Response('', mimetype='text\/css')/a \\\\n@app.route('/<key>/search', methods=['GET', 'POST'])\\ndef search_key(key=None):\\n    from searx.auth import auth_search_key\\n    return auth_search_key(sxng_request, key)" searx/webapp.py \
&& sed -i "/3\. If the IP is not in either list, the request is not blocked\./a\\    from searx.auth import valid_api_key\\n    if (valid_api_key(sxng_request)):\\n        return None" searx/limiter.py

# fix opensearch autocompleter (force method of autocompleter to use GET reuqests)
RUN sed -i '/{% if autocomplete %}/,/{% endif %}/s|method="{{ opensearch_method }}"|method="GET"|g' searx/templates/simple/opensearch.xml

# set default settings
RUN sed -i -e "/safe_search:/s/0/1/g" \
-e "/autocomplete:/s/\"\"/\"google\"/g" \
-e "/autocomplete_min:/s/4/0/g" \
-e "/favicon_resolver:/s/\"\"/\"google\"/g" \
-e "/port:/s/8888/8080/g" \
-e "/simple_style:/s/auto/macchiato/g" \
-e "/infinite_scroll:/s/false/true/g" \
-e "/query_in_title:/s/false/true/g" \
-e "s+donation_url: https://docs.searxng.org/donate.html+donation_url: false+g" \
-e '/default_lang:/s/ ""/ en/g' \
-e "/method:/s/\"POST\"/\"GET\"/g" \
-e "/http_protocol_version:/s/1.0/1.1/g" \
-e "/X-Content-Type-Options: nosniff/d" \
-e "/X-XSS-Protection: 1; mode=block/d" \
-e "/X-Robots-Tag: noindex, nofollow/d" \
-e "/Referrer-Policy: no-referrer/d" \
-e "/news:/{n;s/.*//}" \
-e "/files:/d" \
-e "/social media:/d" \
-e "/static_use_hash:/s/false/true/g" \
-e "s/    use_mobile_ui: false/    use_mobile_ui: true/g" \
-e "/disabled: false/d" \
-e "/name: wikipedia/s/$/\n    disabled: true/g" \
-e "/name: wikidata/s/$/\n    disabled: true/g" \
-e "/name: wikispecies/s/$/\n    disabled: true/g" \
-e "/name: wikinews/s/$/\n    disabled: true/g" \
-e "/name: wikibooks/s/$/\n    disabled: true/g" \
-e "/name: wikivoyage/s/$/\n    disabled: true/g" \
-e "/name: wikiversity/s/$/\n    disabled: true/g" \
-e "/name: wikiquote/s/$/\n    disabled: true/g" \
-e "/name: wikisource/s/$/\n    disabled: true/g" \
-e "/name: wikicommons.images/s/$/\n    disabled: true/g" \
-e "/name: pinterest/s/$/\n    disabled: true/g" \
-e "/name: piped/s/$/\n    disabled: true/g" \
-e "/name: piped.music/s/$/\n    disabled: true/g" \
-e "/name: bandcamp/s/$/\n    disabled: true/g" \
-e "/name: radio browser/s/$/\n    disabled: true/g" \
-e "/name: mixcloud/s/$/\n    disabled: true/g" \
-e "/name: hoogle/s/$/\n    disabled: true/g" \
-e "/name: currency/s/$/\n    disabled: true/g" \
-e "/name: qwant/s/$/\n    disabled: true/g" \
-e "/name: btdigg/s/$/\n    disabled: true/g" \
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
-e "/engine: startpage/s/$/\n    disabled: true/g" \
-e "/engine: wikipedia/s/$/\n    timeout: 1.0/g" \
-e "/shortcut: fd/{n;s/.*/    disabled: false/}" \
-e "/searx.plugins.calculator.SXNGPlugin:/,/^[^[:space:]]/s/active: true/active: false/" \
searx/settings.yml;

EXPOSE 8080

# set env
ENV GRANIAN_PROCESS_NAME="searxng" GRANIAN_INTERFACE="wsgi" GRANIAN_HOST="::" GRANIAN_PORT="8080" GRANIAN_WEBSOCKETS="false" GRANIAN_LOOP="uvloop" GRANIAN_BLOCKING_THREADS="1" GRANIAN_WORKERS_KILL_TIMEOUT="30" GRANIAN_BLOCKING_THREADS_IDLE_TIMEOUT="300" \
IMAGE_PROXY=true PROXY= REDIS_URL= LIMITER= BASE_URL= CAPTCHA= AUTHORIZED_API= NAME= SEARCH_DEFAULT_LANG= SEARCH_ENGINE_ACCESS_DENIED= PUBLIC_INSTANCE= \
GOOGLE_DEFAULT=true BING_DEFAULT= BRAVE_DEFAULT= DUCKDUCKGO_DEFAULT= \
OPENMETRICS= \
PRIVACYPOLICY= \
DONATION_URL= \
CONTACT=https://vojk.au \
FOOTER_MESSAGE= \
ISSUE_URL=https://github.com/privau/searxng/issues GIT_URL=https://github.com/privau/searxng GIT_BRANCH=main

CMD ["run.sh"]
