import{normalizeBaseUrl}from"./core.js";
export class ProviderError extends Error{constructor(m,code="PROVIDER_ERROR",status=0){super(m);this.name="ProviderError";this.code=code;this.status=status}}
export class MockProvider{
 constructor(){this.name="Mock (simulated)";this.kind="simulated";this.jobs=new Map()}
 async health(){return{connected:true,kind:"simulated"}}
 async capabilities(){return{available:true,providers:[{name:"mock",available:true,kind:"simulated"}],text:true,image:true,negative_prompt:false,max_clip_seconds:5,supports_start_image:true,kind:"simulated",durations:[5,10,15,30],simulated:true}}
 async submitText(p){return this.submit(p,"text")}
 async submitImage(p){if(!p.image)throw new ProviderError("Select an image first.","VALIDATION");return this.submit(p,"image")}
 async submit(p,mode){const id="demo-"+Date.now();this.jobs.set(id,{id,mode,status:"running",progress:0});return{id,simulated:true,kind:"simulated"}}
 async status(id){const j=this.jobs.get(id);if(!j)throw new ProviderError("Unknown job","NOT_FOUND",404);return j}
 async result(id){if(!this.jobs.has(id))throw new ProviderError("Unknown job","NOT_FOUND",404);return{id,simulated:true,label:"SIMULATED, not AI generated",url:null}}
 async cancel(id){const j=this.jobs.get(id);if(j)j.status="cancelled";return{id,status:"cancelled"}}
 advance(id,n){const j=this.jobs.get(id);if(j){j.progress=n;if(n>=100)j.status="completed"}}
}
export class HttpProvider{
 constructor(url,custom=false,fetchImpl=globalThis.fetch,timeoutMs=30000){this.baseUrl=normalizeBaseUrl(url);this.name=custom?"Custom HTTP endpoint":"Local backend";this.kind="unknown";this.fetchImpl=fetchImpl;this.timeoutMs=timeoutMs}
 async request(path,options={}){
  if(!this.baseUrl)throw new ProviderError("Enter a valid HTTP(S) endpoint URL without embedded credentials.","VALIDATION");
  const controller=new AbortController(),external=options.signal;let timedOut=false,timer=null;
  const abortExternal=()=>controller.abort(external?.reason);
  if(external?.aborted)abortExternal();else external?.addEventListener("abort",abortExternal,{once:true});
  if(this.timeoutMs>0)timer=setTimeout(()=>{timedOut=true;controller.abort()},this.timeoutMs);
  let r;
  try{
   r=await this.fetchImpl(this.baseUrl+path,{...options,signal:controller.signal,headers:{...(options.body===undefined?{}:{"Content-Type":"application/json"}),...options.headers}})
  }catch(e){
   if(timedOut)throw new ProviderError(`Request timed out after ${this.timeoutMs} ms. Check the backend and try again.`,"TIMEOUT");
   if(e?.name==="AbortError")throw e;
   throw new ProviderError("Could not reach endpoint. Check that the server is running, the URL is correct, and browser CORS/private-network access is allowed.","NETWORK")
  }finally{if(timer!==null)clearTimeout(timer);external?.removeEventListener("abort",abortExternal)}
  if(!r.ok){let detail="";try{const t=await r.text();if(t){try{const d=JSON.parse(t);detail=typeof d.error==="string"?": "+d.error:""}catch{detail=": "+t.slice(0,160)}}}catch{}throw new ProviderError("Endpoint returned HTTP "+r.status+detail,"HTTP",r.status)}
  if(r.status===204)return{};const ct=r.headers?.get?.("content-type")||"";
  try{if(ct&&!ct.includes("json"))throw new Error("Expected JSON response");return await r.json()}catch{throw new ProviderError("Endpoint returned an invalid or non-JSON response.","INVALID_RESPONSE",r.status)}
 }
 health(options){return this.request("/api/health",options)}
 capabilities(options){return this.request("/api/capabilities",options)}
 submitText(p,options={}){const{image,...rest}=p;return this.request("/api/jobs",{...options,method:"POST",body:JSON.stringify({...rest,mode:"text"})})}
 async submitImage(p,options={}){if(!p.image)throw new ProviderError("Select an image first.","VALIDATION");const bytes=await p.image.arrayBuffer();const base64=typeof Buffer!=="undefined"?Buffer.from(bytes).toString("base64"):btoa(String.fromCharCode(...new Uint8Array(bytes)));return this.request("/api/jobs",{...options,method:"POST",body:JSON.stringify({prompt:p.prompt,negativePrompt:p.negativePrompt||"",duration:p.duration,aspectRatio:p.aspectRatio,seed:p.seed,model:p.model,mode:"image",image:{mime:p.image.type,data:base64}})})}
 status(id,options){return this.request("/api/jobs/"+encodeURIComponent(id),options)}
 async result(id,options={}){const state=await this.status(id,options);if(state.status!=="completed")throw new ProviderError("Job result is not ready.","NOT_READY");return{url:this.baseUrl+"/api/jobs/"+encodeURIComponent(id)+"/result",kind:state.kind||options.kind||"unknown"}}
 cancel(id,options){return this.request("/api/jobs/"+encodeURIComponent(id)+"/cancel",{...options,method:"POST"})}
 delete(id,options){return this.request("/api/jobs/"+encodeURIComponent(id),{...options,method:"DELETE"})}
}
export function getProvider(n,u,fetchImpl){if(n==="mock")return new MockProvider();if(n==="local")return new HttpProvider(u,false,fetchImpl);if(n==="custom")return new HttpProvider(u,true,fetchImpl);throw new ProviderError("Unknown provider","VALIDATION")}
