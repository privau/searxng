# SearXNG

Builds base image from alpine with python packages needed for SearXNG to work. This speeds up SearXNG builds, since the python packages do not need to be rebuild every time.



### Project Links

Production Server / Instance : https://paulgo.io

DockerHub : https://hub.docker.com/r/paulgoio/searxng

GitHub : https://github.com/paulgoio/searxng

GitLab : https://paulgo.dev/paulgoio/searxng



### Development

* Clone this repo: ```git clone https://github.com/paulgoio/searxng.git```

* Switch to `base` branch: ```git checkout base```

* Make your changes to Dockerfile and requirements.txt

* Build image: ```docker build --pull -f ./Dockerfile -t searxng-dev:base .```
