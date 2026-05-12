#!/bin/bash
# =============================================================================
# simple_github.sh — Flask behind nginx + HTTPS on CentOS (dnf)
# Code is already on the server via git. Packages installed system-wide (no venv).
# Usage:  sudo bash scripts/simple_github.sh
# =============================================================================

# =============================================================================
# FILL THESE IN BEFORE RUNNING
# =============================================================================
DOMAIN="matrixcoders.io"
EMAIL="admin@matrixcoders.io"
APP_DIR="/home/matrixcoders/git/triangular-number-matrix"
APP_USER="matrixcoder"
FLASK_PORT=5000
# =============================================================================

echo ""
echo "======================================================"
echo " Triangular Number Matrix — Quick Deploy"
echo "======================================================"
echo ""

# Only two hard stops — everything else keeps going
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Run as root:  sudo bash $0"
    exit 1
fi
if [[ "$DOMAIN" == "your-domain.com" || "$EMAIL" == "your@email.com" ]]; then
    echo "ERROR: Set DOMAIN and EMAIL at the top of this script."
    exit 1
fi

echo "Config:"
echo "  DOMAIN   : $DOMAIN"
echo "  APP_DIR  : $APP_DIR"
echo "  APP_USER : $APP_USER"
echo "  PORT     : $FLASK_PORT"
echo "  Python   : $(python3 --version 2>&1 || echo 'not found')"
echo ""

# ── [1/7] packages ─────────────────────────────────────────────────────────────
echo "[1/7] Installing EPEL, nginx, certbot..."
dnf install -y epel-release
dnf install -y nginx certbot python3-certbot-nginx
echo "      done"

# ── [2/7] nginx config ─────────────────────────────────────────────────────────
echo "[2/7] Writing nginx config..."
cat > /etc/nginx/conf.d/calculator.conf <<NGINX
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass         http://127.0.0.1:${FLASK_PORT};
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_buffering    off;
    }
}
NGINX

nginx -t \
    && echo "      nginx config OK" \
    || echo "      WARNING: nginx config test failed — check /etc/nginx/conf.d/calculator.conf"

# ── [3/7] systemd service ──────────────────────────────────────────────────────
echo "[3/7] Writing systemd service..."
PYTHON3_BIN=$(command -v python3 || echo "/usr/bin/python3")
cat > /etc/systemd/system/calculator.service <<UNIT
[Unit]
Description=Triangular Number Matrix (Flask)
After=network.target

[Service]
User=${APP_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${PYTHON3_BIN} ${APP_DIR}/app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT
echo "      service file written (using $PYTHON3_BIN)"

# ── [4/7] firewall ─────────────────────────────────────────────────────────────
echo "[4/7] Firewall..."
if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-service=http  || true
    firewall-cmd --permanent --add-service=https || true
    firewall-cmd --reload || true
    echo "      ports 80 + 443 opened"
else
    echo "      firewalld not running — skipping (open ports in Hostinger panel if needed)"
fi

# ── [5/7] start Flask ──────────────────────────────────────────────────────────
echo "[5/7] Starting Flask (calculator) service..."
systemctl daemon-reload
systemctl enable calculator || true
systemctl restart calculator || true
sleep 3
systemctl is-active --quiet calculator \
    && echo "      calculator: running" \
    || echo "      WARNING: calculator not running — debug: journalctl -u calculator -n 30 --no-pager"

# ── [6/7] start nginx ──────────────────────────────────────────────────────────
echo "[6/7] Starting nginx..."
systemctl enable nginx || true
systemctl restart nginx || true
systemctl is-active --quiet nginx \
    && echo "      nginx: running" \
    || echo "      WARNING: nginx not running — debug: journalctl -u nginx -n 30 --no-pager"

# ── [7/7] SSL cert ─────────────────────────────────────────────────────────────
echo "[7/7] Obtaining SSL certificate for ${DOMAIN}..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect \
    && echo "      SSL: certificate issued — HTTPS active" \
    || echo "      WARNING: certbot failed — site is HTTP only for now
             Fix: check DNS points to this server, port 80 is open in Hostinger,
             then run manually: certbot --nginx -d $DOMAIN -m $EMAIL --agree-tos"

# ── summary ────────────────────────────────────────────────────────────────────
echo ""
echo "======================================================"
echo " Result"
echo "======================================================"
echo "  calculator : $(systemctl is-active calculator 2>/dev/null)"
echo "  nginx      : $(systemctl is-active nginx      2>/dev/null)"
echo "  url        : https://${DOMAIN}"
echo ""
echo "  Debug commands:"
echo "    journalctl -u calculator -n 50 --no-pager   # Flask logs"
echo "    journalctl -u nginx -n 50 --no-pager         # nginx logs"
echo "    systemctl restart calculator                  # restart Flask"
echo "    nginx -t && systemctl reload nginx            # reload nginx"
echo ""
