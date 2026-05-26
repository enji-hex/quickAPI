from fastapi import FastAPI
import uvicorn

app = FastAPI()

def make_fastapi_static_handler(route_id: int):
    def handler(): # No 'id' parameter here!
        return {"route_id": route_id, "status": "processed"}
    return handler

def make_fastapi_dynamic_handler(route_id: int):
    def handler(id: str):
        return {"route_id": route_id, "status": "processed", "id": id}
    return handler

# Seed 500 Static Routes
for i in range(1, 501):
    app.add_api_route(f"/api/static/route-{i}", 
                      make_fastapi_static_handler(i), methods=["GET"])

# Seed 500 Dynamic Routes
for i in range(1, 501):
    app.add_api_route(f"/api/dynamic/route-{i}/{{id}}", 
                      make_fastapi_dynamic_handler(i), methods=["GET"])

@app.get("/api/v1/check")
def check():
    return {"status": "ok"}

if __name__ == '__main__':
    uvicorn.run("server-fastapi:app", host="127.0.0.1", port=8081, workers=1, log_level="warning")