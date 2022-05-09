# SearXNG

A Fork of https://github.com/paulgoio/searxng

Builds custom SearXNG container with a changed simple theme, settings.yml and bundled with filtron binary; This project builds on top of https://github.com/searxng/searxng (SearXNG vs SearX: https://github.com/searxng/searxng/issues/46) as well as https://github.com/dalf/filtron.)

Production Server / Instance : https://search.vojkovic.xyz/
Note: the production instance is extremely bleeding edge with updates from upstream being pushed in ~10m. During this update, the instance restarts, which causes a ~20s downtime. If this has happened to you, please try trying in half a minute. Thank you!

## FAQ

### Are you logging requests?

Short answer: Yes

Long answer: This instance doesn't log anything from Filtron or with SearXNG. However, I am currently using Caddy as a reverse proxy and I am collecting a modified access log from that. Before these logs are encoded, I remove a lot of the personal information according to this filter:


```
format filter {
  wrap json
  fields {
    request>remote_port delete
    request>remote_ip delete
    request>headers delete
    request>tls delete
    request>host delete
    size delete
    resp_headers delete
    user_id delete
    request>uri regexp .(search|image_proxy|autocompleter|static|opensearch|preferences|.*).* ${1}
    }
}
```

Put simply, I only know that a search request has come but not what was searched for or who searched for it.

This is a typical log from a search request.

```

{"level":"info","ts":1651945036.4679813,"logger":"http.log.access.log1","msg":"handled request","request":{"proto":"HTTP/3","method":"POST","uri":"search"},"duration":0.737567246,"status":200}

```

This data is saved with Loki and displayed in Grafana.
But if I'm going to such far efforts to remove personal information, why even collect any information in the first place? 

In my opinion, there are some very sensible reasons to collect this data. I can see if my instance is performing correctly, if people are actually using it or not, and if people are actually using HTTP3. Furthermore, if my instance breaks for whatever reason, I can respond faster and fix the issue. So, while I am logging requests, I believe the removal of personal information is done in a privacy-respecting manner. Of course, I'm always interested in other ways to do this and all suggestions are always welcome.

### Why does Quant not work?

This SearXNG instance is hosted on a VPS in Singapore. In December 2020, Qwant closed access for multiple countries, one being Singapore. You can read their statement on the matter [here](https://twitter.com/QwantCom/status/1339149434572206080). Therefore, I have deactivated Qwant as a default search engine until Qwant allows Singaporean users to access their service.

### Basic Usage

* ```docker run -it --rm -p 8080:8080 vojkovic/vsearch:production```

* After that just visit http://127.0.0.1:8080 in your browser and stop the server with ctrl-c.

### Development

* Clone this repo: ```git clone https://github.com/vojkovic/vsearch.git```

* After making your changes in `src/less` make sure to update `src/css` by running `update.sh` (python, npm and make needed)

* You can build the docker container locally by running (check out base branch for the alpine base with the needed python packages): ```docker build --pull -f ./Dockerfile -t searxng-dev:latest .```

* Debug the local container with: ```docker run -it --rm -p 8080:8080 searxng-dev:latest```



### Environment Variables (all optional: if not set -> using default settings)

* ```IMAGE_PROXY``` : enable the image proxyfication through SearXNG; the builtin image proxy is used (set this to `true`)

* ```REDIS_URL``` : set the URL of redis server to store data for limiter plugin (for example `redis://redis:6379/0` or `unix:///usr/local/searxng-redis/run/redis.sock?db=0`)

* ```LIMITER``` : limit bot traffic; this option also requires redis to be set up

* ```BASE_URL``` : set the base url (for example example.org would have `https://example.org/` as base)

* ```NAME``` : set the name of the instance, which is for example displayed in the title of the site (for example `vSearch`)

* ```CONTACT``` : set instance maintainer contact (for example `mailto:user@example.org`)

* ```ISSUE_URL``` : set issue url for custom SearXNG repo (for example `https://github.com/vojkovic/vsearch/issues` !Without trailing /)

* ```GIT_URL``` : set git url for custom SearXNG repo (for example `https://github.com/vojkovic/vsearch`)

* ```GIT_BRANCH``` : set git branch for custom SearXNG repo (for example `main`)

* ```PROXY1``` ```PROXY2``` ```PROXY3``` : set proxy server that are applied as round robin for all engines (for example `http://example.org:8080`)
