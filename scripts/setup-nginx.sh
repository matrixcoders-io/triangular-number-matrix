#!/bin/bash
# =============================================================================
# setup-nginx.sh
# Installs nginx + certbot on CentOS (Hostinger), configures it as a reverse
# proxy for the Triangular Number Matrix Flask/Gunicorn app, issues a free
# Let's Encrypt SSL certificate, and registers the app as a systemd service.
#
# Run as root:  sudo bash scripts/setup-nginx.sh
# =============================================================================

set -euo pipefail

# =============================================================================
# FILL THESE IN BEFORE RUNNING
# =============================================================================
DOMAIN="your-domain.com"            # e.g. calc.example.com
EMAIL="your@email.com"              # Let's Encrypt renewal notifications
APP_DIR="/home/user/triangular-number-matrix"  # absolute path to project root
APP_USER="user"                     # Linux user that owns the project files
VENV_DIR="$APP_DIR/.venv"           # virtualenv (gunicorn must be installed here)
FLASK_PORT=5000
# =============================================================================

# ── helpers ──────────────────────────────────────────────────────────────────
info()  { echo -e "\n\033[1;34m▶ $*\033[0m"; }
ok()    { echo -e "\033[1;32m✔ $*\033[0m"; }
die()   { echo -e "\033[1;31m✘ $*\033[0m" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Run this script as root (sudo bash $0)"

# Validate required variables
[[ "$DOMAIN"   == "your-domain.com" ]] && die "Set DOMAIN at the top of the script before running."
[[ "$EMAIL"    == "your@email.com"  ]] && die "Set EMAIL at the top of the script before running."
[[ -d "$APP_DIR" ]]                    || die "APP_DIR '$APP_DIR' does not exist."
id "$APP_USER" &>/dev/null             || die "APP_USER '$APP_USER' does not exist on this system."
[[ -x "$VENV_DIR/bin/gunicorn" ]]      || die "gunicorn not found at $VENV_DIR/bin/gunicorn. Run: pip install gunicorn"

# ── package manager ──────────────────────────────────────────────────────────
info "Detecting package manager"
if command -v dnf &>/dev/null; then
    PKG=dnf
    CERTBOT_PLUGIN="python3-certbot-nginx"
else
    PKG=yum
    CERTBOT_PLUGIN="python2-certbot-nginx"
fi
ok "Using $PKG"

# ── install packages ─────────────────────────────────────────────────────────
info "Installing EPEL repository"
$PKG install -y epel-release

info "Installing nginx"
$PKG install -y nginx

info "Installing certbot + nginx plugin"
$PKG install -y certbot "$CERTBOT_PLUGIN"

# ── nginx config ─────────────────────────────────────────────────────────────
NGINX_CONF="/etc/nginx/conf.d/calculator.conf"
info "Writing nginx config → $NGINX_CONF"

cat > "$NGINX_CONF" <<NGINX
# Rate-limit zones — valid here because conf.d/ is included inside nginx's http {} block
# SEC-05: protect heavy compute endpoints from abuse
limit_req_zone \$binary_remote_addr zone=tnm_calc:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=tnm_lab:10m  rate=1r/m;

server {
    listen 80;
    server_name ${DOMAIN};

    # Security headers
    add_header X-Frame-Options        "SAMEORIGIN"   always;
    add_header X-Content-Type-Options "nosniff"      always;
    add_header Referrer-Policy        "strict-origin" always;

    # SEC-03 / SEC-04: block external access to stats write endpoints
    location /stats/history/clear {
        allow 127.0.0.1;
        deny  all;
        proxy_pass http://127.0.0.1:${FLASK_PORT}/stats/history/clear;
        proxy_set_header Host \$host;
    }
    location /stats/history/append {
        allow 127.0.0.1;
        deny  all;
        proxy_pass http://127.0.0.1:${FLASK_PORT}/stats/history/append;
        proxy_set_header Host \$host;
    }

    # SEC-05: rate-limit calculation endpoint (5 req/min per IP, burst 3)
    location /calc {
        limit_req        zone=tnm_calc burst=3 nodelay;
        limit_req_status 429;
        proxy_pass          http://127.0.0.1:${FLASK_PORT}/calc;
        proxy_set_header    Host              \$host;
        proxy_set_header    X-Real-IP         \$remote_addr;
        proxy_set_header    X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto \$scheme;
        proxy_read_timeout  300;
        proxy_buffering     off;
    }

    # SEC-05: rate-limit lab test runner (1 req/min per IP — spawns subprocess)
    location /lab/run-tests {
        limit_req        zone=tnm_lab burst=1 nodelay;
        limit_req_status 429;
        proxy_pass          http://127.0.0.1:${FLASK_PORT}/lab/run-tests;
        proxy_set_header    Host              \$host;
        proxy_set_header    X-Real-IP         \$remote_addr;
        proxy_read_timeout  300;
        proxy_buffering     off;
    }

    # Catch-all
    location / {
        proxy_pass          http://127.0.0.1:${FLASK_PORT};
        proxy_set_header    Host              \$host;
        proxy_set_header    X-Real-IP         \$remote_addr;
        proxy_set_header    X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto \$scheme;
        proxy_read_timeout  300;
        proxy_connect_timeout 60;
        proxy_send_timeout  300;
        # Disable buffering for streaming/large TN responses
        proxy_buffering     off;
    }
}
NGINX
ok "nginx config written"

# ── systemd service ───────────────────────────────────────────────────────────
SERVICE_FILE="/etc/systemd/system/calculator.service"
info "Writing systemd service → $SERVICE_FILE"

cat > "$SERVICE_FILE" <<UNIT
[Unit]
Description=Triangular Number Matrix (Gunicorn)
After=network.target

[Service]
User=${APP_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${VENV_DIR}/bin/gunicorn \\
    --workers 2 \\
    --bind 127.0.0.1:${FLASK_PORT} \\
    --timeout 120 \\
    --access-logfile - \\
    app:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT
ok "systemd service written"

# ── firewall ──────────────────────────────────────────────────────────────────
info "Configuring firewall"
if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
    ok "firewalld: opened ports 80 and 443"
else
    echo "  (firewalld not active — skipping; open ports 80/443 in Hostinger panel if needed)"
fi

# ── start services ────────────────────────────────────────────────────────────
info "Enabling and starting calculator service"
systemctl daemon-reload
systemctl enable --now calculator
ok "calculator service started"

info "Testing nginx config"
nginx -t

info "Enabling and starting nginx"
systemctl enable --now nginx
ok "nginx started"

# ── SSL certificate ───────────────────────────────────────────────────────────
info "Obtaining Let's Encrypt certificate for ${DOMAIN}"
certbot --nginx \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    -m "$EMAIL" \
    --redirect          # enforce HTTPS redirect
ok "SSL certificate issued and nginx reloaded by certbot"

# ── final status ──────────────────────────────────────────────────────────────
info "Status summary"
systemctl status calculator --no-pager -l || true
echo ""
systemctl status nginx     --no-pager -l || true
echo ""
ok "Setup complete! Visit https://${DOMAIN}"
echo ""
echo "Useful commands:"
echo "  journalctl -u calculator -f       # follow app logs"
echo "  systemctl restart calculator      # restart app"
echo "  certbot renew --dry-run           # test auto-renewal"
echo "  nginx -t && systemctl reload nginx # reload nginx after config changes"
