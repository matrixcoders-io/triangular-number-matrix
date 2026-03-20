#!/bin/bash

# Check if an argument was provided
if [ -z "$1" ]; then
    echo "Usage: $0 <reference_file>"
    exit 1
fi

REF_FILE="$1"
FOLDER=$(dirname "$REF_FILE")

# Ensure the reference file exists
if [ ! -f "$REF_FILE" ]; then
    echo "Error: Reference file '$REF_FILE' not found."
    exit 1
fi

# Print reference file info first
REF_SIZE=$(du -h "$REF_FILE" | cut -f1)
echo "Reference File: $REF_FILE ($REF_SIZE)"
echo "--------------------------------------------------"

for FILE in "$FOLDER"/*; do
    # Skip if it's a directory or the reference file itself
    [[ -d "$FILE" ]] && continue
    [[ "$FILE" == "$REF_FILE" ]] && continue

    # Get individual file size
    FILE_SIZE=$(du -h "$FILE" | cut -f1)

    # Fast binary comparison
    if ! cmp -s "$REF_FILE" "$FILE"; then
        echo "[DIFF FOUND] $FILE (Size: $FILE_SIZE)"
        
        # Extract first 200 and last 200 bytes
        # Using -c (bytes) is essential for fast one-liner handling
        START=$(head -c 200 "$FILE")
        END=$(tail -c 200 "$FILE")

        echo "  Start (200b): $START"
        echo "  End   (200b): $END"
        echo "--------------------------------------------------"
    else
        echo "[MATCH]      $FILE (Size: $FILE_SIZE)"
    fi
done

echo "Comparison complete."