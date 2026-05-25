from quickapi import quickAPI,Request,RouterHandler,HTTPServer
from quickapi.static import StaticFiles

# app test
app = quickAPI()
app.mount(url_prefix='/',sub_app=StaticFiles(directory='./test_data'))

@app.get('/api/v1/users/{user_id}/posts/{post_id}')
def get_post(req:Request, user_id:str, post_id:str):
    return 200, {"msg":f"post content for user {user_id} post_id {post_id}"}

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
        print('close server')
        server.server_close()