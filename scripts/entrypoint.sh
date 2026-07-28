#!/bin/sh
set -e

# Create /dev/fuse if it doesn't exist
if [ ! -e /dev/fuse ]; then
    mknod /dev/fuse c 10 229
    chmod 666 /dev/fuse
fi

# Prepare and mount attached block devices, if any.
#
# MIGET_MACHINE_VOLUMES is "<device>:<mountpoint>[,<device>:<mountpoint>...]".
# Devices arrive raw and unformatted, so this image owns both formatting and
# mounting them. Unset means there is nothing to do.
#
# mkfs ONLY when blkid finds no filesystem, which is what makes an attached disk
# durable across restarts -- reformatting on every boot would silently erase its
# contents. e2fsck before resize2fs because resize2fs refuses a filesystem whose
# last check predates its last mount, and accepting rc<4 keeps "errors
# corrected" (1) and "corrected, reboot advised" (2) as success while "left
# uncorrected" (4+) still fails. resize2fs then picks up an expanded device for
# free.
#
# Failures are fatal on purpose: booting without an attached data disk looks
# healthy and is not.
if [ -n "$MIGET_MACHINE_VOLUMES" ]; then
    echo "$MIGET_MACHINE_VOLUMES" | tr ',' '\n' | while IFS=: read -r dev mnt; do
        [ -n "$dev" ] && [ -n "$mnt" ] || continue
        echo "Preparing $dev at $mnt"
        if ! blkid "$dev" | grep -q TYPE; then
            echo "  $dev has no filesystem, creating one"
            mkfs.ext4 -q "$dev" || exit 1
        fi
        e2fsck -p -f "$dev"
        rc=$?
        if [ "$rc" -ge 4 ]; then
            echo "  e2fsck on $dev left errors uncorrected (rc=$rc); refusing to mount"
            exit 1
        fi
        resize2fs "$dev" >/dev/null 2>&1 || true
        mkdir -p "$mnt" || exit 1
        mount -t ext4 "$dev" "$mnt" || exit 1
    done || exit 1
fi

if command -v sshd >/dev/null 2>&1; then
    mkdir -p /run/sshd /var/run/sshd
    ssh-keygen -A
    
    if [ -d /home/miget/.ssh ]; then
        chown -R miget:miget /home/miget/.ssh
        chmod 700 /home/miget/.ssh
        if [ -f /home/miget/.ssh/authorized_keys ]; then
            chmod 600 /home/miget/.ssh/authorized_keys
        fi
    fi
fi

if command -v crond >/dev/null 2>&1; then
    mkdir -p /var/spool/cron/crontabs
fi

if command -v podman >/dev/null 2>&1; then
    mkdir -p /var/run/podman /run/podman
    
    # Configure subuid/subgid for rootless podman
    if ! grep -q "^miget:" /etc/subuid 2>/dev/null; then
        echo "miget:100000:65536" >> /etc/subuid
    fi
    if ! grep -q "^miget:" /etc/subgid 2>/dev/null; then
        echo "miget:100000:65536" >> /etc/subgid
    fi
    
    podman system migrate >/dev/null 2>&1 || true
fi

# Detect supervisord config location (Alpine vs Debian/Ubuntu)
if [ -f /etc/supervisord.conf ]; then
    SUPERVISOR_CONF=/etc/supervisord.conf
elif [ -f /etc/supervisor/supervisord.conf ]; then
    SUPERVISOR_CONF=/etc/supervisor/supervisord.conf
else
    echo "Error: supervisord.conf not found"
    exit 1
fi

echo "Starting supervisord..."
exec /usr/bin/supervisord -c "$SUPERVISOR_CONF"
