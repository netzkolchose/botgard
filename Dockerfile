FROM python:3.11-alpine

# --- install packages ---

RUN apk add bash gcc musl-dev libffi-dev openssl-dev python3-dev postgresql-dev gettext
RUN apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev libxslt-dev libxml2-dev librsvg rsvg-convert
RUN apk add texmf-dist texlive ttf-liberation ttf-linux-libertine texmf-dist-fontsrecommended texmf-dist-latexrecommended
RUN apk add poppler-utils  # for `pdfinfo`
RUN apk add binutils geos proj gdal  # for GeoDjango
RUN apk add libspatialite  # for GeoDjango using sqlite

# make sure django modules find the libraries
RUN ln -s /usr/lib/libproj.so.25 /usr/lib/libproj.so \
    && ln -s /usr/lib/libgdal.so.37 /usr/lib/libgdal.so \
    && ln -s /usr/lib/libgeos_c.so.1 /usr/lib/libgeos_c.so \
    && ln -s /usr/lib/mod_spatialite.so.8 /usr/lib/mod_spatialite.so

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
