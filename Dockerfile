# ------------------------------------------------------------------------
# Custom Airflow image for the News Extractor crawler pipeline.
#
# Build:
#   docker compose build
#
# Extends the official Apache Airflow image with project runtime deps.
# ------------------------------------------------------------------------
FROM apache/airflow:2.10.5-python3.12

# ── 1. Install system build deps (as root) ──────────────────────────
USER root
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        libxml2-dev \
        libxslt1-dev \
        build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── 2. Install Python deps (as airflow — enforced by base image) ───
COPY requirements.txt /tmp/requirements.txt
USER airflow
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ── 3. Clean up build deps + pre-create data dir (as root) ─────────
USER root
RUN rm /tmp/requirements.txt && \
    apt-get remove -y libxml2-dev libxslt1-dev build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Make /opt/airflow/data writable by the airflow user (UID 50000).
# Docker copies image directory ownership into the named volume on first mount.
RUN mkdir -p /opt/airflow/data && \
    chown airflow:root /opt/airflow/data && \
    chmod 775 /opt/airflow/data

USER airflow
