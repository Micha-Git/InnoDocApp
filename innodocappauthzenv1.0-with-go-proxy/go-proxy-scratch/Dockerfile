FROM golang:1.25 AS build-stage

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends file

COPY go.mod go.sum ./
RUN go mod download

COPY *.go ./

#RUN CGO_ENABLED=0 GOOS=linux go build -o /go-proxy
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-extldflags=-static" -o /go-proxy

RUN file /go-proxy

# Deploy the application binary into a lean image
FROM scratch AS build-release-stage

WORKDIR /

COPY --from=build-stage /go-proxy /go-proxy

EXPOSE 8484

#USER nonroot:nonroot

ENTRYPOINT ["/go-proxy"]
