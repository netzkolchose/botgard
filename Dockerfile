FROM python:3.7-alpine

# --- install packages ---

RUN apk add bash gcc musl-dev libffi-dev openssl-dev python3-dev postgresql-dev gettext
RUN apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev
RUN apk add libxslt-dev libxml2-dev
RUN apk add librsvg
RUN apk add texmf-dist texlive
RUN apk add ttf-liberation ttf-linux-libertine

RUN adduser appuser -D -u 9999

# --- install python packages ---

COPY --chown=appuser:appuser ./app/requirements.txt /app/requirements.txt
WORKDIR /app/

RUN pip install -r requirements.txt

# --- copy code and run ---

COPY --chown=appuser:appuser ./app /app

RUN chmod 0755 /app/start-server.sh

USER appuser

ENTRYPOINT ["/app/start-server.sh"]
