import os
from typing import Tuple
from quickapi import Route
def StaticFiles(directory:str) -> Route:
    abs_dir = os.path.abspath(os.path.join(os.getcwd(),directory))

    def file_handler(req,filename:str):
        filename = filename or "index.html"
        safe_path = os.path.abspath(os.path.join(abs_dir,filename.lstrip('/')))
        if not safe_path.startswith(abs_dir) or not os.path.isfile(safe_path):
            return 404, (f"File Not Found {filename}".encode('utf-8'),'text/plain')

        _,ext = os.path.splitext(safe_path)
        ext = ext.lstrip('.').lower()
        mime_types = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 
                      'js': 'text/javascript', 'css': 'text/css','html':'text/html'}
        content_type = mime_types.get(ext,'application/octet-stream')
        with open(safe_path,'rb') as f: 
            return 200, (f.read(),content_type)
        
    return Route(file_handler,lambda d: d)