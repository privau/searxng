# SearXNG

A Fork of https://github.com/paulgoio/searxng

Builds a custom SearXNG container with a changed simple theme and settings.yml. This project builds on top of https://github.com/searxng/searxng (SearXNG vs SearX: https://github.com/searxng/searxng/issues/46)

Production Server / Instance : https://priv.au/

## FAQ

### Do you have a privacy policy?

Yes! You can find it [here](https://priv.au/privacy/).

### Why does Quant not work?

This SearXNG instance is hosted on a VPS in Singapore. In December 2020, Qwant closed access for multiple countries, one being Singapore. You can read their statement on the matter [here](https://nitter.net/QwantCom/status/1339149434572206080). Therefore, I have deactivated Qwant as a default search engine until Qwant allows Singaporean users to access their service.

### Basic Usage

* ```docker run -d --restart always -p 127.0.0.1:8080:8080 --name searxng vojkovic/searxng:production```

* After that, just visit http://127.0.0.1:8080 in your browser and stop the server with ctrl-c.

### Development

* Clone this repo: ```git clone https://github.com/vojkovic/searxng.git```

* After making your changes in `src/less` make sure to update `src/css` by running `update.sh` (python, npm and make needed).

* You can build the docker container locally by running (check out the base branch for the alpine base with the needed python packages): ```docker build --pull -f ./Dockerfile -t searxng-dev:latest .```

* Debug the local container with: ```docker run -it --rm -p 8080:8080 searxng-dev:latest```



### Environment Variables (all optional: if not set -> using default settings)

* ```IMAGE_PROXY``` : enable the image proxyfication through SearXNG; the builtin image proxy is used (set this to `true`)

* ```REDIS_URL``` : set the URL of redis server to store data for limiter plugin (for example `redis://redis:6379/0` or `unix:///usr/local/searxng-redis/run/redis.sock?db=0`)

* ```LIMITER``` : limit bot traffic; this option also requires redis to be set up

* ```BASE_URL``` : set the base url (for example example.org would have `https://example.org/` as base)

* ```NAME``` : set the name of the instance, which is for example displayed in the title of the site (for example `SearXNG`)

* ```PRIVACYPOLICY``` : set URL of privacy policy of the instance (for example `https://example.org/privacy-policy`)

* ```CONTACT``` : set instance maintainer contact (for example `mailto:user@example.org`)

* ```ISSUE_URL``` : set issue url for custom SearXNG repo (for example `https://github.com/vojkovic/searxng/issues` !Without trailing /)

* ```DONATION_URL``` : set URL of the donation link of the instance (for example `https://docs.searxng.org/donate.html`). Leave empty to disable.

* ```GIT_URL``` : set git url for custom SearXNG repo (for example `https://github.com/vojkovic/searxng`)

* ```GIT_BRANCH``` : set git branch for custom SearXNG repo (for example `main`)
