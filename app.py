from flask import Flask, request, Response, render_template
from calculator import ManualBigNumber, TriangulaNumberMatrix, ShortFormBigNumber
from werkzeug.exceptions import RequestEntityTooLarge
import os
import time
import json
from typing import List, Tuple

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 * 1024 * 1024
app.config['MAX_FORM_MEMORY_SIZE'] = 100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 * 1024 * 1024


from flask import Flask, render_template
import os
import logging

app = Flask(__name__)


# Path to the local folder
folder_path = 'static/numbers'

try:
    # Try to list the files in the folder
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")

    # Get the list of files in the folder
    file_names = os.listdir(folder_path)
    
    # Filter out directories, keep only files
    file_names = [file for file in file_names if os.path.isfile(os.path.join(folder_path, file))]
    if not file_names:
        raise ValueError(f"No files found in the folder '{folder_path}'.")

except FileNotFoundError as e:
    print(f"FileNotFoundError: {e}")
    file_names = []
except Exception as e:
    print(f"Unexpected error: {e}")
    file_names = []




@app.errorhandler(RequestEntityTooLarge)
def handle_large_request(e):
    print(e)
    return "File too large! Maximum allowed size is " + str(app.config.get('MAX_CONTENT_LENGTH')), 413

def calc_change(old, new):
    if old == 0:
        raise ValueError("Cannot calculate percent change from zero (division by zero).")
    return ((float(new) - float(old)) / float(old)) * 100

def read_file_content(filename):
    try:
        with open(filename, 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return f"Error: The file {filename} was not found."
    except Exception as e:
        return f"An error occurred: {e}"
    
def write_to_file(output_file: str, content: str) -> None:
    """Write `content` to `output_file`, overwriting if it already exists."""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

def load_windows_json(path: str) -> List[Tuple[int, int]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [tuple(pair) for pair in data]  # convert list-lists to list-tuples

def handle_big_number_math(requestType: str):
    result = None
    error = None
    num1 = ''
    num2 = ''
    operation = ''
    file_name = request.form.get('file_names', '')
    elapsed = None
    percent_change = float("0.0")
    tn_out_file="static/output/tn-files/tn-file.txt"
    file_load_time = 0
    if request.method == 'POST':
        num1 = request.form.get('num1', '').strip()
        num2 = request.form.get('num2', '').strip()
        operation = request.form.get('operation', '')
       
        try:
            start_time = time.perf_counter()
            if file_name != '':
                num1 = read_file_content('static/numbers/' + file_name)
                file_load_time = str(time.perf_counter() - start_time)
                print ("Loading file from: " + "static/numbers/" + file_name)
           
            if operation == 'add':
                a = ManualBigNumber(num1)
                b = ManualBigNumber(num2)
                result = a.add(b)
            elif operation == 'subtract':
                a = ManualBigNumber(num1)
                b = ManualBigNumber(num2)
                result = a.subtract(b)
            elif operation == 'multiply':
                a = ManualBigNumber(num1)
                b = ManualBigNumber(num2)
                result = a.multiply(b)
            elif operation == 'divide':
                a = ManualBigNumber(num1)
                b = ManualBigNumber(num2)
                result = a.divide(b)
            elif operation == 'tri_add':
                a = ManualBigNumber(num1)
                result = a.triangular_number_addition()
            elif operation == 'tri_formula':
                a = ManualBigNumber(num1)
                result = a.triangular_number_formula()
            elif operation == 'tri_div_simpy_formula':
                a = ManualBigNumber(num1)
                result = a.triangular_number_sympi_division(num1)
                print ("rep digit calculation complete using n(n+1)/2: " + str(time.perf_counter() - start_time ));
                b = TriangulaNumberMatrix('1')
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result              
            elif operation == 'tri_div_gmpy2_formula':
                a = ManualBigNumber(num1)
                print ("loaded file for gmpy2 n(n+1)/2: " + file_load_time)

                result = a.triangular_number_gmpy2_division(num1)
                write_to_file(tn_out_file + "." + operation + ".txt", str(result))
                write_to_file(
                    "static/output/stat-files/stat-file.txt.tri_div_pmpy2_formula.txt", 
                    "{repdigit: " + str(num1[0]) + 
                    ", repdigit_length: " + str(len(num1)) + 
                    ", generated_chars: " + str(len(result)) + 
                    ", file_load_time: " + str(file_load_time) +  
                    ", total_elapsed: " + str(time.perf_counter() - start_time) + "}"
                )

                print ("rep digit calculation complete using n(n+1)/2: " + str(time.perf_counter() - start_time ))
                b = TriangulaNumberMatrix('1')
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result
            elif operation == 'tri_matrix':
                b = TriangulaNumberMatrix('1')
                print ("loaded file Triangular Numbers Matrix: " + file_load_time)

                result = b.repDigitTriangularNumber(num1)   
                write_to_file(tn_out_file + "." + operation + "_standard.txt", str(result))
                write_to_file("static/output/stat-files/stat-file.txt.tri_matrix_standard.txt", "{repdigit: " + str(num1[0]) + ", repdigit_length: " + str(len(num1)) + ", generated_chars: " + str(len(result)) + ", file_load_time: " + str(file_load_time) + ", total_elapsed: " + str(time.perf_counter() - start_time) + "}")
                print ("rep digit calculation complete using Matrix: " + str(time.perf_counter() - start_time ))
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result
            elif operation == 'tri_matrix_stream':
                b = TriangulaNumberMatrix('1')
                print ("loaded file Triangular Numbers Matrix Stream: " + file_load_time)

                windows_from_file = load_windows_json("static/configs/windows.json")
                windows = [(int(a), int(b)) for a, b in windows_from_file]
                result = b.repDigitTriangularNumberStream(num1, out_path=tn_out_file +"." +operation+".txt", extract_ranges=windows, collect_result=False)  

                # Write files
                write_to_file("static/output/we-files/we-file.txt.tri_matrix_stream.txt", str(result["extracted"]))
                write_to_file("static/output/stat-files/stat-file.txt.tri_matrix_stream.txt", "{repdigit: " + str(result["repdigit"]) + ", repdigit_length: " + str(result["repdigit_length"]) + ", generated_chars: " + str(result["generated_chars"]) + ", file_load_time: " + file_load_time + ", elapsed_seconds: " + str(result["elapsed_seconds"]) + ", total_elapsed: " + str(time.perf_counter() - start_time ) +"}") 

                print ("rep digit calculation complete using Matrix Streaming: " + str(time.perf_counter() - start_time ));
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result
            elif operation == 'tri_matrix_memory':
                b = TriangulaNumberMatrix('1')
                print ("loaded file Triangular Numbers Matrix Memory: " + file_load_time)
                # No results collected No windows extracted
                  #result = b.repDigitTriangularNumberMemory(num1, chunk_chars=8_388_608, extract_ranges=None, collect_result=False)
                # Just for verification purposes prints the whole pattern
                  #result = b.repDigitTriangularNumberMemory(num1, collect_result=True)
                  #result = result["result"]
                windows_from_file = load_windows_json("static/configs/windows.json")
                windows = [(int(a), int(b)) for a, b in windows_from_file]
                result = b.repDigitTriangularNumberMemory( num1, extract_ranges=windows, collect_result=False) 
                #result = b.repDigitTriangularNumberMemory( num1, extract_ranges=windows, collect_result=True) 

                # Write files
                write_to_file("static/output/tn-files/tn-file.txt.tri_matrix_memory.txt", str(result.get("result","")))
                write_to_file("static/output/we-files/we-file.txt.tri_matrix_memory.txt", str(result["extracted"]))
                write_to_file("static/output/stat-files/stat-file.txt.tri_matrix_memory.txt", "{repdigit: " + str(result["repdigit"]) + ", repdigit_length: " + str(result["repdigit_length"]) + ", generated_chars: " + str(result["generated_chars"]) + ", file_load_time: " + file_load_time +  ", elapsed_seconds: " + str(result["elapsed_seconds"]) + ", total_elapsed: " + str(time.perf_counter() - start_time ) +"}") 

                print ("rep digit calculation complete using Matrix Memory: " + time.perf_counter() - start_time );
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result
            elif operation == 'tri_matrix_random':
                b = TriangulaNumberMatrix('1')
                print ("loaded file Triangular Numbers Matrix Random: " + file_load_time)

                # No results collected No windows extracted
                  #result = b.repDigitTriangularNumberMemory(num1, chunk_chars=8_388_608, extract_ranges=None, collect_result=False)
                # Just for verification purposes prints the whole pattern
                  #result = b.repDigitTriangularNumberMemory(num1, collect_result=True)
                  #result = result["result"]
                
                windows_from_file = load_windows_json("static/configs/windows.json")
                windows = [(int(a), int(b)) for a, b in windows_from_file]
                sf = ShortFormBigNumber.from_ops(num1)
               

                result = b.repDigitTriangularNumberRandomAccess(sf, extract_ranges=windows, collect_result=True, compressed_tn_result=False)
                #result = b.repDigitTriangularNumberRandomAccess(sf, extract_ranges=windows, collect_result=True, compressed_tn_result=False)

                # Write files
                write_to_file("static/output/tn-files/tn-file.txt.tri_matrix_random.txt", str(result.get("result",result.get("compressed"))))
                write_to_file("static/output/we-files/we-file.txt.tri_matrix_random.txt", str(result["extracted"]))
                write_to_file("static/output/stat-files/stat-file.txt.tri_matrix_random.txt", "{repdigit: " + str(result["repdigit"]) + ", repdigit_length: " + str(result["l"]) + ", file_load_time: " + file_load_time +  ", elapsed_seconds: " + str(result["elapsed_seconds"]) + ", total_elapsed: " + str(time.perf_counter() - start_time ) +"}")

                # just triangular number, that's in 'result' for verification
                result = result.get("result",result.get("compressed"))
                

                print ("rep digit calculation complete using Matrix Memory: " + str(time.perf_counter() - start_time ));
                result = b.increment_by_gmpy_count(num1, result, num2) if num2 not in (None, "", " ") else result
            else:   
                error = 'Unsupported operation.'
                
            #print(request.form.to_dict())
            old_elapsed = request.form.get('elapsed')
            elapsed = time.perf_counter() - start_time 
            print ("Operation complete, elapsed time: " + str(elapsed))
            percent_change = calc_change(old_elapsed, elapsed)     
        except Exception as e:
            error = str(e)

    if requestType == "API":
        print ("operation: " + operation)
        #if operation != "tri_matrix_stream" and operation != "tri_matrix_memory" and operation != "tri_matrix_random": 
        #    write_to_file(tn_out_file + "." + operation + ".txt", str(result))
        return Response("Elapsed: "+ str(elapsed) + " seconds. ", status=200, mimetype='text/plain') 
                   

    return render_template(
        'index.html',
        result=result,
        error=error,
        num1=num1,
        num2=num2,
        selected_operation=operation,
        elapsed=elapsed,
        elapsed_display=elapsed,
        percent_change=percent_change,
        file_names=file_names
    )

@app.route('/', methods=['GET', 'POST'])
def index():
    return handle_big_number_math('WEB')

@app.route('/rep-digit-math', methods=['GET', 'POST'])
def rep_digit_math():
    return handle_big_number_math("API")

if __name__ == '__main__':
    app.run(debug=True)
