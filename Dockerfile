FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-pip python3-numpy libpq5 tzdata gettext && \
    apt-get autoremove -y && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/

WORKDIR /app
COPY requirements.txt /app/
RUN MAKEFLAGS="-j$(nproc)" pip install --break-system-packages --no-cache-dir -r requirements.txt

FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-numpy gnuradio libpq5 tzdata gettext && \
    apt-get autoremove -y && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/

COPY --from=builder /usr/local/lib/python3.12/dist-packages/ /usr/local/lib/python3.12/dist-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
WORKDIR /app
COPY . .
COPY entrypoint /entrypoint
RUN django-admin compilemessages && \
    mkdir -p /app/data && \
    ./gen_decoder.sh

EXPOSE 8000
