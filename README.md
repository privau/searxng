# SearXNG

A Fork of https://github.com/paulgoio/searxng

Builds custom SearXNG container with a changed simple theme, settings.yml and bundled with filtron binary; This project builds on top of https://github.com/searxng/searxng (SearXNG vs SearX: https://github.com/searxng/searxng/issues/46) as well as https://github.com/dalf/filtron.)

Production Server / Instance : https://search.vojkovic.xyz/

## FAQ

### Are you logging requests?

As off May 11th, I am no longer logging any requests.

### Why does Quant not work?

This SearXNG instance is hosted on a VPS in Singapore. In December 2020, Qwant closed access for multiple countries, one being Singapore. You can read their statement on the matter [here](https://twitter.com/QwantCom/status/1339149434572206080). Therefore, I have deactivated Qwant as a default search engine until Qwant allows Singaporean users to access their service.

### Basic Usage

* ```docker run -it --rm -p 8080:8080 vojkovic/searxng:production```

* After that just visit http://127.0.0.1:8080 in your browser and stop the server with ctrl-c.

### Development

* Clone this repo: ```git clone https://github.com/vojkovic/searxng.git```

* After making your changes in `src/less` make sure to update `src/css` by running `update.sh` (python, npm and make needed)

* You can build the docker container locally by running (check out base branch for the alpine base with the needed python packages): ```docker build --pull -f ./Dockerfile -t searxng-dev:latest .```

* Debug the local container with: ```docker run -it --rm -p 8080:8080 searxng-dev:latest```



### Environment Variables (all optional: if not set -> using default settings)

* ```IMAGE_PROXY``` : enable the image proxyfication through SearXNG; the builtin image proxy is used (set this to `true`)

* ```REDIS_URL``` : set the URL of redis server to store data for limiter plugin (for example `redis://redis:6379/0` or `unix:///usr/local/searxng-redis/run/redis.sock?db=0`)

* ```LIMITER``` : limit bot traffic; this option also requires redis to be set up

* ```BASE_URL``` : set the base url (for example example.org would have `https://example.org/` as base)

* ```NAME``` : set the name of the instance, which is for example displayed in the title of the site (for example `SearXNG`)

* ```CONTACT``` : set instance maintainer contact (for example `mailto:user@example.org`)

* ```ISSUE_URL``` : set issue url for custom SearXNG repo (for example `https://github.com/vojkovic/searxng/issues` !Without trailing /)

* ```GIT_URL``` : set git url for custom SearXNG repo (for example `https://github.com/vojkovic/searxng`)

* ```GIT_BRANCH``` : set git branch for custom SearXNG repo (for example `main`)

* ```PROXY1``` ```PROXY2``` ```PROXY3``` : set proxy server that are applied as round robin for all engines (for example `http://example.org:8080`)
