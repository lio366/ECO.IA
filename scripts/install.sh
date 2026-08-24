#!/usr/bin/env bash
# ECO-IA — Automated installer for Ubuntu 22.04 (OVHcloud / Hetzner VPS)
set -euo pipefail

REPO_URL="https://github.com/lio366/ECO.IA.git"
INSTALL_DIR="/opt/eco-ia"
SERVICE_USER="eco-ia"

echo "🌱 ECO-IA Installer starting..."

# Dependencies
apt-get update -qq
apt-get install -y --no-install-recommends git curl docker.io docker-compose-v2 ufw fail2ban

# Create service user
id -u "$SERVICE_USER" &>/dev/null || useradd -r -s /bin/false "$SERVICE_USER"

# Clone / update
if [ -d "$INSTALL_DIR/.git" ]; then
  git -C "$INSTALL_DIR" pull
else
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

chown -R "$SERVICE_USER":"$SERVICE_USER" "$INSTALL_DIR"

# Configure env
if [ ! -f "$INSTALL_DIR/.env" ]; then
  cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
  echo "⚠️  Edit $INSTALL_DIR/.env before starting."
fi

# UFW firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw --force enable

# Start with Docker Compose
cd "$INSTALL_DIR"
docker compose -f docker/docker-compose.yml up -d --build

echo "✅ ECO-IA installed. API: http://$(curl -s ifconfig.me):8000"
