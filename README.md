# Tutter

Tutter is a simple social platform. Developed for PP'23.

https://pproj.net/


## Build

Tutter can be built using it's single Dockerfile.

```shell
cd tutter
docker build -t tutter .
```

## Run

Tutter is designed to run from a single container. It only have one dependency and that is a Postgresql database.

Tutter can be accessed over HTTP on port :8080. It does not terminate TLS, however. You may need a reverse proxy for that.

## Configure

Tutter can be configured using the following env-vars:

| Envvar           | Default                           | Description                                              |
|------------------|-----------------------------------|----------------------------------------------------------|
| `POSTGRESQL_DSN` | `postgresql://localhost/postgres` | The DSN of the single Postgresql database used by Tutter |

## API

For Open API 3.0 definition See `/apidoc/spec.yaml`.

For Swagger UI the `/api` endpoint while running Tutter.

**Note:** The code is not generated from API specification. The specification is updated manually for each change.