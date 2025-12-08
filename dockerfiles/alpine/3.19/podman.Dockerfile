FROM alpine:3.19

ENV DOCKER_DATA_DIR=/var/lib/docker

RUN apk add --no-cache \
    bash \
    supervisor \
    openssh \
    dcron \
    iptables-legacy \
    fuse-overlayfs \
    fuse3 \
    sudo \
    podman \
    podman-docker \
    slirp4netns \
    shadow-subids

RUN set -eux; \
    group_name=$(getent group 1000 | cut -d: -f1 || true); \
    if [ -z "$group_name" ]; then \
        addgroup -g 1000 miget; \
        group_name=miget; \
    fi; \
    if ! id -u miget >/dev/null 2>&1; then \
        adduser -D -u 1000 -G "$group_name" -s /bin/bash miget; \
        passwd -u miget; \
    fi; \
    addgroup miget docker 2>/dev/null || true; \
    addgroup miget podman 2>/dev/null || true; \
    addgroup miget wheel 2>/dev/null || true; \
    echo '%wheel ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/wheel; \
    chmod 0440 /etc/sudoers.d/wheel; \
    mkdir -p /home/miget/.ssh; \
    chown -R miget:"$group_name" /home/miget; \
    chmod 700 /home/miget/.ssh

RUN mkdir -p /var/log/supervisor /var/run/supervisor

RUN LEGACY_IP=$(command -v iptables-legacy) && \
    LEGACY_IP6=$(command -v ip6tables-legacy) && \
    ln -sf "$LEGACY_IP" /sbin/iptables && \
    ln -sf "$LEGACY_IP" /usr/sbin/iptables && \
    ln -sf "$LEGACY_IP6" /sbin/ip6tables && \
    ln -sf "$LEGACY_IP6" /usr/sbin/ip6tables

RUN set -eux; \
    ARCH=$(uname -m); \
    case "$ARCH" in \
        x86_64) COMPOSE_ARCH=x86_64 ;; \
        aarch64) COMPOSE_ARCH=aarch64 ;; \
        armv7l) COMPOSE_ARCH=armv7 ;; \
        *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac; \
    wget -qO /usr/local/bin/docker-compose \
        "https://github.com/docker/compose/releases/download/v5.0.0/docker-compose-linux-${COMPOSE_ARCH}"; \
    chmod +x /usr/local/bin/docker-compose; \
    docker-compose version

RUN mkdir -p /etc/supervisor/conf.d
COPY config/supervisord.conf /etc/supervisord.conf
COPY config/sshd.conf /etc/supervisor/conf.d/sshd.conf
COPY config/crond.conf /etc/supervisor/conf.d/crond.conf
COPY config/podman.conf /etc/supervisor/conf.d/podman.conf

COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
