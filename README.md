
# quickAPI

quickAPI is a extremely lightweight, high-performnace backend framework. Initially built on top of Python's native [http.server](https://docs.python.org/3/library/http.server.html),
its decoupled, layered architecture allows the underlying core engine to be completely swapped out. Currently quickAPI supports only `HTTPServer` and `ThreadedHTTPServer` backends.

This project was inspired by the elegant developer-friendly design of FastAPI. The goal wasto build 
highly optimized version of that paradigm with absolute minimum of code footprint.

## Features:
- **Static Route Serving:** O(1) efficiency via direct hash-table lookups.
- **Dynamic Routes Serving:** O(n), complexity, searching sequentially across all registered routes.
- **Url Parameters Handling:** Inline path variable extraction (e.g. `/user/{id}`).
- **Automatic response encoding:** Out-of-the-box encoding for `dict/list/str` data types.
- **Folder mount:** O(1) efficiency where only one mount exists and it's defined as the first route.

## Constraints:
- **HTTP methods:** Supports GET and POST requests exclusively.
- **Mounting Restrictions:** Directory mounting must be bound to a non-root entry point. Mounting a folder directly to the root (`/`) will disrupt standard routing logic.
- **Concurrency:** Operates strictly in a single-threaded execution loop.

## Quickstart 

Designed with a sharp focus on Developer Experience (DX), quickAPI implements a clean, intuitive interface inspired by FastAPI. Below is quick example of functional web server handling dynamic routes alongside static directory mounting:

```python
app = quickAPI()
# mount public assets( or even frontend app like React)
app.mount(url_prefix='/assets',sub_app=StaticFiles(directory='./public/'))

@app.post('/api/user/{user_id}/post/{post_id}')
def post_check(req, user_id, post_id):
    # Path matching guarantees these variables exist as strings.
    # Simply check if they are numeric before casting.
    if user_id.isdigit() and post_id.isdigit():
        post_data: dict = db_request(int(user_id), int(post_id))
        return 200, post_data
    return 400, "Bad Request: Parameters must be numeric"

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0',8080), 
        lambda *args, **kwargs: RouterHandler(app,*args,**kwargs))
    server.serve_forever()
```

## Architecture & Components

```mermaid
flowchart LR
H(handle_func) --> Q(quickAPI) --> R(RouterHandler)
```

- `handle_func` - The user-defined handler function wrapped by a route decorator to process incoming requests.
- `quickAPI` - The core framework engine. It handles route registration, route matching, and the serialization of payloads returned by user functions.
- `RouterHandler` - The data entry point that directly receives incoming network requests and forwards them to the quickAPI engine.


### quickAPI Static File Serving (`quickapi[static]`)

A specialized companion module designed for directory mounting and static asset delivery. It provides a dedicated handler function that evaluates file routing using relative paths.

For example, given a mount prefix of `/static/`, a request to `/static/images/kitty.jpg` will resolve seamlessly to the relative path `images/kitty.jpg` inside your target asset directory.

### Codebase Footprint

The codebase is intentionally hyper-lean to prevent middleware bloat. 
Code size is calculated with stripped comments, docstrings, empty lines, and imports:
`grep -Ev '\s+#|"""|^\s*$|import|from'  ./src/quickapi/__init__.py | wc -l` \

- quickAPI core:   85LOC
- quickAPI static: 14LOC 


## Benchmarks

To ensure an honest, high-stress evaluation, 500 distinct routes were registered in each framework for both static and dynamic configurations.

Benchmarks were performed using the `autocannon` HTTP benchmarking tool using the following command:
`autocannon -c 1 -d <time>s <url>`


Every request was targeted directly at the last registered route to simulate maximum lookup stress:
- `/api/static/route-500`       - Static path lookup, requiring no parameter parsing.
- `/api/dynamic/route-500/{id}` - Dynamic path lookup, requiring parameter extraction.

Static routes could be checked without parameter parsing and checked by hash with O(1) complexity 
(quickAPI works this way), dynamic routes require parameter parsing, partial comparison and route rotation,
that leads O(n) complexity plus additional time for for each route comparison.

All tests was performed in single thread mode.

> ⚠️ While single-threaded testing limits FastAPI's native async design, it isolates and measures pure routing pipeline overhead.

### Duration: 10s

| Framework & Route    | Requests Per Second (RPS) | Avg Latency (ms) | p99 Latency (ms) | Errors |
| -------------------- | ------------------------- | ---------------- | ---------------- | ------ |
| **quickAPI static**  | 7,334.91                  | 0.01             | 0                | 0      |
| **quickAPI dynamic** | 2,314.10                  | 0.01             | 0                | 0      |
| **FastAPI static**   | 1,310.37                  | 3,880.95         | 4,900            | 6,870  |
| **FastAPI dynamic**  | 890.40                    | 1.01             | 1                | 0      |
| **Flask static**     | 2,430.82                  | 3,225.14         | 5,708            | 2,670  |
| **Flask dynamic**    | 2,569.37                  | 2,737.63         | 5,450            | 0      |

### Duration: 120s

| Framework & Route    | Requests Per Second (RPS) | Avg Latency (ms) | p99 Latency (ms) | Errors |
| -------------------- | ------------------------- | ---------------- | ---------------- | ------ |
| **quickAPI static**  | 6971.74                   | 0.01             | 0                | 0      |
| **quickAPI dynamic** | 2371.74                   | 0.01             | 0                | 0      |
| **FastAPI static**   | 1458.73                   | 6203.41          | 6579             | 9333   |
| **FastAPI dynamic**  | 934.85                    | 0.99             | 1                | 0      |
| **Flask static**     | 2090.86                   | 30202.54         | 67293            | 3537   |
| **Flask dynamic**    | 2056.32                   | 29612.91         | 66099            | 0      |


## Key Insights from testing

1. In short burst tests, Flask's basic static route slightly outperforme quickAPI's dynamic execution. However, during the 120-second test, Flask degraded significantly under queue pressure. quickAPI's dynamic parameter-matching route outpaced Flask's static path by over 13% (2,371.74 vs 2,090.86RPS).

2. Under sustained load, Flask and FastAPI accumulated socket queue backlogs, pushing average latency past 30 seconds and dropping thousands of connections. quickAPI maintained a flat 0.01ms baseline with zero errors.

3. quickAPI bypasses the serialization and validation layers built into FastAPI, processing dynamic routes at over 2.5x the throughput.

## Roadmap

- [ ] TLS v1.3 support
- [ ] Async runtime
