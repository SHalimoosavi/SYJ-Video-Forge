export const STATES=["Application ready","Backend unreachable","Backend connected","FFmpeg missing","Provider unavailable","Queued","Running","Generating","Completed","Failed","Cancelled"];
const T={"Application ready":["Backend unreachable","Backend connected","FFmpeg missing","Provider unavailable","Queued","Running"],"Backend unreachable":["Backend connected","FFmpeg missing","Provider unavailable","Queued","Running","Failed"],"Backend connected":["Backend unreachable","FFmpeg missing","Provider unavailable","Queued","Running","Failed"],"FFmpeg missing":["Backend unreachable","Backend connected","Provider unavailable","Queued","Running","Failed"],"Provider unavailable":["Backend unreachable","Backend connected","FFmpeg missing","Queued","Running","Failed"],Queued:["Running","Cancelled","Failed"],Running:["Completed","Failed","Cancelled"],Generating:["Completed","Failed","Cancelled"],Completed:["Queued","Running","Backend unreachable","Backend connected"],Failed:["Queued","Running","Backend unreachable","Backend connected"],Cancelled:["Queued","Running","Backend unreachable","Backend connected"]};
export const canTransition=(a,b)=>Boolean(T[a]?.includes(b));
export function validateImage(f){if(!f)return{ok:false,error:"Choose an image first."};if(!["image/png","image/jpeg","image/webp"].includes(f.type))return{ok:false,error:"Use PNG, JPEG, or WebP."};if(!f.size||f.size>10*1024*1024)return{ok:false,error:"Image must be non-empty and no larger than 10 MiB."};return{ok:true,error:""}}
export const validatePrompt=p=>typeof p==="string"&&p.trim().length>0&&p.trim().length<=4000;
export function normalizeBaseUrl(s){try{const u=new URL(s);if(!["http:","https:"].includes(u.protocol)||u.username||u.password)return null;return u.href.replace(/\/+$/,"")}catch{return null}}
export function scenePlan(duration,clip=5){return Array.from({length:Math.ceil(Number(duration)/clip)},(_,i)=>({index:i+1,duration:Math.min(clip,Number(duration)-i*clip),status:"Not started",progress:0}))}
export function createHistoryStore(storage){const key="syj-video-forge.history.v1";return{list(){try{return JSON.parse(storage.getItem(key)||"[]").filter(x=>x&&x.kind&&x.id)}catch{return[]}},add(x){if(!x||!x.kind||x.kind==="simulated"||!x.id)return false;const a=this.list();a.unshift({...x});storage.setItem(key,JSON.stringify(a.slice(0,50)));return true},clear(){storage.removeItem(key)}}}
export function requestDisclosure(provider,url){if(provider==="mock")return"Mock provider: simulated interface progress only. No prompt or image is sent to a remote service.";if(provider==="local")return`Local backend: after submission, prompt and optional image are sent to ${url}.`;if(provider==="custom")return`Custom HTTP endpoint: after submission, prompt and optional image are sent to ${url}.`;return"Unknown provider: no request will be sent."}

/** Token guard used to discard late async responses after a run is cancelled. */
export class RunGate{
 constructor(){this.token=0;this.cancelled=false;this.jobId=null;this.controller=null}
 begin(controller=new AbortController()){this.token+=1;this.cancelled=false;this.jobId=null;this.controller=controller;return this.token}
 setJobId(token,id){if(!this.isCurrent(token))return false;this.jobId=id;return true}
 isCurrent(token){return token===this.token&&!this.cancelled}
 cancel(){if(this.cancelled)return null;this.cancelled=true;const id=this.jobId;if(this.controller)this.controller.abort();this.token+=1;return id}
}
