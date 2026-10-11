"""Threaded bounded job queue and sequential scene-to-video pipeline."""
from __future__ import annotations
import json, math, os, queue, shutil, subprocess, threading, time, uuid
from pathlib import Path
from typing import Any
from .config import safe_child
from .media import concatenate, extract_last_frame, ffmpeg_path, ffprobe_path
from .providers import ProviderError, VideoProvider, provider_registry

TERMINAL={"completed","failed","cancelled"}
class JobManager:
    def __init__(self,data_dir: str|Path="./data",ttl_seconds: int=86400,max_jobs: int=12,ffmpeg: str|None=None,providers: list[VideoProvider]|None=None,workers: int=1):
        self.data_dir=Path(data_dir).resolve();self.data_dir.mkdir(parents=True,exist_ok=True)
        self.ttl_seconds=max(1,int(ttl_seconds));self.max_jobs=max(1,int(max_jobs));self.ffmpeg=(str(Path(ffmpeg).resolve()) if Path(ffmpeg).is_file() else shutil.which(ffmpeg)) if ffmpeg is not None else ffmpeg_path()
        self.providers=providers if providers is not None else provider_registry(ffmpeg if ffmpeg is not None else self.ffmpeg);self.provider=self.providers[0]
        self._lock=threading.RLock();self._jobs:dict[str,dict[str,Any]]={};self._events:dict[str,threading.Event]={};self._queue:queue.Queue[str|None]=queue.Queue();self._closed=False
        self.cleanup();self._load_metadata()
        self._threads=[]
        for i in range(max(1,workers)):
            t=threading.Thread(target=self._worker,name=f"syj-video-worker-{i}",daemon=True);t.start();self._threads.append(t)
    def _job_dir(self,jid:str)->Path:
        if not isinstance(jid,str) or not __import__("re").fullmatch(r"[0-9a-f]{32}",jid):raise KeyError("Job not found")
        return safe_child(self.data_dir,jid)
    def _metadata_path(self,jid:str)->Path:return safe_child(self._job_dir(jid),"job.json")
    def _persist(self,jid:str)->None:
        job=self._jobs[jid];directory=self._job_dir(jid);directory.mkdir(parents=True,exist_ok=True)
        public={k:v for k,v in job.items() if not k.startswith("_") and k not in {"event","image_bytes"}}
        temp=self._metadata_path(jid).with_suffix(".json.tmp");temp.write_text(json.dumps(public,ensure_ascii=False),encoding="utf-8");os.replace(temp,self._metadata_path(jid))
    def _load_metadata(self)->None:
        now=time.time()
        for p in self.data_dir.glob("*/job.json"):
            try:
                j=json.loads(p.read_text(encoding="utf-8"));jid=j.get("id")
                if not isinstance(jid,str) or p.parent!=self._job_dir(jid):continue
                if now-float(j.get("created_at",now))>self.ttl_seconds:shutil.rmtree(p.parent,ignore_errors=True);continue
                if j.get("status") in {"queued","running"}:j.update(status="failed",error="Job interrupted by backend restart; submit it again.",updated_at=now,progress=0)
                self._jobs[jid]=j;self._events[jid]=threading.Event();self._persist(jid)
            except (OSError,ValueError,TypeError,KeyError):continue
    def cleanup(self)->None:
        now=time.time()
        if not self.data_dir.exists():return
        for p in self.data_dir.iterdir():
            if not p.is_dir():continue
            try:
                if now-p.stat().st_mtime>self.ttl_seconds:shutil.rmtree(p,ignore_errors=True)
            except OSError:pass
    def health(self)->dict[str,Any]:
        available,reason=self.provider.available()
        return {"ok":True,"ffmpeg":{"available":bool(self.ffmpeg and Path(self.ffmpeg).exists()),"path":self.ffmpeg,"message":"" if self.ffmpeg else "FFmpeg missing. Install FFmpeg and ensure ffmpeg is on PATH, then restart the backend."},"ffprobe":{"available":bool(ffprobe_path())},"providers":[{"name":p.name,"available":p.available()[0],"reason":p.available()[1],"kind":p.capabilities.kind} for p in self.providers]}
    def capabilities(self)->dict[str,Any]:
        available,reason=self.provider.available();c=self.provider.capabilities.as_dict()
        return {**c,"available":available,"reason":reason,"providers":[{"name":p.name,"available":p.available()[0],"kind":p.capabilities.kind,"reason":p.available()[1]} for p in self.providers],"durations":[5,10,15,30,60,120,300,600],"aspect_ratios":["16:9","9:16","1:1"],"kind":self.provider.capabilities.kind}
    def create(self,payload:dict[str,Any])->dict[str,Any]:
        with self._lock:
            self.cleanup()
            active=sum(j.get("status") not in TERMINAL for j in self._jobs.values())
            if active>=self.max_jobs:raise ValueError(f"Job limit reached ({self.max_jobs}); wait for a job to finish or expire.")
            available,reason=self.provider.available()
            if not available:raise ProviderError(reason)
            if payload["mode"]=="image" and not (self.provider.capabilities.image and self.provider.capabilities.supports_start_image):raise ValueError("Selected provider does not support image-to-video.")
            if payload["negativePrompt"] and not self.provider.capabilities.negative_prompt:raise ValueError("Selected provider does not support negative prompts.")
            jid=uuid.uuid4().hex;now=time.time();ev=threading.Event()
            scenes=payload.get("scenes") or max(1,math.ceil(payload["duration"]/payload["clip_seconds"]))
            if scenes>30:raise ValueError("A job may contain at most 30 scenes")
            lengths=[];remaining=payload["duration"]
            for _ in range(scenes):
                seconds=min(payload["clip_seconds"],remaining)
                if seconds<=0:break
                lengths.append(seconds);remaining-=seconds
            if remaining>0.0001:raise ValueError("scene count and clip_seconds do not cover the requested duration")
            job={"id":jid,"status":"queued","progress":0,"created_at":now,"updated_at":now,"prompt":payload["prompt"],"duration":sum(lengths),"scene_count":len(lengths),"scenes":[{"index":i+1,"duration":s,"progress":0,"status":"queued"} for i,s in enumerate(lengths)],"kind":self.provider.capabilities.kind,"provider":self.provider.name,"error":"","result_file":"","concat_mode":"","seed":payload.get("seed") or 0,"mode":payload["mode"],"_lengths":lengths}
            # Internal-only fields are not persisted as API fields.
            job["_lengths"]=lengths
            if payload.get("image") is not None:
                extension={"image/png":"png","image/jpeg":"jpg","image/webp":"webp"}[payload["image"]["mime"]]
                input_path=safe_child(self._job_dir(jid),"input-image."+extension)
                input_path.parent.mkdir(parents=True,exist_ok=True);input_path.write_bytes(payload["image"]["bytes"]);job["_initial_image"]=str(input_path)
            self._jobs[jid]=job;self._events[jid]=ev;self._persist(jid);self._queue.put(jid)
            return self.public(jid)
    def public(self,jid:str)->dict[str,Any]:
        with self._lock:
            j=self._jobs.get(jid)
            if not j:raise KeyError("Job not found")
            return {k:v for k,v in j.items() if not k.startswith("_") and k not in {"created_at","updated_at"}}|{"result_url":f"/api/jobs/{jid}/result" if j.get("status")=="completed" else None}
    def get(self,jid:str)->dict[str,Any]:return self.public(jid)
    def cancel(self,jid:str)->dict[str,Any]:
        with self._lock:
            if jid not in self._jobs:raise KeyError("Job not found")
            j=self._jobs[jid]
            if j["status"] not in TERMINAL:
                self._events[jid].set();j["status"]="cancelled";j["error"]="";j["updated_at"]=time.time();self._persist(jid)
            return self.public(jid)
    def result_path(self,jid:str)->Path:
        with self._lock:
            if jid not in self._jobs:raise KeyError("Job not found")
            j=self._jobs[jid]
            if j["status"]!="completed":raise ValueError("Job result is not ready")
            path=safe_child(self._job_dir(jid),"output.mp4")
            if not path.is_file():raise ValueError("Completed job has no result file")
            return path
    def _update(self,jid:str,**changes:Any)->None:
        with self._lock:
            if jid not in self._jobs:return
            if self._events[jid].is_set() and changes.get("status") not in {"cancelled"}:return
            self._jobs[jid].update(changes,updated_at=time.time());self._persist(jid)
    def _worker(self)->None:
        while True:
            jid=self._queue.get()
            try:
                if jid is None:return
                self._run(jid)
            finally:self._queue.task_done()
    def _run(self,jid:str)->None:
        with self._lock:
            job=self._jobs.get(jid)
            if not job or job["status"]=="cancelled":return
            ev=self._events[jid];job["status"]="running";job["updated_at"]=time.time();self._persist(jid)
        work=self._job_dir(jid);work.mkdir(parents=True,exist_ok=True);clips=[];last_frame=Path(job["_initial_image"]) if job.get("_initial_image") else None
        try:
            if not self.ffmpeg:raise ProviderError("FFmpeg is missing. Install FFmpeg and ensure ffmpeg is on PATH, then restart the backend.")
            lengths=job.get("_lengths") or [s["duration"] for s in job["scenes"]]
            for index,seconds in enumerate(lengths):
                if ev.is_set():raise ProviderError("Job cancelled")
                clip=safe_child(work,f"scene-{index+1:02d}.mp4")
                def cb(p:float,message:str,ix:int=index)->None:
                    if ev.is_set():return
                    with self._lock:
                        j=self._jobs[jid];j["scenes"][ix].update(progress=max(0,min(100,float(p))),status="running",message=message);j["progress"]=int((ix+max(0,min(100,float(p)))/100)/len(lengths)*100);j["updated_at"]=time.time();self._persist(jid)
                self.provider.generate_clip(job["prompt"],last_frame,seconds,int(job.get("seed") or 0)+index,clip,cb,ev)
                if ev.is_set():raise ProviderError("Job cancelled")
                clips.append(clip)
                if index<len(lengths)-1:
                    last_frame=safe_child(work,f"last-frame-{index+1:02d}.png");extract_last_frame(self.ffmpeg,clip,last_frame,ev)
                    # The next provider receives this frame; providers may honestly declare it unsupported.
                with self._lock:
                    j=self._jobs[jid];j["scenes"][index].update(progress=100,status="completed");j["progress"]=int((index+1)/len(lengths)*100);self._persist(jid)
            if ev.is_set():raise ProviderError("Job cancelled")
            output=safe_child(work,"output.mp4");concat_mode=concatenate(self.ffmpeg,clips,output,work,ev)
            if ev.is_set():raise ProviderError("Job cancelled")
            with self._lock:
                j=self._jobs[jid]
                if ev.is_set() or j["status"]=="cancelled":return
                j.update(status="completed",progress=100,result_file="output.mp4",concat_mode=concat_mode,error="",updated_at=time.time());self._persist(jid)
        except Exception as exc:
            with self._lock:
                j=self._jobs.get(jid)
                if not j:return
                if ev.is_set() or j["status"]=="cancelled":j.update(status="cancelled",error="",progress=min(j.get("progress",0),99))
                else:j.update(status="failed",error=str(exc),progress=0)
                j["updated_at"]=time.time();self._persist(jid)
    def close(self)->None:
        self._closed=True
        with self._lock:
            for ev in self._events.values():ev.set()
        for _ in self._threads:self._queue.put(None)
        for t in self._threads:t.join(timeout=2)
