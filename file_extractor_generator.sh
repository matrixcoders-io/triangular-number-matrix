#!/bin/bash

# Check if all 3 parameters are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <input_file> <output_file> <fraction_denominator>"
    echo "Example: $0 data.txt output.txt 5 (to extract 1/5 of data.txt)"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="$2"
DENOMINATOR="$3"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found."
    exit 1
fi

# 1. Get the total file size in bytes (macOS specific)
TOTAL_BYTES=$(stat -f%z "$INPUT_FILE")

# 2. Calculate the size of the portion
# Bash arithmetic handles integers, so this will round down
EXTRACT_SIZE=$(( TOTAL_BYTES / DENOMINATOR ))

if [ "$EXTRACT_SIZE" -le 0 ]; then
    echo "Error: Calculated extract size is 0 bytes. Check your fraction."
    exit 1
fi

# 3. Extract the data using 'head'
# -c specifies the exact number of bytes to copy
head -c "$EXTRACT_SIZE" "$INPUT_FILE" > "$OUTPUT_FILE"

echo "Success: Extracted $EXTRACT_SIZE bytes (1/$DENOMINATOR of $TOTAL_BYTES) to $OUTPUT_FILE."
