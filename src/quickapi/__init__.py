from http.server import BaseHTTPRequestHandler
import json
import os
import socket
from typing import Callable, Dict, Tuple,Optional

class Request:
    def __init__(self,headers:dict, content:bytes, params: dict):
        self.headers  = headers
        self.content  = content
        self.params   = params

class Route:
    def __init__(self,handler:Callable,encoder:Callable,path:str=""):
        self.handler     = handler
        self.encoder     = encoder
        self.segments    = [s for s in path.split('/') if s]
        self.base_prefix = path.split('{')[0] if '{filename*}' in path else None

class quickAPI:
    def __init__(self):
        self.routes: Dict[Tuple[str,str],Route] = {}
        self.status_routes: Dict[Tuple[str,str],Route] = {}

    def serialize(self,data) -> Tuple[bytes,str]:
        if isinstance(data,(dict,list)):
            return json.dumps(data,ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8'
        if isinstance(data,str):
            return data.encode('utf-8'),'text/html; charset=utf-8'
        return (data, 'application/octet-stream') if isinstance(data, bytes) else (str(data).encode('utf-8'), 'text/plain')

    def register(self,method:str,path:str):
        if (method,path) in self.routes or (method,path) in self.status_routes:
            raise ValueError(f"Route already defined {(method,path)}")
        def decorator(func:Callable):
            route = Route(func,self.serialize,path)
            if '{' in path and '}' in path: self.routes[(method,path)]        = route
            else:                           self.status_routes[(method,path)] = route
            return func
        return decorator

    def mount(self,url_prefix:str,sub_app:Route):
        """Direct path include in routes"""
        prefix = url_prefix.strip("/")
        path_pattern = f'/{prefix}/{{filename*}}' if prefix else "/{filename*}"
        if ('GET',path_pattern) in self.routes:
            raise KeyError(f'Mount already defined {path_pattern}')
        
        sub_app.base_prefix = path_pattern.split('{')[0]
        self.routes[('GET',path_pattern)] = sub_app

    def match_route(self,method:str,in_path:str) -> Tuple[Optional[Route],dict]:
        """Return meta for route, param dict"""
        
        # one line static route
        if (method,in_path) in self.status_routes: return self.status_routes[(method,in_path)],{} 
        in_segs = [s for s in in_path.split('/') if s]

        for (r_method,_),route in self.routes.items():
            if r_method != method: continue
            # file path
            if route.base_prefix is not None:
                if in_path.startswith(route.base_prefix):
                    filename = in_path[len(route.base_prefix):]
                    return route, {'filename':filename}
                continue

            # dynamic path
            r_segs = route.segments
            if len(r_segs) != len(in_segs): continue

            params,match_found = {},True
            for r_seg,i_seg in zip(r_segs,in_segs):
                if r_seg.startswith('{') and r_seg.endswith('}'):
                    params[r_seg[1:-1]] = i_seg
                elif r_seg != i_seg:
                    match_found = False; break
            if match_found: return route,params
        
        return None,{}
    
    def post(self,path:str): return self.register('POST',path)
    def get(self,path:str):  return self.register('GET',path)

class RouterHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def setup(self):
        self.disable_nagle_algorithm = True
        return super().setup()
    
    def __init__(self, app:quickAPI, *args, **kwargs):
        self.app = app
        super().__init__(*args,**kwargs)
    
    def log_message(self, format, *args): pass
        
    def handle_req(self,method:str):
        path = self.path.split('?')[0].split('#')[0]

        content_length = int(self.headers.get('Content-Length',0))
        content = self.rfile.read(content_length) if method != 'GET' and content_length > 0 else b""
        route,params =  self.app.match_route(method,path)
        if route is None: self.send_error(404,"Route not found"); return

        req  = Request(dict(self.headers),content,params)
        status_code,raw_resp = route.handler(req,**params)
        body, content_type   = route.encoder(raw_resp)

        self.send_response(status_code)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def do_GET(self): self.handle_req('GET')
    def do_POST(self): self.handle_req('POST')
