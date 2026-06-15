FROM python:3.11-alpine

# --- install packages ---

RUN apk add bash gcc musl-dev libffi-dev openssl-dev python3-dev postgresql-dev gettext
RUN apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev libxslt-dev libxml2-dev librsvg rsvg-convert
RUN apk add texmf-dist texlive ttf-liberation ttf-linux-libertine texmf-dist-fontsrecommended texmf-dist-latexrecommended
RUN apk add poppler-utils  # for `pdfinfo`
RUN apk add binutils geos proj gdal  # for GeoDjango
RUN apk add libspatialite  # for GeoDjango using sqlite

# make sure django modules find the libraries
# (find alphabetically latest entry for each lib, e.g. /usr/lib/libproj.so.39.3.13.0 and symlink to libproj.so)
RUN ln -sf `ls /usr/lib/libproj.so.* | cut -d' ' -f1 | tail -n 1` /usr/lib/libproj.so
RUN ln -sf `ls /usr/lib/libgdal.so.* | cut -d' ' -f1 | tail -n 1` /usr/lib/libgdal.so
RUN ln -sf `ls /usr/lib/libgeos_c.so.* | cut -d' ' -f1 | tail -n 1` /usr/lib/libgeos_c.so
RUN ln -sf `ls /usr/lib/mod_spatialite.so.* | cut -d' ' -f1 | tail -n 1` /usr/lib/mod_spatialite.so

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
