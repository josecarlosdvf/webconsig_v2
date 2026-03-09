#!/usr/bin/env sh
set -eu

CERT_DIR="/etc/nginx/certs"
CERT_FILE="$CERT_DIR/webconsig.crt"
KEY_FILE="$CERT_DIR/webconsig.key"
HTPASSWD_FILE="/etc/nginx/.htpasswd"

mkdir -p "$CERT_DIR"

HTTPS_DOMAIN="${HTTPS_DOMAIN:-localhost}"
HTTPS_ADMIN_USER="${HTTPS_ADMIN_USER:-admin}"
HTTPS_ADMIN_PASSWORD="${HTTPS_ADMIN_PASSWORD:-Admin@123!ChangeMe}"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
  openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -days 365 \
    -subj "/CN=$HTTPS_DOMAIN"
fi

htpasswd -bc "$HTPASSWD_FILE" "$HTTPS_ADMIN_USER" "$HTTPS_ADMIN_PASSWORD"

exec nginx -g "daemon off;"
