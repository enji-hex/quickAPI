import socket
from quickapi import quickAPI,Request,RouterHandler
from quickapi.static import StaticFiles
from http.server import HTTPServer,ThreadingHTTPServer

# app test
app = quickAPI()
# app.mount(url_prefix='/assets',sub_app=StaticFiles(directory='./public/'))

def make_handler(route_id:int):
    def handler(req,**kwargs):
        return 200,{"route_id":route_id,"status":"ok","params":kwargs}
    return handler

for i in range(1,501):
    path = f'/api/static/route-{i}'
    app.register("GET",path)(make_handler(i))

for i in range(1,501):
    path = f'/api/dynamic/route-{i}/{{id}}'
    app.register("GET",path)(make_handler(i))

@app.post('/api/v1/check')
def post_check(req:Request):
    print(f'rec',req.headers, req.content)
    return 200, {"status":"RUNNING"}


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0',8080), 
        lambda *args, **kwargs: RouterHandler(app,*args,**kwargs))
    try:
        print('server started')
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()