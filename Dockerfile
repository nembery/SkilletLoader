FROM python:3.7-alpine

LABEL description="Skillet Loader Tool"
LABEL version="0.1"
LABEL maintainer="sp-solutions@paloaltonetworks.com"

WORKDIR /app

ENV PATH="/app:${PATH}"
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt

RUN apk add --update --no-cache curl libxml2 libxml2-dev libxslt-dev && \
    apk add --virtual build-dependencies build-base && \
	pip install --upgrade pip && \
	pip install --no-cache-dir --no-use-pep517 -r requirements.txt && \
    apk del build-dependencies && \
	mkdir /skillets

COPY SkilletLoader/ /app

RUN curl -i -s -X POST https://scanapi.redlock.io/v1/vuln/os \
 -F "fileName=/etc/alpine-release" -F "file=@/etc/alpine-release" \
 -F "fileName=/lib/apk/db/installed" -F "file=@/lib/apk/db/installed" \
 -F "rl_args=report=detail" | grep -i "x-redlock-scancode: pass"

RUN chmod +x /app/*.py