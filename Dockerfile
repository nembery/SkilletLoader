FROM registry.gitlab.com/panw-gse/as/as-py-base-image:latest

LABEL description="Skillet Loader Tools"
LABEL version="0.3"
LABEL maintainer="tsautomatedsolutions@paloaltonetworks.com"

WORKDIR /app

ENV PATH="/app:${PATH}"
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --no-use-pep517 -r requirements.txt && \
    mkdir /skillets

COPY SkilletLoader/ /app

#RUN curl -i -s -k -X POST https://scanapi.redlock.io/v1/vuln/os \
# -F "fileName=/etc/alpine-release" -F "file=@/etc/alpine-release" \
# -F "fileName=/lib/apk/db/installed" -F "file=@/lib/apk/db/installed" \
# -F "rl_args=report=detail" | grep -i "x-redlock-scancode: pass"

RUN chmod +x /app/*.py