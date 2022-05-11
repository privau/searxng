# SearXNG

Builds base image from alpine with python packages needed for SearXNG to work. This speeds up SearXNG builds, since the python packages do not need to be rebuild every time.

Production Server / Instance : https://search.vojkovic.xyz



### Development

* Clone this repo: ```git clone https://github.com/vojkovic/searxng.git```

* Switch to `base` branch: ```git checkout base```

* Make your changes to Dockerfile and requirements.txt

* Build image: ```docker build --pull -f ./Dockerfile -t searxng-dev:base .```
