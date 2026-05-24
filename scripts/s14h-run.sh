#!/bin/bash
# Suite 14-H Test Runner — Custom + Precompiled Modes
# Usage:
#   bash scripts/s14h-run.sh low
#   bash scripts/s14h-run.sh medium
#   bash scripts/s14h-run.sh high
#   bash scripts/s14h-run.sh d=1,2,4 I=0,1066 L=407
#   bash scripts/s14h-run.sh d=1-9 I=1-100 L=1-2

set -e

PROJECT_DIR="/Users/matrixcoders/git/triangular-number-matrix"
PARSE_SCRIPT="$PROJECT_DIR/.claude/agents/s14h_parse.py"
AUDIT_SCRIPT="$PROJECT_DIR/.claude/agents/s14h_audit.js"
LOG_DIR="$PROJECT_DIR/tmp/tests/ui-tests"
PROFILES_DIR="$LOG_DIR/profiles"
PORT=5002

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$PROFILES_DIR"

TIMESTAMP=$(date +%Y-%m-%d-%H-%M-%S)
LOG_FILE="$LOG_DIR/s14h-$TIMESTAMP.log"

# Parse arguments — check if profile or custom
if [ "$1" = "low" ] || [ "$1" = "medium" ] || [ "$1" = "high" ]; then
  PROFILE="$1"
  if [ ! -f "$PROFILES_DIR/$PROFILE.txt" ]; then
    echo "ERROR: Profile file not found: $PROFILES_DIR/$PROFILE.txt" >&2
    exit 1
  fi
  ARGS=$(cat "$PROFILES_DIR/$PROFILE.txt")
  MODE="$PROFILE"
else
  ARGS="$*"
  MODE="custom"
fi

# Expand range/list notation: "1-5" → "1 2 3 4 5", "1,2,4" → "1 2 4"
expand_list() {
  local spec="$1"
  local result=""

  IFS=',' read -ra parts <<< "$spec"
  for part in "${parts[@]}"; do
    part=$(echo "$part" | xargs)  # trim whitespace
    if [[ "$part" =~ ^([0-9]+)-([0-9]+)$ ]]; then
      local start="${BASH_REMATCH[1]}"
      local end="${BASH_REMATCH[2]}"
      for ((i=start; i<=end; i++)); do
        result="$result $i"
      done
    else
      result="$result $part"
    fi
  done

  echo "$result" | xargs  # trim leading/trailing space
}

# Extract d=, I=, L= values (using python3 for macOS-compatible regex — grep -oP not available on macOS)
D_SPEC=$(python3 -c "import re,sys; m=re.search(r'd=(\S+)', sys.argv[1]); print(m.group(1) if m else '')" "$ARGS")
I_SPEC=$(python3 -c "import re,sys; m=re.search(r'I=(\S+)', sys.argv[1]); print(m.group(1) if m else '')" "$ARGS")
L_SPEC=$(python3 -c "import re,sys; m=re.search(r'L=(\S+)', sys.argv[1]); print(m.group(1) if m else '')" "$ARGS")

if [ -z "$D_SPEC" ] || [ -z "$I_SPEC" ] || [ -z "$L_SPEC" ]; then
  echo "ERROR: Missing d=, I=, or L= in spec: $ARGS" >&2
  exit 1
fi

D_LIST=$(expand_list "$D_SPEC")
I_LIST=$(expand_list "$I_SPEC")
L_LIST=$(expand_list "$L_SPEC")

# Count total ops
D_COUNT=$(echo "$D_LIST" | wc -w)
I_COUNT=$(echo "$I_LIST" | wc -w)
L_COUNT=$(echo "$L_LIST" | wc -w)
TOTAL=$((D_COUNT * I_COUNT * L_COUNT))

# Print header
{
  echo ""
  echo "Suite 14-H — Pyramid Visual-Reading Integrity Test"
  echo "Mode: $MODE ($TOTAL ops)"
  echo "d: $D_LIST"
  echo "I: $I_LIST"
  echo "L: $L_LIST"
  echo "Log: $LOG_FILE"
  echo ""
} | tee "$LOG_FILE"

# Check Flask server is running
if ! nc -z 127.0.0.1 $PORT 2>/dev/null; then
  echo "Flask server not running on port $PORT. Starting..." | tee -a "$LOG_FILE"
  cd "$PROJECT_DIR"
  python -m flask run --port $PORT --host 127.0.0.1 >/dev/null 2>&1 &
  SERVER_PID=$!
  sleep 2
  if ! nc -z 127.0.0.1 $PORT 2>/dev/null; then
    echo "ERROR: Could not start Flask server" >&2
    kill $SERVER_PID 2>/dev/null || true
    exit 1
  fi
  START_SERVER=1
else
  echo "Flask server already running on port $PORT" | tee -a "$LOG_FILE"
  START_SERVER=0
fi

# Clean old test files in /tmp/
rm -f /tmp/s14v_*.json /tmp/s14v_*.html 2>/dev/null || true

echo "Fetching and parsing $TOTAL ops (progress on terminal only)..."

# Fetch and parse each combination — parse progress goes to terminal only, NOT log
for D in $D_LIST; do
  for INC in $I_LIST; do
    for L in $L_LIST; do
      # Build input (D repeated L times)
      INPUT=$(python3 -c "print('$D'*$L,end='')")

      # Fetch HTML
      curl -s -X POST "http://127.0.0.1:$PORT/calc" \
        -F "num1=$INPUT" \
        -F "num2=$INC" \
        -F "operation=tri_matrix" \
        -F "file_names=" \
        -H "HX-Request: true" > "/tmp/s14v_d${D}_i${INC}_l${L}.html" 2>/dev/null

      # Parse HTML to JSON — stdout only (progress), NOT written to log
      python3 "$PARSE_SCRIPT" "$D" "$INC" "$L"
    done
  done
done

echo ""
echo "Running audit..."
echo ""

# Run audit and tee output
node "$AUDIT_SCRIPT" 2>&1 | tee -a "$LOG_FILE"

# Kill server if we started it
if [ "$START_SERVER" = "1" ]; then
  kill $SERVER_PID 2>/dev/null || true
  sleep 1
fi

# Print final path
echo "" | tee -a "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "Report saved: $LOG_FILE" | tee -a "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
