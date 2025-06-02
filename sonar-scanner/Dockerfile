FROM cgr.dev/chainguard/wolfi-base AS base


RUN apk update && apk add sonar-scanner-cli openjdk-17

ENV  JAVA_HOME=/usr/lib/jvm/java-17-openjdk
ENV  PATH=$JAVA_HOME/bin:$PATH




