#!/bin/bash
# =============================================================================
# setup_https.sh — Add HTTPS via Let's Encrypt (certbot) to the calculator
#
# Run this AFTER:
#   1. build_infra.sh has completed successfully
#   2. DNS A record for DOMAIN is pointed to this server's IP
#      (certbot requires HTTP port 80 to be reachable from the internet)
#
# Usage: sudo bash APP_DIR/scripts/setup_https.sh
# =============================================================================

# =============================================================================
# FILL THESE IN (must match what you used in build_infra.sh)
# =============================================================================
DOMAIN="matrixcoders.io"
EMAIL="admin@matrixcoders.io"
# =============================================================================

echo ""
echo "======================================================"
echo " setup_https.sh — Let's Encrypt HTTPS"
echo "======================================================"
echo ""

# Hard exit: must be root
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Run as root:  sudo bash $0"
    exit 1
fi

# Hard exit: EMAIL must be filled in
if [[ "$EMAIL" == "your@email.com" || "$EMAIL" == "admin@matrixcoders.io" && "$DOMAIN" != "matrixcoders.io" ]]; then
    echo "ERROR: Update EMAIL at the top of this script."
    exit 1
fi

echo "Config:"
echo "  DOMAIN : $DOMAIN"
echo "  EMAIL  : $EMAIL"
echo ""
echo "Checking DNS (this is informational only — certbot will fail if DNS is wrong):"
echo "  Resolved IP : $(dig +short $DOMAIN 2>/dev/null | tail -1 || echo 'dig not available')"
echo "  Server IP   : $(curl -s ifconfig.me 2>/dev/null || echo 'unknown')"
echo ""

# ── [1/3] install certbot ──────────────────────────────────────────────────────
echo "[1/3] Installing certbot..."
dnf install -y certbot python3-certbot-nginx \
    && echo "      certbot: OK" \
    || echo "      WARNING: certbot install had errors — continuing anyway"

# ── [2/3] obtain certificate ───────────────────────────────────────────────────
echo "[2/3] Obtaining SSL certificate for $DOMAIN..."
echo "      (this will fail if $DOMAIN does not resolve to this server's IP)"
echo ""

certbot --nginx \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    -m "$EMAIL" \
    --redirect \
    && echo "" \
    && echo "      SSL: certificate issued — HTTPS active" \
    || {
        echo ""
        echo "      WARNING: certbot failed. Common causes:"
        echo "        - DNS A record for $DOMAIN not pointing to this server"
        echo "        - Port 80 blocked by cloud firewall (open it in your hosting panel)"
        echo "        - nginx not running (check: systemctl status nginx)"
        echo ""
        echo "      Retry manually once DNS is ready:"
        echo "        certbot --nginx -d $DOMAIN -m $EMAIL --agree-tos --redirect"
    }

# ── [3/3] reload nginx ─────────────────────────────────────────────────────────
echo "[3/3] Reloading nginx..."
nginx -t \
    && systemctl reload nginx \
    && echo "      nginx: reloaded" \
    || echo "      WARNING: nginx reload failed — check: nginx -t"

# ── summary ────────────────────────────────────────────────────────────────────
echo ""
echo "======================================================"
echo " Result"
echo "======================================================"
echo "  nginx      : $(systemctl is-active nginx 2>/dev/null)"
echo "  calculator : $(systemctl is-active calculator 2>/dev/null)"
echo "  url        : https://${DOMAIN}/tnm-calculator/"
echo ""
echo "  Auto-renewal: managed by certbot's systemd timer"
echo "  Test renewal: certbot renew --dry-run"
echo ""
echo "  If HTTPS is not working yet:"
echo "    1. Verify DNS: dig +short $DOMAIN"
echo "    2. Verify port 80 open from outside: curl http://$DOMAIN/"
echo "    3. Re-run: certbot --nginx -d $DOMAIN -m $EMAIL --agree-tos --redirect"
echo "======================================================"
echo ""
