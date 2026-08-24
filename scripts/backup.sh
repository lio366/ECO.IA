#!/usr/bin/env bash
# ECO-IA — Backup script (Hetzner Storage Box)
set -euo pipefail

BACKUP_DIR="/opt/eco-ia"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE="/tmp/eco-ia-backup-${TIMESTAMP}.tar.gz"

: "${HETZNER_STORAGE_BOX_HOST:?Set HETZNER_STORAGE_BOX_HOST}"
: "${HETZNER_STORAGE_BOX_USER:?Set HETZNER_STORAGE_BOX_USER}"

echo "📦 Creating backup archive..."
tar -czf "$ARCHIVE" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")" \
    --exclude="$(basename "$BACKUP_DIR")/.git" \
    --exclude="$(basename "$BACKUP_DIR")/logs"

echo "📤 Uploading to Hetzner Storage Box..."
scp "$ARCHIVE" "${HETZNER_STORAGE_BOX_USER}@${HETZNER_STORAGE_BOX_HOST}:backups/"
rm "$ARCHIVE"

echo "✅ Backup completed: eco-ia-backup-${TIMESTAMP}.tar.gz"
