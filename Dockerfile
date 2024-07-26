# use prebuild alpine image with needed python packages from base branch
FROM vojkovic/searxng:base
ENV GID=991 UID=991 UWSGI_WORKERS=1 UWSGI_THREADS=16 IMAGE_PROXY=true REDIS_URL= LIMITER= BASE_URL= NAME=PrivAU SEARCH_DEFAULT_LANG= SEARCH_ENGINE_ACCESS_DENIED= PUBLIC_INSTANCE= \
PRIVACYPOLICY=privacy \
DONATION_URL= \
CONTACT=https://vojk.au \
ISSUE_URL=https://github.com/privau/searxng/issues GIT_URL=https://github.com/privau/searxng GIT_BRANCH=main \
UPSTREAM_COMMIT=319afe031e22fb644d336920802dcbafc8a5e338

WORKDIR /usr/local/searxng

# install build deps and git clone searxng as well as setting the version
RUN addgroup -g ${GID} searxng \
&& adduser -u ${UID} -D -h /usr/local/searxng -s /bin/sh -G searxng searxng \
&& git config --global --add safe.directory /usr/local/searxng \
&& git clone https://github.com/searxng/searxng . \
&& git reset --hard ${UPSTREAM_COMMIT} \
&& chown -R searxng:searxng . \
&& su searxng -c "/usr/bin/python3 -m searx.version freeze"

# copy custom simple themes, run.sh, limiter.toml, pages
COPY ./src/css/* searx/static/themes/simple/css/
COPY ./src/js/* searx/static/themes/simple/js/
COPY ./src/run.sh /usr/local/bin/run.sh
COPY ./src/limiter.toml /etc/searxng/limiter.toml

# make our patches to searxng's code to allow for the custom theming
RUN sed -i "/'simple_style': EnumStringSetting(/,/choices=\['', 'auto', 'light', 'dark'\]/s/choices=\['', 'auto', 'light', 'dark'\]/choices=\['', 'light', 'dark', 'paulgo', 'latte', 'frappe', 'macchiato', 'mocha'\]/" /usr/local/searxng/searx/preferences.py \
&& sed -i "s/SIMPLE_STYLE = ('auto', 'light', 'dark')/SIMPLE_STYLE = ('light', 'dark', 'paulgo', 'latte', 'frappe', 'macchiato', 'mocha')/" /usr/local/searxng/searx/settings_defaults.py \
&& sed -i "s/{%- for name in \['auto', 'light', 'dark'\] -%}/{%- for name in \['light', 'dark', 'paulgo', 'latte', 'frappe', 'macchiato', 'mocha'\] -%}/" /usr/local/searxng/searx/templates/simple/preferences/theme.html

# make patch to allow the privacy policy page
COPY ./src/pages/privacy searx/static/pages/privacy
RUN sed -i "/@app\.route('\/client<token>\.css', methods=\['GET', 'POST'\])/i \ \n@app.route('\/privacy', methods=\['GET'\])\ndef privacy_policy():return send_from_directory(os.path.join(app.root_path,settings['ui']['static_path'],'pages','privacy'),'index.html',mimetype='text\/html',)\n" /usr/local/searxng/searx/webapp.py

# include footer message
RUN sed -i "s|<footer>|<footer>\n        {{ _('Favicons in results are currently experimental. Open an issue on the ') }} <a href=\"{{ searx_git_url }}\">{{ _('GitHub') }}</a> if you run into any issues.|g" searx/templates/simple/base.html

# make run.sh executable, copy uwsgi server ini, set default settings, precompile static theme files
RUN cp -r -v dockerfiles/uwsgi.ini /etc/uwsgi/; \
chmod +x /usr/local/bin/run.sh; \
sed -i -e "/safe_search:/s/0/1/g" \
-e "/autocomplete:/s/\"\"/\"google\"/g" \
-e "/autocomplete_min:/s/4/0/g" \
-e "/port:/s/8888/8080/g" \
-e "/simple_style:/s/auto/macchiato/g" \
-e "/infinite_scroll:/s/false/true/g" \
-e "/query_in_title:/s/false/true/g" \
-e "s+donation_url: https://docs.searxng.org/donate.html+donation_url: false+g" \
-e "/bind_address:/s/127.0.0.1/0.0.0.0/g" \
-e '/default_lang:/s/ ""/ en/g' \
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
-e "/name: google/s/$/\n    disabled: false/g" \
-e "/name: wikipedia/s/$/\n    disabled: false/g" \
-e "/name: wikidata/s/$/\n    disabled: true/g" \
-e "/name: wikispecies/s/$/\n    disabled: true/g" \
-e "/name: wikinews/s/$/\n    disabled: true/g" \
-e "/name: wikibooks/s/$/\n    disabled: true/g" \
-e "/name: wikivoyage/s/$/\n    disabled: true/g" \
-e "/name: wikiversity/s/$/\n    disabled: true/g" \
-e "/name: wikiquote/s/$/\n    disabled: true/g" \
-e "/name: wikisource/s/$/\n    disabled: true/g" \
-e "/name: wikicommons.images/s/$/\n    disabled: true/g" \
-e "/name: duckduckgo/s/$/\n    disabled: true/g" \
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
-e "/name: brave/s/$/\n    disabled: true/g" \
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
-e "/shortcut: fd/{n;s/.*/    disabled: false/}" \
-e "/shortcut: bi/{n;s/.*/    disabled: true/}" \
searx/settings.yml; \
su searxng -c "/usr/bin/python3 -m compileall -q searx"; \
find /usr/local/searxng/searx/static -a \( -name '*.html' -o -name '*.css' -o -name '*.js' -o -name '*.svg' -o -name '*.ttf' -o -name '*.eot' \) \
-type f -exec gzip -9 -k {} \+ -exec brotli --best {} \+

# expose port and set tini as CMD; default user is searxng
USER searxng
EXPOSE 8080
CMD ["/sbin/tini","--","run.sh"]
