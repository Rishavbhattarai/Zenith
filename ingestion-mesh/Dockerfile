FROM golang:1.26-alpine AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/ingestor ./cmd/ingestor

FROM alpine:3.20
RUN adduser -D -H app
COPY --from=build /out/ingestor /usr/local/bin/ingestor
USER app
EXPOSE 8080
ENTRYPOINT ["ingestor"]
