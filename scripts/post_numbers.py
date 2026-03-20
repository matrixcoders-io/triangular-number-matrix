import requests
import sys
import os

def main():
    if len(sys.argv) != 3:
        print("Usage: python post_numbers.py <file_path> <operation>")
        sys.exit(1)

    file_path = sys.argv[1]
    operation = sys.argv[2]  # <-- NEW: command line arg #2 after filename

    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    url = "http://127.0.0.1:5000/rep-digit-math"

    data = {
        'num1': '0',
        # 'num1': file_content,  # uncomment if you actually want to send file content
        # operations: tri_matrix, tri_matrix_stream, tri_matrix_memory, tri_matrix_random, tri_div_gmpy2_formula, tri_div_simpy_formula
        'operation': operation,  
        'num2': '0',
        'file_names': os.path.basename(file_path)
    }

    response = requests.post(url, data=data)

    print("Status code:", response.status_code)
    # print("Response text:", response.text)

if __name__ == "__main__":
    main()