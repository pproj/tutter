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

Tutter can be accessed over HTTP on port :8080. It does not terminate TLS, however. You may need a reverse proxy for
that.

## Configure

Tutter can be configured using the following env-vars:

| Envvar                       | Default                           | Description                                                                                                                  |
|------------------------------|-----------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| `POSTGRESQL_DSN`             | `postgresql://localhost/postgres` | The DSN of the single Postgresql database used by Tutter                                                                     |
| `POSTGRESQL_MAX_CONNECTIONS` | `50`                              | Max connection limit to the Postgresql database (psql allow only 100 by default, going above this will result in 500 errors) |
| `DEBUG`                      | `false`                           | Enable Debug logging and some debug features                                                                                 |

## API

For Open API 3.0 definition See `/apidoc/spec.yaml`.

For Swagger UI the `/api` endpoint while running Tutter.

**Note:** The code is not generated from API specification. The specification is updated manually for each change.

## E2E Testing

Tutter comes with a simple hacky e2e test suite written in Python.
It basically just does a bunch of api requests towards Tutter to see if everything works correctly. If not the tests
fail, and you might be able to figure out the reason.
The test suite also connects to Tutter's Postgresql database in order to perform cleaning before and after the test
runs.

You may configure the e2e suite with the following envvars:

- `PSQL_DSN`
- `BASE_URL`

To run the test suite, start an instance of Tutter with the postgresql db reachable from the computer you will run your
test on.
Then create a venv in the e2e directory, and install dependencies. Once that's done, you may start the `run.py` script
which will perform the tests.
If all tests passed, the script will exit with exitcode 0, if any of the tests failed, the script will exit with
exitcode 1.