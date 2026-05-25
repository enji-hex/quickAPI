from http.server import HTTPServer,BaseHTTPRequestHandler
import json
import os
from typing import Callable, Dict, Tuple,Optional

class Request:
    def __init__(self,headers:dict, content:bytes, params: dict):
        self.headers  = headers
        self.content  = content
        self.params   = params

class Route:
    def __init__(self,handler:Callable,encoder:Callable):
        self.handler = handler
        self.encoder = encoder

class quickAPI:
    def __init__(self):
        self.routes: Dict[Tuple[str,str],Route] = {}

    def serialize(self,data) -> Tuple[bytes,str]:
        if isinstance(data,(dict,list)):
            return json.dumps(data,ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8'
        if isinstance(data,str):
            return data.encode('utf-8'),'text/html; charset=utf-8'
        return (data, 'application/octet-stream') if isinstance(data, bytes) else (str(data).encode('utf-8'), 'text/plain')

    def register(self,method:str,path:str):
        def decorator(func:Callable):
            if (method,path) in self.routes: raise ValueError(f"Route already defined {(method,path)}")
            self.routes[(method,path)] = Route(func,self.serialize)
            return func
        return decorator

    def mount(self,url_prefix:str,sub_app:Route):
        """Direct path include in routes"""
        prefix = url_prefix.strip("/")
        path_pattern = f'/{prefix}/{{filename*}}' if prefix else "/{filename*}"
        if ('GET',path_pattern) in self.routes:
            raise KeyError(f'Mount already defined {path_pattern}')
        self.routes[('GET',path_pattern)] = sub_app

    def match_route(self,method:str,in_path:str) -> Tuple[Optional[Route],dict]:
        """Return meta for route, param dict"""
        in_segs = [s for s in in_path.split('/') if s]
        static_fallback = None

        for (r_method,r_path),route in self.routes.items():
            if r_method != method: continue
            # static files
            if r_path.endswith('{filename*}'):
                base_prefix = r_path.split('{')[0]
                if in_path.startswith(base_prefix) or in_path == base_prefix.rstrip('/'):
                    filename = in_path[len(base_prefix):] if in_path.startswith(base_prefix) else ""
                    static_fallback =  route, {'filename':filename}
                continue

            # standard dynami path
            r_segs = [s for s in r_path.split('/') if s]
            if len(r_segs) != len(in_segs) : continue

            params,match_found = {},True
            for r_seg,i_seg in zip(r_segs,in_segs):
                if r_seg.startswith('{') and r_seg.endswith('}'):
                     params[r_seg[1:-1]] = i_seg
                elif r_seg != i_seg:
                    match_found = False; break
            if match_found: return route,params
        
        if static_fallback: return static_fallback
        return None,{}
    
    def post(self,path:str): return self.register('POST',path)
    def get(self,path:str):  return self.register('GET',path)

class RouterHandler(BaseHTTPRequestHandler):
    def __init__(self, app:quickAPI, *args, **kwargs):
        self.app = app
        super().__init__(*args,**kwargs)

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
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self): self.handle_req('GET')
    def do_POST(self): self.handle_req('POST')
