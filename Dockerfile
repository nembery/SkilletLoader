FROM nbalasabas/skillet_tools:latest
  
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --no-use-pep517 -r requirements.txt && \
    mkdir /skillets

COPY SkilletLoader/ /app

#RUN curl -i -s -k -X POST https://scanapi.redlock.io/v1/vuln/os \
# -F "fileName=/etc/alpine-release" -F "file=@/etc/alpine-release" \
# -F "fileName=/lib/apk/db/installed" -F "file=@/lib/apk/db/installed" \
# -F "rl_args=report=detail" | grep -i "x-redlock-scancode: pass"

RUN chmod +x /app/*.py