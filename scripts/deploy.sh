#!/bin/bash
# =============================================================================
# deploy.sh — pull latest code from GitHub and restart the calculator
# Usage:  sudo bash scripts/deploy.sh
# =============================================================================

APP_DIR="/home/matrixcoders/git/triangular-number-matrix"
BACKUP_BASE="/home/matrixcoders/git"
SERVICE="calculator"
WRITE_DIRS=("static/output" "static/numbers")   # dirs matrixcoder must own

[[ $EUID -eq 0 ]] || { echo "Run as root: sudo bash $0"; exit 1; }

echo ""
echo "======================================================"
echo " Deploy — Triangular Number Matrix"
echo "======================================================"
echo ""

# 1. Stop Flask
echo "[1/5] Stopping $SERVICE..."
systemctl stop $SERVICE || true
echo "      stopped"

# 2. Incremental backup — triangular-number-matrix-1, -2, -3 ...
echo "[2/5] Backing up current code..."
N=1
while [[ -d "$BACKUP_BASE/triangular-number-matrix-$N" ]]; do N=$((N+1)); done
BACKUP_DIR="$BACKUP_BASE/triangular-number-matrix-$N"
cp -r "$APP_DIR" "$BACKUP_DIR"
echo "      backed up → $BACKUP_DIR"
echo "      existing backups:"
ls -d "$BACKUP_BASE"/triangular-number-matrix-* 2>/dev/null | sort -V | sed 's/^/        /'

# 3. Pull latest from GitHub
echo "[3/5] Pulling from GitHub..."
cd "$APP_DIR"
git fetch origin
git status
git pull origin "$(git rev-parse --abbrev-ref HEAD)"
echo ""
echo "      recent commits:"
git log --oneline -5 | sed 's/^/        /'
echo ""

# Install any new dependencies
echo "      checking pip dependencies..."
pip3 install -q -r requirements.txt \
    && echo "      pip OK" \
    || echo "      WARNING: pip install failed — check requirements.txt"

# 4. Re-apply write permissions (git pull as root can reset ownership)
echo "[4/5] Fixing permissions for matrixcoder..."
for dir in "${WRITE_DIRS[@]}"; do
    if [[ -d "$APP_DIR/$dir" ]]; then
        chown -R matrixcoder:matrixcoder "$APP_DIR/$dir"
        echo "      chown matrixcoder → $dir"
    fi
done

# 5. Start Flask
echo "[5/5] Starting $SERVICE..."
systemctl start $SERVICE
sleep 3
systemctl is-active --quiet $SERVICE \
    && echo "      $SERVICE: running ✓" \
    || echo "      WARNING: $SERVICE not running — check: journalctl -u $SERVICE -n 30 --no-pager"

echo ""
echo "======================================================"
echo " Done."
echo "  url      : https://matrixcoders.io/tnm-calculator"
echo "  logs     : journalctl -u $SERVICE -f"
echo "  rollback : systemctl stop $SERVICE"
echo "             mv $APP_DIR ${APP_DIR}.broken"
echo "             mv $BACKUP_DIR $APP_DIR"
echo "             systemctl start $SERVICE"
echo "======================================================"
echo ""
