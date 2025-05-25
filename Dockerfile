FROM golang:1.23-alpine as backend-builder

COPY . /src/
WORKDIR /src

RUN apk add --no-cache make=4.4.1-r2 && make -j "$(nproc)"

FROM node:18 as frontend-builder

COPY ./frontend /src/
WORKDIR /src

RUN npm install && npm run build

FROM alpine:3.21

# hadolint ignore=DL3018
RUN apk add --no-cache ca-certificates

COPY --from=frontend-builder /src/dist /app/dist
COPY --from=backend-builder /src/main /app/main
COPY ./apidoc /app/apidoc
WORKDIR /app

ENV DEBUG=false

EXPOSE 8080

ENTRYPOINT [ "/app/main" ]
