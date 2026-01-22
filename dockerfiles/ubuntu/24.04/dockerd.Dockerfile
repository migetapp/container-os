FROM ubuntu:24.04

ENV DOCKER_DATA_DIR=/var/lib/docker
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN apt-get update && apt-get install -y \
    curl \
    supervisor \
    iptables \
    fuse-overlayfs \
    fuse3 \
    openssh-server \
    cron \
    sudo \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /var/log/supervisor /var/run/supervisor

RUN set -eux; \
    groupadd -f miget; \
    if ! id -u miget >/dev/null 2>&1; then \
        useradd -m -g miget -s /bin/bash -p '*' miget; \
    fi; \
    usermod -aG docker miget || true; \
    usermod -aG podman miget || true; \
    usermod -aG sudo miget; \
    echo 'miget ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/miget; \
    chmod 0440 /etc/sudoers.d/miget; \
    mkdir -p /home/miget/.ssh; \
    chown -R miget:miget /home/miget; \
    chmod 700 /home/miget/.ssh

RUN update-alternatives --set iptables /usr/sbin/iptables-legacy && \
    update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy

RUN set -eux; \
    ARCH=$(uname -m); \
    case "$ARCH" in \
        x86_64) COMPOSE_ARCH=x86_64 ;; \
        aarch64) COMPOSE_ARCH=aarch64 ;; \
        armv7l) COMPOSE_ARCH=armv7 ;; \
        *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac; \
    curl -fsSL "https://github.com/docker/compose/releases/download/v5.0.2/docker-compose-linux-${COMPOSE_ARCH}" \
        -o /usr/local/bin/docker-compose; \
    chmod +x /usr/local/bin/docker-compose; \
    docker-compose version

RUN mkdir -p /etc/supervisor/conf.d
COPY config/supervisord.conf /etc/supervisor/supervisord.conf
COPY config/sshd.conf /etc/supervisor/conf.d/sshd.conf
COPY config/crond.conf /etc/supervisor/conf.d/crond.conf
COPY config/dockerd.conf /etc/supervisor/conf.d/dockerd.conf

COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
