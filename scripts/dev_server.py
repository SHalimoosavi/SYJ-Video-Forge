#!/usr/bin/env python3
"""Standard-library static server bound to loopback by default."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse, mimetypes
ROOT=Path(__file__).resolve().parents[1]
mimetypes.add_type("text/javascript",".js")
mimetypes.add_type("text/css",".css")
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
 def end_headers(self): self.send_header("X-Content-Type-Options","nosniff");super().end_headers()
def main():
 p=argparse.ArgumentParser();p.add_argument("--host",default="127.0.0.1");p.add_argument("--port",type=int,default=8000);a=p.parse_args()
 server=ThreadingHTTPServer((a.host,a.port),Handler);print(f"Serving {ROOT} at http://{a.host}:{a.port}/")
 try: server.serve_forever()
 except KeyboardInterrupt: pass
 finally: server.server_close()
if __name__=="__main__":main()
