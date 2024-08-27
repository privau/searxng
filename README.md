# SearXNG

Builds a [SearXNG](https://github.com/searxng/searxng) container, a privacy-respecting metasearch engine. Includes a suite of custom themes from catppuccin, paulgoio, kagi, brave, moa, and the default SearXNG themes.

Don't see your favorite theme? [Submit a theme request!](https://github.com/privau/searxng/issues/new?assignees=&labels=bug&projects=&template=theme-request.md)

Global Instance - 🌐 Worldwide : https://priv.au/

---

America, Vultr - 🇺🇸 Chicago, United States : https://na.priv.au/

America, DigitalOcean - 🇺🇸 San Francisco, United States : https://na2.priv.au/

Europe, Vultr - 🇩🇪 Frankfurt, Germany : https://eu.priv.au/

Europe, DigitalOcean - 🇬🇧 London, United Kingdom : https://eu2.priv.au/

Asia, Vultr - 🇸🇬 Singapore : https://as.priv.au/

Asia, DigitalOcean - 🇮🇳 Bangalore, India : https://as2.priv.au/

Australia, DigitalOcean - 🇦🇺 Sydney, Australia : https://au.priv.au/


## FAQ

### Where geographically is priv.au hosted?

When you connect to priv.au over IPv4, the location of your DNS resolver will determine which of our instances across the globe you will connect to, generally the closest will be chosen. Connecting over IPv6 will route you to the closest instance via BGP Anycast. You are able to bypass this selection process by connecting directly to a geographic instance, using the links above.

### Why does the Qwant engine not work?

If Qwant is returning an 'Access Denied' error, you're most likely connecting to our Singaporean instance. In December 2020, Qwant closed access for multiple countries, one being Singapore. You can read their statement on the matter [here](https://twitter.com/QwantCom/status/1339149434572206080). To bypass this block, you connect to a different instance in a different country.

## Basic Usage

* ```docker run -d --restart always -p 127.0.0.1:8080:8080 --name searxng vojkovic/searxng:production```

* Visit `http://127.0.0.1:8080` in your browser, stop the server with `Ctrl` + `C`.

## Theme Development

* Clone this repo: ```git clone https://github.com/privau/searxng.git```

* Make your changes to the theme within `src/less`

* Build the static files by running `update.sh`. This step requires python, npm and make. It's recommended to run this within the development container.

* You can build the docker container locally by running (check out the base branch for the alpine base with the needed python packages): ```docker build --pull -f ./Dockerfile -t searxng-dev:latest .```

* Run the local container with: ```docker run -it --rm -p 8080:8080 searxng-dev:latest```

* Alternatively, you can build the static files, build the docker image and run the docker container using `./development.sh`

## Environment Variables (all optional: if not set -> using default settings)

* ```IMAGE_PROXY``` : Enables the image proxy in SearXNG. (set this to `true`)

* ```REDIS_URL``` : Sets the URL of redis server to store data for Limiter plugin (for example `redis://redis:6379/0` or `unix:///usr/local/searxng-redis/run/redis.sock?db=0`)

* ```LIMITER``` : limit bot traffic; this option also requires redis to be set up

* ```BASE_URL``` : Sets the base url (for example: example.org would have `https://example.org/` as base)

* ```NAME``` : Sets the name of the instance, which is for example displayed in the title of the site (for example `SearXNG`)

* ```PRIVACYPOLICY``` : Sets the location of privacy policy of the instance. (for example `https://example.org/privacy-policy`)

* ```CONTACT``` : Sets the location for users to contact the instance maintainer. (for example `mailto:user@example.org`)

* ```ISSUE_URL``` : Set the location for users to report issues to. (for example `https://github.com/example/searxng/issues` !Without a trailing /)

* ```DONATION_URL``` : Sets the location for users to donate to. (for example `https://example.org/donate`). Leave empty to disable.

* ```GIT_URL``` : Sets the location of the Git repository. (for example `https://github.com/example/searxng`)

* ```GIT_BRANCH``` : Sets the Git branch of the repository specified in `GIT_URL`. (for example `main`)

* ```SEARCH_ENGINE_ACCESS_DENIED``` : Sets the suspension timeout in seconds if a search engine throws a SEARCH_ENGINE_ACCESS_DENIED exception, by default this value is set to ```86400``` (i.e. 1 day)

* ```PUBLIC_INSTANCE``` : Sets the public_instance parameter, which enables features designed for public instances. Requires the limiter to be enabled, which also requires redis. Required to be used on public production instances. Leave empty to disable.

* ```SECRET_KEY``` : Sets the secret key for the instance. If not set, a random key will be generated on startup.
