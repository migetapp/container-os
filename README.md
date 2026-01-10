# Miget Container OS

Miget Container OS provides the base runtime used by [Miget's](https://miget.com) Platform-as-a-Service and Cloud offerings. Each image bundles the tooling required to run container workloads inside a Miget MicroVM, delivering strong isolation while keeping familiar Docker or Podman workflows.

## What is a MicroVM?

Miget MicroVMs are lightweight virtual machines tailored for container execution. They boot a minimal userland, expose only the services required for workload orchestration, and rely on hardware virtualization for strong isolation. Compared with traditional nested containers, MicroVMs eliminate the need for user-namespace tricks or rootless shims-the workload runs with full privileges inside the VM while the host maintains isolation boundaries.

## Current Release: 1.0.8

### Component Versions

| Component | Ubuntu 22.04<br/>dockerd | Ubuntu 22.04<br/>podman | Ubuntu 24.04<br/>dockerd | Ubuntu 24.04<br/>podman | Alpine 3.19<br/>dockerd | Alpine 3.19<br/>podman | Alpine 3.20<br/>dockerd | Alpine 3.20<br/>podman | Alpine 3.21<br/>dockerd | Alpine 3.21<br/>podman | Alpine 3.22<br/>dockerd | Alpine 3.22<br/>podman |
|-----------|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|:----------:|
| **Docker Compose** | v5.0.1 | v5.0.1 | v5.0.1 | v5.0.1 | v5.0.1 | v5.0.1 | v5.0.1 | v5.0.1 | v5.0.1 | v5.0.1 | v5.0.1 | v5.0.1 |
| **Docker CE** | 5:29.1.4-1\~ubuntu.22.04\~jammy | - | 5:29.1.4-1\~ubuntu.24.04\~noble | - | 25.0.5-r1 | - | 26.1.5-r0 | - | 27.3.1-r5 | - | 28.3.3-r4 | - |
| **Podman** | - | 3.4.4+ds1-1ubuntu1.22.04.3 | - | 4.9.3+ds1-1ubuntu0.2 | - | 4.8.3-r3 | - | 5.2.5-r0 | - | 5.3.2-r5 | - | 5.6.2-r2 |
| **Containerd** | 2.2.1-1\~ubuntu.22.04\~jammy | - | 2.2.1-1\~ubuntu.24.04\~noble | - | 1.7.10-r3 | - | 1.7.17-r2 | - | 2.0.0-r5 | - | 2.1.5-r1 | - |
| **OpenSSH** | 1:8.9p1-3ubuntu0.13 | 1:8.9p1-3ubuntu0.13 | 1:9.6p1-3ubuntu13.14 | 1:9.6p1-3ubuntu13.14 | 9.6_p1-r2 | 9.6_p1-r2 | 9.7_p1-r5 | 9.7_p1-r5 | 9.9_p2-r0 | 9.9_p2-r0 | 10.0_p1-r10 | 10.0_p1-r10 |
| **Supervisor** | 4.2.1-1ubuntu1 | 4.2.1-1ubuntu1 | 4.2.5-1ubuntu0.1 | 4.2.5-1ubuntu0.1 | 4.2.5-r4 | 4.2.5-r4 | 4.2.5-r5 | 4.2.5-r5 | 4.2.5-r5 | 4.2.5-r5 | 4.2.5-r5 | 4.2.5-r5 |

> **Note**: All images include standalone docker-compose binary at `/usr/local/bin/docker-compose`, independent of the docker-compose-plugin that comes with Docker CE.

## Supported tags and respective Dockerfiles

- **Alpine 3.19 dockerd**

  `1.0.8-alpine-3.19.9-dockerd`, `1.0.8-alpine3.19-dockerd`, `1.0.8-alpine3.19`, `alpine3.19`, `stable-alpine3.19-dockerd`
  ([`dockerfiles/alpine/3.19/dockerd.Dockerfile`](dockerfiles/alpine/3.19/dockerd.Dockerfile))

- **Alpine 3.19 podman**

  `1.0.8-alpine-3.19.9-podman`, `1.0.8-alpine3.19-podman`, `stable-alpine3.19-podman`
  ([`dockerfiles/alpine/3.19/podman.Dockerfile`](dockerfiles/alpine/3.19/podman.Dockerfile))

- **Alpine 3.20 dockerd**

  `1.0.8-alpine-3.20.8-dockerd`, `1.0.8-alpine3.20-dockerd`, `1.0.8-alpine3.20`, `alpine3.20`, `stable-alpine3.20-dockerd`
  ([`dockerfiles/alpine/3.20/dockerd.Dockerfile`](dockerfiles/alpine/3.20/dockerd.Dockerfile))

- **Alpine 3.20 podman**

  `1.0.8-alpine-3.20.8-podman`, `1.0.8-alpine3.20-podman`, `stable-alpine3.20-podman`
  ([`dockerfiles/alpine/3.20/podman.Dockerfile`](dockerfiles/alpine/3.20/podman.Dockerfile))

- **Alpine 3.21 dockerd**

  `1.0.8-alpine-3.21.5-dockerd`, `1.0.8-alpine3.21-dockerd`, `1.0.8-alpine3.21`, `alpine3.21`, `stable-alpine3.21-dockerd`
  ([`dockerfiles/alpine/3.21/dockerd.Dockerfile`](dockerfiles/alpine/3.21/dockerd.Dockerfile))

- **Alpine 3.21 podman**

  `1.0.8-alpine-3.21.5-podman`, `1.0.8-alpine3.21-podman`, `stable-alpine3.21-podman`
  ([`dockerfiles/alpine/3.21/podman.Dockerfile`](dockerfiles/alpine/3.21/podman.Dockerfile))

- **Alpine 3.22 dockerd**

  `1.0.8-alpine-3.22.2-dockerd`, `1.0.8-alpine3.22-dockerd`, `1.0.8-alpine3.22`, `alpine3.22`, `latest-alpine`, `stable-alpine3.22-dockerd`
  ([`dockerfiles/alpine/3.22/dockerd.Dockerfile`](dockerfiles/alpine/3.22/dockerd.Dockerfile))

- **Alpine 3.22 podman**

  `1.0.8-alpine-3.22.2-podman`, `1.0.8-alpine3.22-podman`, `stable-alpine3.22-podman`
  ([`dockerfiles/alpine/3.22/podman.Dockerfile`](dockerfiles/alpine/3.22/podman.Dockerfile))

- **Ubuntu 22.04 dockerd**

  `1.0.8-ubuntu-22.04-dockerd`, `1.0.8-ubuntu22-dockerd`, `1.0.8-ubuntu22`, `ubuntu22`, `stable-ubuntu22-dockerd`
  ([`dockerfiles/ubuntu/22.04/dockerd.Dockerfile`](dockerfiles/ubuntu/22.04/dockerd.Dockerfile))

- **Ubuntu 22.04 podman**

  `1.0.8-ubuntu-22.04-podman`, `1.0.8-ubuntu22-podman`, `stable-ubuntu22-podman`
  ([`dockerfiles/ubuntu/22.04/podman.Dockerfile`](dockerfiles/ubuntu/22.04/podman.Dockerfile))

- **Ubuntu 24.04 dockerd**

  `1.0.8-ubuntu-24.04-dockerd`, `1.0.8-ubuntu24-dockerd`, `1.0.8-ubuntu24`, `ubuntu24`, `latest`, `stable-ubuntu24-dockerd`
  ([`dockerfiles/ubuntu/24.04/dockerd.Dockerfile`](dockerfiles/ubuntu/24.04/dockerd.Dockerfile))

- **Ubuntu 24.04 podman**

  `1.0.8-ubuntu-24.04-podman`, `1.0.8-ubuntu24-podman`, `stable-ubuntu24-podman`
  ([`dockerfiles/ubuntu/24.04/podman.Dockerfile`](dockerfiles/ubuntu/24.04/podman.Dockerfile))


## Image Matrix

Images are generated from the templates in `templates/` and published under the `miget/container-os` repository on Docker Hub. Variants exist for:

- Ubuntu 22.04 & 24.04 with either dockerd or podman
- Alpine 3.19, 3.20, 3.21, 3.22 with either dockerd or podman

Concrete Dockerfiles are rendered into `dockerfiles/<os>/<version>/<engine>.Dockerfile` for each supported combination.

## Services Managed by Supervisord

Every image starts `supervisord`, which launches and supervises the following programs:

- **sshd** – Provides a fully functional remote shell for the `miget` user (SSH key-based)
- **crond** – Executes scheduled maintenance jobs inside the MicroVM
- **dockerd** *or* **podman** – Container runtime chosen by the image flavor

During boot the entrypoint script prepares `/run/sshd`, `/var/run/sshd`, `/var/spool/cron`, and runtime state for Podman when applicable.

## Running the Images Locally

All flavors expect privileged execution. When testing, run with `--privileged` (or the equivalent in your orchestration system) and map ports as needed for SSH.

### Ubuntu with dockerd

```bash
docker run --rm -d \
  --name miget-ubuntu-dockerd \
  --privileged \
  -p 2222:22 \
  miget/container-os:latest
```

### Ubuntu with podman

```bash
docker run --rm -d \
  --name miget-ubuntu-podman \
  --privileged \
  -p 2223:22 \
  miget/container-os:ubuntu24-podman
```

### Alpine with dockerd

```bash
docker run --rm -d \
  --name miget-alpine-dockerd \
  --privileged \
  -p 2224:22 \
  miget/container-os:alpine3.22
```

### Alpine with podman

```bash
docker run --rm -d \
  --name miget-alpine-podman \
  --privileged \
  -p 2225:22 \
  miget/container-os:alpine3.22-podman
```

These commands expose SSH on the host for troubleshooting; docker-in-docker or podman-in-podman operations will use the runtime inside the MicroVM.

## Default User and SSH Access

Each image creates a passwordless `miget` user (UID/GID 1000) with an empty `/home/miget/.ssh/authorized_keys`. Supply your public key by mounting a file when launching the container:

```bash
docker run --rm -d \
  --name miget-ubuntu-dockerd \
  --privileged \
  -p 2222:22 \
  -v $(pwd)/authorized_keys:/home/miget/.ssh/authorized_keys:ro \
  miget/container-os:latest
```

Permissions on the directory (`700`) and file (`600`) are enforced by the image. Connect using:

```bash
ssh -p 2222 miget@localhost
```

## Privileged Environment Requirements

All images are intended to run with full privileges. This matches Miget's MicroVM execution model and avoids brittle rootless/container hacks. When running under Kubernetes or Docker, ensure the pod or container is privileged; the workflows expect access to `/dev/fuse`, iptables, and kernel features commonly restricted in non-privileged contexts.

## Contributing

See `DEVELOPMENT.md` for contributor workflow details, including local development setup, manifest updates, validation, and publishing pipelines.

## License

Copyright © 2025 [Miget](https://miget.com)

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.
