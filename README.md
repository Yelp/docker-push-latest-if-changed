[![Build Status](https://travis-ci.org/Yelp/docker-push-latest-if-changed.svg?branch=master)](https://travis-ci.org/Yelp/docker-push-latest-if-changed)
[![Coverage Status](https://coveralls.io/repos/github/Yelp/docker-push-latest-if-changed/badge.svg?branch=master)](https://coveralls.io/github/Yelp/docker-push-latest-if-changed?branch=master)

docker-push-latest-if-changed
=============================

At Yelp, we build base images and push them daily to our internal registry.
The reason we chose to build daily is to receive new security packages when
they become available.  The cost of this is your base image is invalidated
every day requiring a brand new build of your consuming image.  This tool
aims to alleviate that issue by only pushing a new `:latest` tagged image
if the image actually changes in a meaningful way.

## Installation

### Python installation

`pip install docker-push-latest-if-changed`

### debian installation

Grab the latest released debian from the
[releases](https://github.com/Yelp/docker-push-latest-if-changed/releases)
tab.

### Standalone script

The tool is a single file which only has dependencies on python3 and a
working `docker` executable.  You can simply drop the file onto your `PATH`:

```
curl https://raw.githubusercontent.com/Yelp/docker-push-latest-if-changed/master/docker_push_latest_if_changed.py > /usr/local/bin/docker-push-latest-if-changed
chmod 755 /usr/local/bin/docker-push-latest-if-changed
```

## Heuristics

The tool makes its decision based on the following things:

### Checksum of `docker history` commands

`docker history` usefully includes hashes of `ADD`ed / `COPY`d files along with commands.

For example, here's the history for `debian:stretch`

```
$ docker history --no-trunc debian:stretch
IMAGE                                                                     CREATED             CREATED BY                                                                                          SIZE                COMMENT
sha256:51f0da81de8aa83353909e16b0a0361ea7d0790de04aad406b1ed23b166e36da   2 weeks ago         /bin/sh -c #(nop)  CMD ["/bin/bash"]                                                                0 B
<missing>                                                                 2 weeks ago         /bin/sh -c #(nop) ADD file:b784c500074cf93203f92498cb90882e098a854589ab7274432b376198176dfa in /    99.99 MB
```

From this, the tool would only consider:

```
/bin/sh -c #(nop)  CMD ["/bin/bash"]
/bin/sh -c #(nop) ADD file:b784c500074cf93203f92498cb90882e098a854589ab7274432b376198176dfa in /
```

### (debian) length and checksum of `dpkg -l`

An `apt-get install` line may lead to any number of packages being installed.
This heuristic will ensure that if new packages are installed that a new
`:latest` tag gets pushed.  While not necessary for correctness, the length
of `dpkg -l` is produced to aid in debugging.

## Usage

### cli

```
usage: docker-push-latest-if-changed [-h] --source SOURCE [--target TARGET]

optional arguments:
  -h, --help       show this help message and exit
  --source SOURCE  Local image tag to be considered for pushing. For example
                   `--source docker.example.com/img-name:2017.01.05`.
  --target TARGET  Target remote image to push if the docker image is changed.
                   If omitted, the image will be $repository:latest of the
                   `--source` image.
```

### Usage in CI

The general usage pattern looks something like this:

```
$ docker build --no-cache -t $TARGET:$BUILDTIME
...
# optionally run some sort of integration test here
# $ docker run -v $PWD/itest:/itest:ro $TARGET:$BUILDTIME /itest/itest.sh
$ docker-push-latest-if-changed --source $TARGET:$BUILDTIME
```

## Side-effects

The "source" image here refers to that specified in `--source`.  The target
image here refers to that specified in `--target` *or* the `:latest` tag of
the image specified in `--source`.

1. The tool will `docker pull` the target image (to inspect for changes)
2. The tool will run your source image (to collect `dpkg -l` output).
3. The tool will *invariantly* `docker push` the source image.
4. If the tool determines the target image has changed it will:
    - `docker tag` the target image.
    - `docker push` the target image.
