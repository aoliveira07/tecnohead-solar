FROM ghcr.io/home-assistant/base-debian:trixie

ARG BUILD_VERSION=0.1.13
ARG BUILD_ARCH=local

LABEL \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="app" \
  io.hass.arch="${BUILD_ARCH}"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=UTC \
    APP_VERSION="${BUILD_VERSION}"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
      ca-certificates \
      postgresql \
      postgresql-client \
      python3 \
      python3-pip \
      tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/tecnohead-solar-requirements.txt
RUN python3 -m pip install --break-system-packages --no-cache-dir \
      -r /tmp/tecnohead-solar-requirements.txt \
    && rm /tmp/tecnohead-solar-requirements.txt

RUN useradd --system --home-dir /var/lib/tecnohead-solar --create-home \
      --shell /usr/sbin/nologin solarapp

COPY backend/tecnohead_solar /opt/tecnohead_solar/tecnohead_solar
COPY frontend /opt/frontend
COPY logo.png /opt/logo.png
COPY rootfs /

RUN chmod 0755 /etc/cont-init.d/00-init-solar \
      /etc/services.d/postgres/run \
      /etc/services.d/web/run \
      /etc/services.d/worker/run \
    && mkdir -p /data/tecnohead_solar /run/tecnohead-solar \
    && chown -R solarapp:solarapp /opt/tecnohead_solar /opt/frontend \
    && chown solarapp:solarapp /opt/logo.png \
    && chown -R postgres:postgres /data/tecnohead_solar /run/tecnohead-solar

WORKDIR /opt/tecnohead_solar
