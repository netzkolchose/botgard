# BotGard 3.0

Open Source Management System for Botanic Garden Collections
built and maintained by [netzkolchose.de](https://netzkolchose.de/) in cooperation with
the [Botanical Garden of the Friedrich Schiller Universität Jena](https://www.botanischergarten.uni-jena.de) and the
[Botanical Garden of the TU Braunschweig](https://www.tu-braunschweig.de/ifp/garten).


## Features

See [Features wiki page](https://github.com/netzkolchose/botgard/wiki/Features-(de)) for a list of features.


## Requirements

To run the System in production mode you'll need:
- Linux or FreeBSD 
- Python 3
- PostgreSQL (recommended)
- nginx
- latex live
- `librsvg2-bin` (labels use the `rsvg-convert` commandline tool)

### Development

To initially set up the development server create a **virtual environment** using tools like
[venv](https://docs.python.org/3/library/venv.html) 
or [virtualenv](https://virtualenv.pypa.io/en/stable/) and then:

```bash
sudo apt install librsvg2-bin
# or any other means to install the rsvg package

cd app
pip install -r requirements.txt
./manage.py migrate
./manage.py createsuperuser
./manage.py botgard_update_config
```

After that you can just run the development server with:
```bash
./manage.py runserver
```

Postgres is required for proper text search in Django's admin views.
If you do not need fulltext search, sqlite will work too.

To create a local database:
```bash
sudo apt install postgresql-server-dev-all
# or any other means to install a local postgres server

# start psql
sudo -u postgres psql

# create user and database
CREATE USER "botgard-user" WITH PASSWORD "botgard-password";
CREATE DATABASE "botgard" ENCODING=UTF8 TEMPLATE=template0 OWNER="botgard-user";

# allow the user to create databases (for unit-testing)
ALTER USER "botgard-user" CREATEDB;
```

### To run the unit-tests:

```bash
./manage.py collectstatic  # needs to be run once before testing
./manage.py test
```

### Docker and CI

[Dockerfile](/Dockerfile) and [app/start-server.sh](app/start-server.sh) 
are the entry points.

#### run unittests in docker image

```shell script
docker build --tag botgard-dev .
docker run -ti --env BOTGARD_RUN_TESTS=1 botgard-dev
```

### Enironment Variables

The following **environment variables** will be used by 
[app/BotGard/settings.py](app/BotGard/settings.py) and the [start-server.sh](app/start-server.sh) script if present:

- `POSTGRES_PASSWORD`: Password of the postgres user, 
  if specified the postgres database backend will be used. 
  Otherwise it falls back to sqlite3.
- `POSTGRES_DATABASE`: Name of the postgres database, defaults to `postgres`
- `POSTGRES_USER`: Name of the postgres user, defaults to `postgres`
- `POSTGRES_HOST`: Name of the postgres host, defaults to `localhost`
- `POSTGRES_PORT`: Name of the postgres host port, defaults to `5432`
- `DJANGO_SECRET_KEY`: Overrides the `SECRET_KEY`, defaults to a fixed sequence
- `DJANGO_TIME_ZONE`: The default timezone, defaults to `Europe/Berlin`
- `DJANGO_ALLOWED_HOSTS`: A list of hosts separated by spaces, defaults to empty list
- `DJANGO_DEBUG`: Set Django debug mode, defaults to `True`
- `HOST_INTERFACE`: Set the interface the Django Application is listening on, defaults to `localhost`

### docker-compose

You can start the application with postgres and a reverse nginx reverse proxy using the included docker-compose configuration.

Just run:

```bash
docker-compose up
```

**WARNING:**
The docker-compose setup is not intended for production use. It shall give you
a simple method to _simulate_ a complete runtime environment with debug mode
disabled, gunicorn, reverse proxy, LaTeX and a propper PostgreSQL database
during development and evaluation. If you still intend to use this
configuration for production, MAKE SHURE you know what you're doing and modify
docker-compose.yml according to your needs.

### Data migration

The database of BotGard can be exported via:
```bash
./manage.py dumpdata -o dump-file.json
```

and imported into a **newly created database** via:

```bash
./manage.py migrate
./manage.py botgard_clear_django_tables
./manage.py loaddata dump-file.json
```

The import requires about 10-15 minutes per 100k objects...


## Documentation

See the [Wiki Page](https://github.com/netzkolchose/botgard/wiki).

## Getting Help and Commercial support

This project is backed by [netzkolchose.de UG](https://netzkolchose.de/)
If you need help implementing or hosting BotGard for your Institution,
please contact us: botgard@netzkolchose.de

## Credits

Thanks to the Botanical Garden Jena especially Stefan Arndt for his ongoing support and input.

## State and RoadMap

See [RoadMap wiki page](https://github.com/netzkolchose/botgard/wiki/Road-Map).
