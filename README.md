
# Framework battle

**Specs**
- Timeout: 10s
- Concurrency: 1 thread only

| Framework & Route    | Requests Per Second (RPS) | Avg Latency (ms) | p99 Latency (ms) | Errors |
| -------------------- | ------------------------- | ---------------- | ---------------- | ------ |
| **quickAPI static**  | 7,334.91                  | 0.01             | 0                | 0      |
| **quickAPI dynamic** | 2,314.10                  | 0.01             | 0                | 0      |
| **FastAPI static**   | 1,310.37                  | 3,880.95         | 4,900            | 6,870  |
| **FastAPI dynamic**  | 890.40                    | 1.01             | 1                | 0      |
| **Flask static**     | 2,430.82                  | 3,225.14         | 5,708            | 2,670  |
| **Flask dynamic**    | 2,569.37                  | 2,737.63         | 5,450            | 0      |