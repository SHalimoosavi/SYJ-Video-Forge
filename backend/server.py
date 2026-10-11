"""Standard-library HTTP server for SYJ Video Forge."""
from __future__ import annotations
import argparse, json, mimetypes, os, re, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from .config import MAX_BODY_BYTES, cors_origins, validate_job_payload
from .jobs import JobManager
from .providers import ProviderError

ROOT=Path(__file__).resolve().parents[1]
class ForgeHTTPServer(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True
    def __init__(self,address,manager:JobManager,origins:tuple[str,...],serve_frontend:bool=False):
        super().__init__(address,ForgeHandler);self.manager=manager;self.allowed_origins=origins;self.serve_frontend=serve_frontend

class ForgeHandler(BaseHTTPRequestHandler):
    server:ForgeHTTPServer
    protocol_version="HTTP/1.1"
    def log_message(self,fmt,*args):
        # Request logs contain method/path/status only; never log prompts or bodies.
        sys.stderr.write("SYJ Video Forge: "+(fmt%args)+"\n")
    def _cors(self)->None:
        origin=self.headers.get("Origin")
        if origin and origin.rstrip("/") in self.server.allowed_origins:
            self.send_header("Access-Control-Allow-Origin",origin)
            self.send_header("Vary","Origin")
            self.send_header("Access-Control-Allow-Methods","GET, POST, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers","Content-Type, Range")
            self.send_header("Access-Control-Expose-Headers","Content-Length, Content-Range, Accept-Ranges")
            if self.headers.get("Access-Control-Request-Private-Network","").lower()=="true":self.send_header("Access-Control-Allow-Private-Network","true")
    def _headers(self,code:int,ctype:str="application/json",length:int=0,extra:dict[str,str]|None=None)->None:
        self.send_response(code);self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(length));self.send_header("X-Content-Type-Options","nosniff");self.send_header("Cache-Control","no-store");self._cors()
        for k,v in (extra or {}).items():self.send_header(k,v)
        self.end_headers()
    def _json(self,code:int,obj:dict)->None:
        data=json.dumps(obj,ensure_ascii=False,separators=(",",":")).encode("utf-8");self._headers(code,"application/json; charset=utf-8",len(data));self.wfile.write(data)
    def _body(self)->dict:
        raw=self.headers.get("Content-Length")
        if raw is None:raise ValueError("Content-Length is required")
        try:length=int(raw)
        except ValueError as exc:raise ValueError("Invalid Content-Length") from exc
        if length<0 or length>MAX_BODY_BYTES:raise OverflowError(f"Request body exceeds the {MAX_BODY_BYTES} byte limit")
        data=self.rfile.read(length)
        if len(data)!=length:raise ValueError("Request body ended early")
        try:obj=json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError,json.JSONDecodeError) as exc:raise ValueError("Request body must be valid UTF-8 JSON") from exc
        if not isinstance(obj,dict):raise ValueError("Request body must be a JSON object")
        return obj
    def do_OPTIONS(self):
        origin=self.headers.get("Origin")
        if origin and origin.rstrip("/") not in self.server.allowed_origins:self._json(403,{"error":"Origin is not allowed by CORS policy"});return
        self._headers(204,"text/plain",0,extra={"Access-Control-Max-Age":"600"})
    def do_GET(self):
        path=urlsplit(self.path).path
        try:
            if path=="/api/health":self._json(200,self.server.manager.health());return
            if path=="/api/capabilities":self._json(200,self.server.manager.capabilities());return
            match=re.fullmatch(r"/api/jobs/([0-9a-f]{32})",path)
            if match:self._json(200,self.server.manager.get(match.group(1)));return
            match=re.fullmatch(r"/api/jobs/([0-9a-f]{32})/result",path)
            if match:self._video(match.group(1));return
            if self.server.serve_frontend:self._static(path);return
            self._json(404,{"error":"Not found"})
        except KeyError:self._json(404,{"error":"Job not found"})
        except ValueError as exc:self._json(409,{"error":str(exc)})
        except (BrokenPipeError,ConnectionResetError):return
    def do_POST(self):
        path=urlsplit(self.path).path
        try:
            if path=="/api/jobs":
                payload=validate_job_payload(self._body());job=self.server.manager.create(payload);self._json(202,job);return
            match=re.fullmatch(r"/api/jobs/([0-9a-f]{32})/cancel",path)
            if match:
                # Empty body is optional for cancellation.
                self._json(200,self.server.manager.cancel(match.group(1)));return
            self._json(404,{"error":"Not found"})
        except OverflowError as exc:self._json(413,{"error":str(exc)})
        except (ValueError,UnicodeError) as exc:self._json(400,{"error":str(exc)})
        except ProviderError as exc:self._json(503,{"error":str(exc)})
        except KeyError:self._json(404,{"error":"Job not found"})
    def do_DELETE(self):
        match=re.fullmatch(r"/api/jobs/([0-9a-f]{32})",urlsplit(self.path).path)
        if not match:self._json(404,{"error":"Not found"});return
        try:self._json(200,self.server.manager.cancel(match.group(1)))
        except KeyError:self._json(404,{"error":"Job not found"})
    def _video(self,jid:str)->None:
        path=self.server.manager.result_path(jid);size=path.stat().st_size;range_header=self.headers.get("Range")
        try:selection=__import__("backend.media",fromlist=["parse_range"]).parse_range(range_header,size)
        except ValueError:
            self._headers(416,"application/json",0,{"Content-Range":f"bytes */{size}","Accept-Ranges":"bytes"});return
        start,end=(selection if selection is not None else (0,size-1));length=end-start+1;code=206 if selection is not None else 200
        self._headers(code,"video/mp4",length,{"Accept-Ranges":"bytes","Content-Range":f"bytes {start}-{end}/{size}"} if code==206 else {"Accept-Ranges":"bytes"})
        try:
            with path.open("rb") as f:
                f.seek(start);remaining=length
                while remaining:
                    chunk=f.read(min(64*1024,remaining))
                    if not chunk:break
                    self.wfile.write(chunk);remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError):return
    def _static(self,path:str)->None:
        requested=unquote(path).lstrip("/") or "index.html"
        if "\x00" in requested: self._json(400,{"error":"Invalid path"});return
        candidate=(ROOT/requested).resolve()
        if ROOT.resolve() not in candidate.parents and candidate!=ROOT.resolve():self._json(404,{"error":"Not found"});return
        if not candidate.is_file():self._json(404,{"error":"Not found"});return
        ctype=mimetypes.guess_type(candidate.name)[0] or "application/octet-stream";data=candidate.read_bytes();self._headers(200,ctype,len(data));self.wfile.write(data)

def make_server(host:str="127.0.0.1",port:int=8080,data_dir:str|Path="./data",origins:tuple[str,...]|None=None,serve_frontend:bool=False,ttl_seconds:int=86400,max_jobs:int=12,ffmpeg:str|None=None)->ForgeHTTPServer:
    manager=JobManager(data_dir,ttl_seconds,max_jobs,ffmpeg)
    try:return ForgeHTTPServer((host,port),manager,origins or cors_origins(),serve_frontend)
    except Exception:manager.close();raise

def main()->int:
    p=argparse.ArgumentParser(description="SYJ Video Forge local backend (test-pattern provider; not AI)")
    p.add_argument("--host",default="127.0.0.1",help="Bind address; non-loopback addresses require explicit --host and display a warning")
    p.add_argument("--port",type=int,default=8080);p.add_argument("--data-dir",default="./data");p.add_argument("--ttl-seconds",type=int,default=86400);p.add_argument("--max-jobs",type=int,default=12);p.add_argument("--cors-origins",default=None);p.add_argument("--serve-frontend",action="store_true");p.add_argument("--ffmpeg",default=None,help="Optional explicit ffmpeg executable path")
    a=p.parse_args()
    try:origins=cors_origins(a.cors_origins)
    except ValueError as exc:p.error(str(exc))
    if a.port<0 or a.port>65535:p.error("port must be between 0 and 65535")
    if a.host not in {"127.0.0.1","localhost","::1"}:print(f"WARNING: binding to non-loopback host {a.host!r} exposes this unauthenticated local service to reachable hosts. Use a firewall and explicit CORS allowlist.",file=sys.stderr)
    server=make_server(a.host,a.port,a.data_dir,origins,a.serve_frontend,a.ttl_seconds,a.max_jobs,a.ffmpeg)
    print(f"SYJ Video Forge backend listening at http://{a.host}:{server.server_address[1]}/ (provider: test-pattern; NOT AI generated)",flush=True)
    if a.serve_frontend:print("Frontend served on the same origin.",flush=True)
    try:server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:print("Stopping backend.",flush=True)
    finally:server.shutdown();server.server_close();server.manager.close()
    return 0
if __name__=="__main__":raise SystemExit(main())
