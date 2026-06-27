# SearXNG

Builds a modified [SearXNG](https://github.com/searxng/searxng) container, a privacy respecting metasearch engine. Includes a suite of custom themes and bleeding edge patches that either don't fit upstream or aren't ready yet.

🌐 Global : https://priv.au

---

🇺🇸 Kansas City, United States : https://na.priv.au

🇸🇬 Singapore, Singapore : https://as.priv.au

🇩🇪 Frankfurt, Germany : https://eu.priv.au

🇦🇺 Melbourne, Australia : https://au.priv.au

Use the [Looking Glass](https://lg.as44354.net/) to find the closest one to you.

---

## Basic Usage

* ```docker run -d --restart always -p 127.0.0.1:8080:8080 --name searxng ghcr.io/privau/searxng```

* Visit `http://127.0.0.1:8080` in your browser, stop the server with `Ctrl` + `C`.

## Theme Development

* Clone this repo: ```git clone https://github.com/privau/searxng.git```

* Make your changes to the theme within `src/less`

* Build the static files by running `update.sh`.

* You can build the docker container locally by running: ```docker build --pull -f ./Dockerfile -t searxng-dev:latest .```

* Run the local container with: ```docker run -it --rm -p 8080:8080 searxng-dev:latest```

* Alternatively, you can build the static files, build the docker image and run the docker container using `./development.sh`

## Environment Variables (all optional: if not set -> using default settings)

* ```IMAGE_PROXY``` : enables the image proxy. (set this to `true`)

* ```REDIS_URL``` : sets the URL of valkey/redis server (for example `redis://redis:6379/0` or `unix:///usr/local/searxng-redis/run/redis.sock?db=0`)

* ```LIMITER``` : limit bot traffic; this option also requires redis to be set up

* ```PROXY``` : list of comma seperated proxies selected round robin for all engines (for example http://127.0.0.1:8080,http://proxy.example.net)

* ```BASE_URL``` : sets the base url (for example: example.org would have `https://example.org/`)

* ```GRANIAN_HOST``` : sets the address that granian will bind to. (default: `[::]`)

* ```GRANIAN_PORT``` : sets the port that granian will bind to (default: `8080`)

* ```NAME``` : sets the name of the instance, displayed as the url title - worth changing this as users can't add two instances named the same in Firefox (e.g. `PrivAU`)

* ```PRIVACYPOLICY``` : sets the location of the privacy policy of the instance (for example `https://example.org/privacy-policy`)

* ```CONTACT``` : sets the location for users to contact the instance maintainer (for example `mailto:user@example.org`)

* ```ISSUE_URL``` : set the location for users to report issues to (for example `https://github.com/example/searxng/issues` !Without a trailing /)

* ```DONATE``` : sets the location of the donation page of the instance (Default: unset)

* ```GIT_URL``` : sets the location of the Git repository. (for example `https://github.com/privau/searxng`)

* ```GIT_BRANCH``` : sets the Git branch of the repository specified in `GIT_URL`. (for example `main`)

* ```SEARCH_ENGINE_ACCESS_DENIED``` : sets the suspension timeout in seconds if a search engine throws a SEARCH_ENGINE_ACCESS_DENIED exception (Default: `60`)

* ```SEARCH_ENGINE_CAPTCHA``` : sets the suspension timeout in seconds if a search engine throws a SEARCH_ENGINE_CAPTCHA exception (Default: `60`)

* ```PUBLIC_INSTANCE``` : enables features designed for public instances. Forces image_proxy and limiter set to enabled. Requires redis/valkey.

* ```SECRET_KEY``` : manually set the secret key for the instance. A random key will be generated on startup if not set.

* ```FOOTER_MESSAGE``` : sets the footer message of the instance (Default: empty)

* ```AUTHORIZED_API``` : set the password for the Authorized API (Default: empty)

* ```OPENMETRICS``` : set the password for the Openmetrics endpoint (Default: empty)

* ```GOOGLE_DEFAULT``` : enable the Google search engine by default (Default: `true`)

* ```BING_DEFAULT``` : enable the Bing search engine by default (Default: `false`)

* ```BRAVE_DEFAULT``` : enable the Brave search engine by default (Default: `false`)

* ```DUCKDUCKGO_DEFAULT``` : enable the DuckDuckGo search engine by default (Default: `false`)

* ```STARTPAGE_DEFAULT``` : enable the Startpage search engine by default (Default: `false`)

* ```WIKIPEDIA_DEFAULT``` : enable the Wikipedia engine by default (Default: `false`)

* ```WIKIDATA_DEFAULT``` : enable the Wikidata engine by default (Default: `false`)

* ```DDG_DEFINITIONS_DEFAULT``` : enable the DuckDuckGo Definitions engine by default (Default: `false`)

* ```LUXXLE_DEFAULT``` : enable the Luxxle search engine by default (Default: `false`)

* ```ISEEK_DEFAULT``` : enable the iSeek search engine by default (Default: `false`)

* ```PRESEARCH_DEFAULT``` : enable the Presearch search engine by default (Default: `false`)

* ```YANDEX_DEFAULT``` : enable the Yandex search engine by default (Default: `false`)

* ```SWISSCOWS_DEFAULT``` : enable the Swisscows search engine by default (Default: `false`)

* ```DOGPILE_DEFAULT``` : enable the Dogpile search engine by default (Default: `false`)

* ```PRIVACYWALL_DEFAULT``` : enable the PrivacyWall search engine by default (Default: `false`)

* ```VUHUV_DEFAULT``` : enable the Vuhuv search engine by default (Default: `false`)

* ```GMX_DEFAULT``` : enable the GMX search engine by default (Default: `false`)

* ```DUCKDUCKGO_WEB_DEFAULT``` : enable the DuckDuckGo Web search engine by default (Default: `false`)

* ```RESULTHUNTER_DEFAULT``` : enable the ResultHunter search engine by default (Default: `false`)

* ```TUSKSEARCH_DEFAULT``` : enable the Tusksearch search engine by default (Default: `false`)

* ```SEARCH_DEFAULT_LANG``` : sets the default search language (for example `en`, Default: `auto`)

* ```MARGINALIA_API``` : sets the API key for the Marginalia search engine and enables it (Default: disabled)
