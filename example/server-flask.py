from flask import Flask, jsonify
import logging
import gunicorn.app.base

app = Flask(__name__)

# Mute Flask's standard logging out of fairness
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def make_flask_handler(route_id: int):
    def handler(**kwargs):
        return jsonify({"route_id": route_id, "status": "ok", "params": kwargs})
    return handler

# Seed 500 Static Routes
for i in range(1, 501):
    app.add_url_rule(f"/api/static/route-{i}", endpoint=f"static_{i}", view_func=make_flask_handler(i))

# Seed 500 Dynamic Routes
for i in range(1, 501):
    app.add_url_rule(f"/api/dynamic/route-{i}/<id>", endpoint=f"dynamic_{i}", view_func=make_flask_handler(i))

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        # Apply the dictionary options to Gunicorn's configuration engine
        config = {key: value for key, value in self.options.items() 
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

# 3. Execution Block
if __name__ == '__main__':
    # Define production configuration options
    options = {
        'bind': '0.0.0.0:8082',
        'workers': 1,           
        'threads': 1,           
        'keepalive': 5,         # 💡 Crucial! Forces Gunicorn to keep HTTP/1.1 connections alive
        'loglevel': 'warning'   # Suppresses request spam logs during the benchmark
    }
    StandaloneApplication(app, options).run()