# SearXNG

Builds a [SearXNG](https://github.com/searxng/searxng) container, a privacy-respecting metasearch engine. Includes a suite of custom themes from catppuccin, paulgoio, kagi, brave, moa, and the default SearXNG themes.

Don't see your favorite theme? [Submit a theme request!](https://github.com/privau/searxng/issues/new?assignees=&labels=bug&projects=&template=theme-request.md)

Global Instance - 🌐 Worldwide : https://priv.au [![Better Stack Badge](https://uptime.betterstack.com/status-badges/v3/monitor/1lrch.svg)](https://uptime.betterstack.com/?utm_source=status_badge)

---

America, Ausra - 🇺🇸 Kansas City, United States : https://na.priv.au [![Better Stack Badge](https://uptime.betterstack.com/status-badges/v3/monitor/1sv3j.svg)](https://uptime.betterstack.com/?utm_source=status_badge)

Asia, Vultr - 🇸🇬 Singapore, Singapore : https://as.priv.au [![Better Stack Badge](https://uptime.betterstack.com/status-badges/v3/monitor/1sv3i.svg)](https://uptime.betterstack.com/?utm_source=status_badge)

Europe, iFog - 🇩🇪 Frankfurt, Germany : https://eu.priv.au [![Better Stack Badge](https://uptime.betterstack.com/status-badges/v3/monitor/1sv3o.svg)](https://uptime.betterstack.com/?utm_source=status_badge)

Australia, Vultr - 🇦🇺 Melbourne, Australia : https://au.priv.au [![Better Stack Badge](https://uptime.betterstack.com/status-badges/v3/monitor/1sv3e.svg)](https://uptime.betterstack.com/?utm_source=status_badge)

## FAQ

### Where geographically is priv.au hosted?

When you connect to priv.au you are routed to the closest instance via BGP Anycast. You are able to bypass this selection process by connecting directly to a geographic instance, using the links above.

## Basic Usage

* ```docker run -d --restart always -p 127.0.0.1:8080:8080 --name searxng ghcr.io/privau/searxng```

* Visit `http://127.0.0.1:8080` in your browser, stop the server with `Ctrl` + `C`.

## Theme Development

* Clone this repo: ```git clone https://github.com/privau/searxng.git```

* Make your changes to the theme within `src/less`

* Build the static files by running `update.sh`. This step requires python, npm and make. It's recommended to run this within the development container.

* You can build the docker container locally by running: ```docker build --pull -f ./Dockerfile -t searxng-dev:latest .```

* Run the local container with: ```docker run -it --rm -p 8080:8080 searxng-dev:latest```

* Alternatively, you can build the static files, build the docker image and run the docker container using `./development.sh`

## Environment Variables (all optional: if not set -> using default settings)

* ```IMAGE_PROXY``` : Enables the image proxy in SearXNG. (set this to `true`)

* ```REDIS_URL``` : Sets the URL of redis server to store data for Limiter plugin (for example `redis://redis:6379/0` or `unix:///usr/local/searxng-redis/run/redis.sock?db=0`)

* ```LIMITER``` : limit bot traffic; this option also requires redis to be set up

* ```PROXY``` : list of comma-seperated servers that are applied as round robin for all engines (for example http://127.0.0.1:8080,http://proxy.example.net)

* ```BASE_URL``` : Sets the base url (for example: example.org would have `https://example.org/` as base)

* ```GRANIAN_HOST``` : Sets the address that granian will bind to. (default: `[::]`)

* ```GRANIAN_PORT``` : Sets the port that granian will bind to. (default: `8080`)

* ```NAME``` : Sets the name of the instance, which is for example displayed in the title of the site (for example `SearXNG`)

* ```PRIVACYPOLICY``` : Sets the location of privacy policy of the instance. (for example `https://example.org/privacy-policy`)

* ```CONTACT``` : Sets the location for users to contact the instance maintainer. (for example `mailto:user@example.org`)

* ```ISSUE_URL``` : Set the location for users to report issues to. (for example `https://github.com/example/searxng/issues` !Without a trailing /)

* ```DONATION_URL``` : Sets the location for users to donate to. (for example `https://example.org/donate`). Leave empty to disable.

* ```GIT_URL``` : Sets the location of the Git repository. (for example `https://github.com/example/searxng`)

* ```GIT_BRANCH``` : Sets the Git branch of the repository specified in `GIT_URL`. (for example `main`)

* ```SEARCH_ENGINE_ACCESS_DENIED``` : Sets the suspension timeout in seconds if a search engine throws a SEARCH_ENGINE_ACCESS_DENIED exception, by default this value is set to ```60``` (i.e. 1 minute)

* ```PUBLIC_INSTANCE``` : Sets the public_instance parameter, which enables features designed for public instances. Requires the limiter to be enabled, which also requires redis. Required to be used on public production instances. Leave empty to disable. (Default: `false`)

* ```SECRET_KEY``` : Sets the secret key for the instance. If not set, a random key will be generated on startup.

* ```FOOTER_MESSAGE``` : Sets the footer message of the instance. (Default: empty)

* ```CAPTCHA``` : Enables the captcha for the instance if set. (Default: `false`)

* ```AUTHORIZED_API``` : Set the password for the Authorized API. (Default: empty)

* ```OPENMETRICS``` : Set the password for the OpenMetrics endpoint. (Default: empty)

* ```GOOGLE_DEFAULT``` : Enable the Google search engine by default. (Default: `true`)

* ```BING_DEFAULT``` : Enable the Bing search engine by default. (Default: `false`)

* ```BRAVE_DEFAULT``` : Enable the Brave search engine by default. (Default: `false`)

* ```DUCKDUCKGO_DEFAULT``` : Enable the DuckDuckGo search engine by default. (Default: `false`)
