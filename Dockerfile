FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential git python3 python3-dev python3-pip python3-numpy libpq5 tzdata gettext libjpeg8-dev libopenexr-dev libpng-dev libfreetype6-dev && \
    apt-get autoremove -y && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/

RUN pip download --no-binary OpenImageIO openimageio==3.0.11.0 && \
    tar -xzf openimageio-*.tar.gz && \
    cd openimageio-* && \
    sed -i '/include (testing)/d' CMakeLists.txt && \
    pip install --config-settings=cmake.build-type=MinSizeRel --config-settings=cmake.args="-DLINKSTATIC=0" --break-system-packages .

WORKDIR /app
COPY requirements.txt /app/
RUN arch=$(dpkg --print-architecture) && [ "$arch" = "armhf" ] && sed -i '/ai-edge-litert/d' requirements.txt || true
RUN MAKEFLAGS="-j$(nproc)" pip install --break-system-packages --no-cache-dir -r requirements.txt

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-numpy gnuradio libpq5 tzdata ca-certificates gettext libjpeg8 libopenexr-3-1-30 libpng16-16t64 libfreetype6 && \
    apt-get autoremove -y && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/

COPY --from=builder /usr/local/lib/python3.12/dist-packages/ /usr/local/lib/python3.12/dist-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
WORKDIR /app
COPY . .
COPY /entrypoint/* /entrypoint/
RUN django-admin compilemessages && \
    mkdir -p /app/data && \
    ./gen_decoder.sh && \
    ./manage.py runscript download_libs --script-args="-c libs.json -o static/libs/" && \
    chown -R ubuntu:ubuntu /app/
ARG VERSION=""
ARG COMMIT=""
ARG CHANGES=""
RUN echo "$(TZ=UTC date +"%Y-%m-%dT%H:%M:%S%z")" | tee /sdr_monitor_build_time && \
    echo "$VERSION" | tee /sdr_monitor_version && \
    echo "$COMMIT" | tee /sdr_monitor_commit && \
    echo "$CHANGES" | tee /sdr_monitor_changes

EXPOSE 8000
ENTRYPOINT [ "/entrypoint/entrypoint.sh" ]
