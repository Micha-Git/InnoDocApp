# Small Envoy image with lua-cjson available for the Lua filter
FROM envoyproxy/envoy:v1.36-latest

# Install lua-cjson (Debian/Ubuntu-based Envoy image)
USER root
RUN apt-get update -o Acquire::http::Timeout=10 -o Acquire::https::Timeout=10 -o Acquire::Retries=3 && \
    apt-get install -y --no-install-recommends lua-cjson && \
    rm -rf /var/lib/apt/lists/*
USER envoy

EXPOSE 80
