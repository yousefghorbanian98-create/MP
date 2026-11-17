# Maintained MIT Dev Containers base; deliberately not a Cirrus Labs Flutter image.
FROM mcr.microsoft.com/devcontainers/base:ubuntu24.04

ARG FLUTTER_VERSION=3.50.0
ARG FLUTTER_REVISION=ab2912035e160d9cad6306df307576da6128ebdb
ARG FLUTTER_ARCHIVE_SHA256=6ea2d806fd57269ae783e6788e2a81fc26eaad782f1e0d0ff38623bb765ff9f5

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates curl git openjdk-17-jdk unzip xz-utils zip \
    && rm -rf /var/lib/apt/lists/*

# The official Flutter archive is pinned by version and SHA-256. Keep the SDK
# writable by the non-root Codespaces user so Flutter can populate its cache.
RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    test "$arch" = "amd64" || { echo "Flutter SDK archive is x64-only; unsupported architecture: $arch" >&2; exit 1; }; \
    archive="flutter_linux_${FLUTTER_VERSION}-stable.tar.xz"; \
    curl --fail --location --retry 3 --retry-all-errors \
      "https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/${archive}" \
      --output "/tmp/${archive}"; \
    echo "${FLUTTER_ARCHIVE_SHA256}  /tmp/${archive}" | sha256sum --check -; \
    mkdir -p /home/vscode/sdk; \
    tar -xJf "/tmp/${archive}" -C /home/vscode/sdk; \
    rm "/tmp/${archive}"; \
    chown -R vscode:vscode /home/vscode/sdk/flutter

ENV FLUTTER_HOME=/home/vscode/sdk/flutter
ENV PUB_CACHE=/home/vscode/.pub-cache
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV FLUTTER_EXPECTED_VERSION=${FLUTTER_VERSION}
ENV FLUTTER_EXPECTED_REVISION=${FLUTTER_REVISION}
ENV PATH=${FLUTTER_HOME}/bin:${JAVA_HOME}/bin:${PATH}

USER vscode
RUN flutter config --no-analytics
