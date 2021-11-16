# SearXNG

builds custom SearXNG container with a changed simple theme, settings.yml and bundled with filtron binary; This project builds on top of https://github.com/searxng/searxng (SearXNG vs SearX: https://github.com/searxng/searxng/issues/46) as well as https://github.com/dalf/filtron.



### Project Links

Production Server / Instance : https://paulgo.io

DockerHub : https://hub.docker.com/r/paulgoio/searxng

GitHub : https://github.com/paulgoio/searxng

GitLab : https://paulgo.dev/paulgoio/searxng



### Development

* Clone this repo: ```git clone https://github.com/paulgoio/searxng.git```

* After making your changes make sure to update `searxng.min.css` as well as `searxng-rtl.min.css` by running `update.sh` (docker needed)

* You can build the docker container locally by running: ```docker build --pull -f ./Dockerfile -t searxng-dev:latest .```

* Debug the local container with: ```docker run -it --rm -p 8080:8080 searxng-dev:latest```



This is the base image to speed up SearXNG build times. It basically already builds are the python packages ahead of time
