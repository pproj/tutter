FROM golang:1.19-alpine3.17 as backend-builder

COPY . /src/
WORKDIR /src

RUN apk add --no-cache make=4.3-r1 && make -j "$(nproc)"

FROM node:18 as frontend-builder

COPY ./frontend /src/
WORKDIR /src

RUN npm install && npm run build

FROM alpine:3.17

# hadolint ignore=DL3018
RUN apk add --no-cache ca-certificates

COPY --from=frontend-builder /src/dist /app/dist
COPY --from=backend-builder /src/main /app/main
WORKDIR /app

ENV GIN_MODE=release

EXPOSE 8080

ENTRYPOINT [ "/app/main" ]
