#!/bin/bash
# =============================================================================
# build_infra.sh — Provision a fresh CentOS/RHEL server for the calculator
#
# Usage:
#   1. Edit the config vars below
#   2. Copy this file to the server (scp or curl raw GitHub URL)
#   3. sudo bash build_infra.sh
#   4. Point DNS A record → server IP
#   5. sudo bash APP_DIR/scripts/setup_https.sh
#   6. Future updates: sudo bash APP_DIR/scripts/deploy.sh
# =============================================================================

# =============================================================================
# FILL THESE IN BEFORE RUNNING
# =============================================================================
DOMAIN="matrixcoders.io"
GITHUB_REPO="https://github.com/OWNER/triangular-number-matrix.git"
BRANCH="main"
APP_DIR="/home/matrixcoders/git/triangular-number-matrix"
APP_USER="matrixcoder"
APP_USER_HOME="/home/matrixcoders"
FLASK_PORT=5000
# =============================================================================

echo ""
echo "======================================================"
echo " build_infra.sh — Triangular Number Matrix"
echo "======================================================"
echo ""

# Hard exit: must be root
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Run as root:  sudo bash $0"
    exit 1
fi

# Hard exit: GITHUB_REPO must be filled in
if [[ "$GITHUB_REPO" == *"OWNER"* ]]; then
    echo "ERROR: Set GITHUB_REPO at the top of this script (replace OWNER with your GitHub username)."
    exit 1
fi

echo "Config:"
echo "  DOMAIN      : $DOMAIN"
echo "  GITHUB_REPO : $GITHUB_REPO"
echo "  BRANCH      : $BRANCH"
echo "  APP_DIR     : $APP_DIR"
echo "  APP_USER    : $APP_USER"
echo "  FLASK_PORT  : $FLASK_PORT"
echo "  Python      : $(python3 --version 2>&1 || echo 'not found — will install')"
echo ""

# ── [1/8] packages ─────────────────────────────────────────────────────────────
echo "[1/8] Installing packages..."
dnf install -y epel-release \
    && echo "      epel-release: OK" \
    || echo "      WARNING: epel-release install had errors — continuing"

dnf install -y nginx git python3 python3-pip \
    && echo "      nginx git python3 python3-pip: OK" \
    || echo "      WARNING: some packages may not have installed — check output above"

# ── [2/8] service account ──────────────────────────────────────────────────────
echo "[2/8] Creating service account ($APP_USER)..."
if id "$APP_USER" &>/dev/null; then
    echo "      $APP_USER already exists — skipping"
else
    useradd \
        --home-dir "$APP_USER_HOME" \
        --no-create-home \
        --shell /sbin/nologin \
        "$APP_USER" \
        && echo "      $APP_USER created (home=$APP_USER_HOME, shell=/sbin/nologin)" \
        || echo "      WARNING: useradd failed — service may not start as $APP_USER"
fi

# ── [3/8] clone repo ───────────────────────────────────────────────────────────
echo "[3/8] Cloning repo..."
PARENT_DIR="$(dirname "$APP_DIR")"
mkdir -p "$PARENT_DIR"

if [[ -d "$APP_DIR" ]]; then
    echo "      WARNING: $APP_DIR already exists — skipping clone"
    echo "               If you want a fresh clone: rm -rf $APP_DIR and re-run"
else
    git clone --branch "$BRANCH" "$GITHUB_REPO" "$APP_DIR" \
        && echo "      cloned ($BRANCH) → $APP_DIR" \
        || echo "      WARNING: git clone failed — check GITHUB_REPO and BRANCH, and that git is installed"
fi

# ── [4/8] Python dependencies ──────────────────────────────────────────────────
echo "[4/8] Installing Python dependencies..."
if [[ -f "$APP_DIR/requirements.txt" ]]; then
    pip3 install -q -r "$APP_DIR/requirements.txt" \
        && echo "      pip3: OK" \
        || echo "      WARNING: pip3 install had errors — check requirements.txt"
else
    echo "      WARNING: $APP_DIR/requirements.txt not found — skipping pip install"
    echo "               (clone may have failed in step 3)"
fi

# ── [5/8] output directory ownership ──────────────────────────────────────────
echo "[5/8] Setting up output directories..."
mkdir -p "$APP_DIR/static/output/stat-files" \
         "$APP_DIR/static/output/tn-files" \
         "$APP_DIR/static/output/we-files" \
         "$APP_DIR/static/numbers"

chown -R "$APP_USER:$APP_USER" "$APP_DIR/static/output" "$APP_DIR/static/numbers" \
    && echo "      chown $APP_USER → static/output + static/numbers" \
    || echo "      WARNING: chown failed — Flask may not be able to write output files"

# ── [6/8] nginx config ─────────────────────────────────────────────────────────
echo "[6/8] Writing nginx config (HTTP only)..."
cat > /etc/nginx/conf.d/calculator.conf <<NGINX
server {
    listen 80;
    server_name ${DOMAIN};

    # Redirect bare root to calculator
    location = / {
        return 302 /tnm-calculator/;
    }

    # Strip /tnm-calculator prefix, proxy to Flask, rewrite HTML paths back
    location /tnm-calculator/ {
        proxy_pass          http://127.0.0.1:${FLASK_PORT}/;
        proxy_set_header    Host              \$host;
        proxy_set_header    X-Real-IP         \$remote_addr;
        proxy_set_header    X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Proto \$scheme;
        proxy_read_timeout  300;
        proxy_buffering     off;

        # Disable compression so sub_filter can rewrite response bodies
        proxy_set_header    Accept-Encoding   "";

        # Rewrite absolute paths in HTML so browser stays under /tnm-calculator/
        sub_filter_once  off;
        sub_filter_types text/html;
        sub_filter 'action="/'   'action="/tnm-calculator/';
        sub_filter 'href="/'     'href="/tnm-calculator/';
        sub_filter 'src="/'      'src="/tnm-calculator/';
        sub_filter 'hx-get="/'  'hx-get="/tnm-calculator/';
        sub_filter 'hx-post="/' 'hx-post="/tnm-calculator/';
        sub_filter 'hx-put="/'  'hx-put="/tnm-calculator/';
    }
}
NGINX

nginx -t \
    && echo "      nginx config OK" \
    || echo "      WARNING: nginx config test failed — check /etc/nginx/conf.d/calculator.conf"

# ── [7/8] systemd service ──────────────────────────────────────────────────────
echo "[7/8] Writing systemd service..."
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

systemctl daemon-reload
systemctl enable calculator \
    && echo "      service enabled (using $PYTHON3_BIN)" \
    || echo "      WARNING: systemctl enable failed"

# ── [8/8] firewall + start services ───────────────────────────────────────────
echo "[8/8] Firewall + starting services..."

if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-service=http  || true
    firewall-cmd --permanent --add-service=https || true
    firewall-cmd --reload || true
    echo "      ports 80 + 443 opened in firewalld"
else
    echo "      firewalld not running — skipping (open ports 80 + 443 in your cloud panel if needed)"
fi

systemctl restart calculator || true
systemctl restart nginx      || true
sleep 3

CALC_STATUS=$(systemctl is-active calculator 2>/dev/null)
NGINX_STATUS=$(systemctl is-active nginx      2>/dev/null)

[[ "$CALC_STATUS" == "active" ]] \
    && echo "      calculator: running" \
    || echo "      WARNING: calculator not running — debug: journalctl -u calculator -n 30 --no-pager"

[[ "$NGINX_STATUS" == "active" ]] \
    && echo "      nginx: running" \
    || echo "      WARNING: nginx not running — debug: journalctl -u nginx -n 30 --no-pager"

# ── summary ────────────────────────────────────────────────────────────────────
echo ""
echo "======================================================"
echo " Result"
echo "======================================================"
echo "  calculator : $CALC_STATUS"
echo "  nginx      : $NGINX_STATUS"
echo "  url        : http://${DOMAIN}/tnm-calculator/   (HTTP only)"
echo ""
echo "  Next steps:"
echo "    1. Point DNS A record for $DOMAIN → $(curl -s ifconfig.me 2>/dev/null || echo '<server-ip>')"
echo "    2. sudo bash $APP_DIR/scripts/setup_https.sh"
echo "       (run after DNS propagates — adds HTTPS via Let's Encrypt)"
echo ""
echo "  Future code updates:"
echo "    sudo bash $APP_DIR/scripts/deploy.sh"
echo ""
echo "  Debug commands:"
echo "    journalctl -u calculator -n 50 --no-pager   # Flask logs"
echo "    journalctl -u calculator -f                  # Flask logs (live)"
echo "    journalctl -u nginx -n 50 --no-pager         # nginx logs"
echo "    systemctl restart calculator                  # restart Flask"
echo "    nginx -t && systemctl reload nginx            # test + reload nginx"
echo "======================================================"
echo ""
