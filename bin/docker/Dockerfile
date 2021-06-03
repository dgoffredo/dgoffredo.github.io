ARG PACKAGES=

FROM debian:buster-slim as blog-build-env

RUN apt-get update && \
    apt-get install -y \
        ca-certificates \
        coreutils \
        findutils \
        gawk \
        graphviz \
        imagemagick \
        jq \
        make \
        nodejs \
        python3 \
        sed \
        webp \
        wget

RUN mkdir /repo
VOLUME /repo
WORKDIR /repo
