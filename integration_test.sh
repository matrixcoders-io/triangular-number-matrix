#!/bin/bash

# Check if filename argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

BASE_FILENAME=$1
#OPERATIONS=("tri_matrix" "tri_matrix_stream" "tri_matrix_memory" "tri_matrix_random" "tri_div_gmpy2_formula")
OPERATIONS=("tri_matrix_stream")

echo "Starting integration tests..."
echo "--------------------------------------------"

for OP in "${OPERATIONS[@]}"; do
    # Logic to swap filename for tri_matrix_random
    if [ "$OP" == "tri_matrix_random" ]; then
        CURRENT_FILE="${BASE_FILENAME}-sf.txt"
    else
        CURRENT_FILE="$BASE_FILENAME"
    fi

    echo "Running operation: $OP using file: $CURRENT_FILE"
    
    python3 post_numbers.py "$CURRENT_FILE" "$OP"
    
    if [ $? -eq 0 ]; then
        echo "✅ $OP completed successfully."
    else
        echo "❌ $OP failed."
    fi
    echo "--------------------------------------------"
done

echo "Integration tests finished."
