import argparse
import os
import random
import time

# python benchmark_catalog_read.py my_huge_catalog_file.txt --index 300-5000000 --length 100-200 --max_queries 10000

def run_benchmark(filename, index_range, length_range, max_queries=10000, print_data=False):
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return

    # Parse ranges: "300-5000" -> [300, 5000]
    idx_min, idx_max = map(int, index_range.split('-'))
    len_min, len_max = map(int, length_range.split('-'))
    
    total_bytes_read = 0
    start_time = time.perf_counter()

    print(f"Starting benchmark: {max_queries} random queries...")

    with open(filename, 'rb') as f:
        for i in range(max_queries):
            current_idx = random.randint(idx_min, idx_max)
            current_len = random.randint(len_min, len_max)
            
            f.seek(current_idx)
            data = f.read(current_len)
            
            # Now 'i' is defined and will work
            if print_data:
                print(f"Query {i+1} | Index {current_idx}: {repr(data)}", flush=True)
            
            total_bytes_read += len(data)

    end_time = time.perf_counter()
    duration = end_time - start_time

    print("\n" + "="*30)
    print(f"BENCHMARK RESULTS")
    print(f"="*30)
    print(f"Total Queries:    {max_queries:,}")
    print(f"Total Time:       {duration:.4f} seconds")
    print(f"Total Bytes:      {total_bytes_read:,} bytes")
    print(f"Avg Speed:        {max_queries / duration:.2f} queries/sec")
    print(f"Bytes/Sec:        {total_bytes_read / duration:.2f} B/s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="Path to large file")
    parser.add_argument("--index", default="300-5000", help="Range of indices (e.g. 300-5000)")
    parser.add_argument("--length", default="100-200", help="Range of lengths (e.g. 100-200)")
    parser.add_argument("--max_queries", type=int, default=10000, help="Total queries to run")
    parser.add_argument("--print_data", action="store_true", help="Include this flag to print data")
    args = parser.parse_args()
    
    run_benchmark(args.filename, args.index, args.length, args.max_queries, args.print_data)
