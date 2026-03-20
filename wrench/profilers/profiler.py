import os
import sys
import subprocess

def profile_file(filename):
    result = subprocess.run(
        [sys.executable, "-m", "cProfile", "-s", "cumulative", filename],
        capture_output= True,
        text= True,
        cwd=os.path.dirname(os.path.abspath(filename))
    )
    return result.stdout

def parse_stats(raw_output):
    lines = raw_output.strip().split("\n")
    stats = []
    for line in lines[4:]:
        parts = line.split()
        if len(parts) >= 6:
            try:
                float(parts[1])  
                float(parts[3])  
                function = " ".join(parts[5:])
                if not function.startswith("{"):  
                    stats.append({
                        "ncalls": parts[0],
                        "tottime": parts[1],
                        "cumtime": parts[3],
                        "function": function
                    })
            except ValueError:
                continue
    return stats

def write_temp_file(code, original_filename):
    temp_file = original_filename.replace("py", "_wrench_temp.py")
    with open(temp_file, "w") as f:
        f.write(code)
    return temp_file

def delete_temp_file(temp_filename):
    if os.path.exists(temp_filename):
        os.remove(temp_filename)

