import subprocess
import time
import os
import json
import pprint
import csv

# Define test matrix configurations
test_targets = [
    {"name": "quickAPI", "port": 8080, "cmd": ["python", "server-quickapi.py"]},
    {"name": "FastAPI",  "port": 8081, "cmd": ["python", "server-fastapi.py"]},
    {"name": "Flask",    "port": 8082, "cmd": ["python", "server-flask.py"]}
]

CONCURRENCY = "1"
DURATION    = "120s"

def extract_metrics(json_filepath):
    with open(json_filepath, 'r') as f:
        data = json.load(f)
        
    return {
        "rps":       data['requests']['average'],
        "avg_lat":   data['latency']['average'],
        "p99_lat":   data['latency']['p99'],
        "errors":    data['errors'] + data['non2xx']
    }

def execute_autocannon(port, path, output_filename):
    url = f"http://127.0.0.1:{port}{path}"
    # print(f"Executing: autocannon -c {CONCURRENCY} -d {DURATION} {url}")
    cmd = ["autocannon", "-c", CONCURRENCY, "-d", DURATION, url, "--json"]
    with open(f'metrics/{output_filename}', "w") as f:
        subprocess.run(cmd, stdout=f, stderr=subprocess.DEVNULL)

def test():
    for target in test_targets:
        print(f"Launching Benchmark Phase: {target['name']}")
        proc = subprocess.Popen(target['cmd'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

        try:
            print(f" [A] Testing Static Route No. 500...")
            execute_autocannon(target["port"], "/api/static/route-500", 
                            f"{target['name'].lower()}_static.json")
            
            print(f" [B] Testing Dynamic Route No. 500...")
            execute_autocannon(target["port"], "/api/dynamic/route-500/123", 
                            f"{target['name'].lower()}_dynamic.json")
            
        finally:
            proc.terminate()
            proc.wait()
            time.sleep(1.5)

def report():
    results = {}
    for target in test_targets:
        name = target["name"].lower()
        results[name+'_static']  = extract_metrics(f'metrics/{name}_static.json')
        results[name+'_dynamic'] = extract_metrics(f'metrics/{name}_dynamic.json')
    
    f = open('metrics/metrics.csv','w')
    csv_writer = csv.writer(f)
    csv_writer.writerow(['Name','RPS',"AVG_LAT","P99_LAT","ERRORS"])
    for key,val in results.items():
        csv_writer.writerow([key,*list(val.values())])
        print(key,val)

if __name__ == '__main__':
    test()
    report()
