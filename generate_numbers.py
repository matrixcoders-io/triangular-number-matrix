import sys
import os

def main():
    # Check if the correct number of arguments are provided
    if len(sys.argv) != 4:
        print("Usage: python script.py <input_file> <output_file> <number_of_times>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        number_of_times = int(sys.argv[3])
        if number_of_times < 0:
            raise ValueError
    except ValueError:
        print("Error: <number_of_times> must be a non-negative integer.")
        sys.exit(1)

    # Check if the input file exists
    if not os.path.isfile(input_file):
        print(f"Error: The input file '{input_file}' does not exist.")
        sys.exit(1)

    # Read the content of the input file
    with open(input_file, 'r', encoding='utf-8') as infile:
        content = infile.read()

    # Repeat the content as specified
    repeated_content = content * number_of_times

    # Write the repeated content to the output file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write(repeated_content)

    print(f"Content repeated {number_of_times} times and written to '{output_file}'.")

if __name__ == "__main__":
    main()
