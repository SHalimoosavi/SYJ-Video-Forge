const MAX_IMAGE_BYTES=10*1024*1024;
export const MAX_RESULT_BYTES=512*1024*1024;
export const BUNDLE_STATES=["awaiting_worker","importing","completed","failed","cancelled"];
const MIME={"image/png":b=>b.length>=8&&[137,80,78,71,13,10,26,10].every((x,i)=>b[i]===x),"image/jpeg":b=>b.length>=3&&b[0]===255&&b[1]===216&&b[2]===255,"image/webp":b=>b.length>=12&&String.fromCharCode(...b.slice(0,4))==="RIFF"&&String.fromCharCode(...b.slice(8,12))==="WEBP"};
export const transitionBundleState=(from,to)=>({awaiting_worker:["importing","cancelled","failed"],importing:["completed","failed","cancelled"],completed:["awaiting_worker","importing"],failed:["awaiting_worker","importing","cancelled"],cancelled:["awaiting_worker","importing","failed"]})[from]?.includes(to)===true;
export async function sha256Hex(data){const bytes=data instanceof ArrayBuffer?data:await data.arrayBuffer();const hash=await crypto.subtle.digest("SHA-256",bytes);return Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,"0")).join("")}
export async function validateImageFile(file){if(!file)return{ok:false,error:"Choose a starting image first."};if(!Object.hasOwn(MIME,file.type))return{ok:false,error:"Use PNG, JPEG, or WebP."};if(!file.size||file.size>MAX_IMAGE_BYTES)return{ok:false,error:"Image must be non-empty and no larger than 10 MiB."};const b=new Uint8Array(await file.slice(0,16).arrayBuffer());if(!MIME[file.type](b))return{ok:false,error:"Image magic bytes do not match its declared MIME type."};return{ok:true,error:""}}
async function imageRecord(file){const valid=await validateImageFile(file);if(!valid.ok)throw new Error(valid.error);const buf=await file.arrayBuffer(),bytes=new Uint8Array(buf);let bin="";for(let i=0;i<bytes.length;i+=0x8000)bin+=String.fromCharCode(...bytes.subarray(i,i+0x8000));return{mime:file.type,sha256:await sha256Hex(buf),base64:btoa(bin)}}
export async function createJobBundle(opts){const {prompt,negativePrompt="",aspect="16:9",totalSeconds=30,seed=0,image=null,engine="ltx-video",resolution=null,continuity="last_frame",scenePrompts=null}=opts;if(typeof prompt!=="string"||!prompt.trim()||prompt.length>4000)throw new Error("Prompt must contain 1-4000 characters.");if(typeof negativePrompt!=="string"||negativePrompt.length>2000)throw new Error("Negative prompt must be at most 2000 characters.");if(!Number.isInteger(totalSeconds)||totalSeconds<1||totalSeconds>3600)throw new Error("Duration must be an integer from 1 to 3600 seconds.");if(!Number.isInteger(seed)||seed<0||seed>2147483647)throw new Error("Seed must be an integer from 0 to 2147483647.");if(!["ltx-video","wan2.2-ti2v-5b"].includes(engine))throw new Error("Unknown AI engine.");if(!["16:9","9:16","1:1"].includes(aspect))throw new Error("Unsupported aspect ratio.");const dims=resolution||({"16:9":"512x288","9:16":"288x512","1:1":"384x384"}[aspect]);if(!["512x288","288x512","384x384","704x384","384x704","512x512"].includes(dims))throw new Error("Unsupported resolution.");const count=Math.ceil(totalSeconds/5),scenes=Array.from({length:count},(_,i)=>({index:i+1,prompt:(scenePrompts?.[i]||`${prompt.trim()} — continues the same scene with consistent subject, setting, lighting, and camera motion.`).trim()}));if(scenes.some(s=>!s.prompt||s.prompt.length>4000))throw new Error("Each scene prompt must contain 1-4000 characters.");return{schemaVersion:1,jobId:Array.from(crypto.getRandomValues(new Uint8Array(16)),b=>b.toString(16).padStart(2,"0")).join(""),createdAt:new Date().toISOString(),mode:image?"image":"text",preset:totalSeconds>=30?"Long":"Custom",prompt:prompt.trim(),negativePrompt,aspect,resolution:dims,seed,totalSeconds,fps:24,clipSeconds:5,continuity,engine:{id:engine},scenes,image:image?await imageRecord(image):null}}
export async function validateJobBundle(job){
  if(!job||job.schemaVersion!==1||!/^[0-9a-f]{32}$/.test(job.jobId||""))throw new Error("Invalid job bundle schema or jobId.");
  if(typeof job.createdAt!=="string"||Number.isNaN(Date.parse(job.createdAt)))throw new Error("Invalid bundle createdAt timestamp.");
  if(!["text","image"].includes(job.mode)||!Array.isArray(job.scenes)||!job.scenes.length)throw new Error("Invalid job bundle mode or scenes.");
  if(typeof job.prompt!=="string"||!job.prompt.trim()||job.prompt.length>4000)throw new Error("Invalid bundle prompt.");
  if(typeof job.negativePrompt!=="string"||job.negativePrompt.length>2000)throw new Error("Invalid negative prompt.");
  if(!["16:9","9:16","1:1"].includes(job.aspect)||!["512x288","288x512","384x384","704x384","384x704","512x512"].includes(job.resolution))throw new Error("Invalid aspect or resolution.");
  if(!Number.isInteger(job.seed)||job.seed<0||job.seed>2147483647||!Number.isInteger(job.fps)||job.fps<1||job.fps>60)throw new Error("Invalid seed or fps.");
  if(!Number.isInteger(job.totalSeconds)||job.totalSeconds<1||job.totalSeconds>3600||!Number.isInteger(job.clipSeconds)||job.clipSeconds<1||job.clipSeconds>60)throw new Error("Invalid bundle duration or clipSeconds.");
  if(job.preset==="Long"&&job.totalSeconds<30)throw new Error("Long preset requires at least 30 seconds.");
  if(!["last_frame","none"].includes(job.continuity)||!job.engine||!["ltx-video","wan2.2-ti2v-5b"].includes(job.engine.id))throw new Error("Invalid continuity or engine request.");
  if(job.scenes.length!==Math.ceil(job.totalSeconds/job.clipSeconds)||job.scenes.some((s,i)=>!s||s.index!==i+1||typeof s.prompt!=="string"||!s.prompt.trim()||s.prompt.length>4000))throw new Error("Invalid scene count or scene prompt schema.");
  if(job.mode==="image"&&!job.image)throw new Error("Image mode requires image data.");
  if(job.image){
    if(!MIME[job.image.mime]||!/^[0-9a-f]{64}$/.test(job.image.sha256||"")||typeof job.image.base64!=="string")throw new Error("Invalid image record.");
    let raw;try{const bin=atob(job.image.base64);if(bin.length>MAX_IMAGE_BYTES||!bin.length)throw new Error("Image size is invalid.");raw=Uint8Array.from(bin,c=>c.charCodeAt(0))}catch(e){throw new Error("Image base64 is invalid or exceeds the 10 MiB limit.")}
    if(!MIME[job.image.mime](raw))throw new Error("Image magic bytes do not match the declared MIME type.");
    if(await sha256Hex(raw.buffer)!==job.image.sha256)throw new Error("Image SHA-256 mismatch.");
  }
  return true;
}
export function validateManifestShape(manifest,job){
  if(!manifest||manifest.schemaVersion!==1)throw new Error("Unsupported manifest schema; expected schemaVersion 1.");
  if(manifest.status!=="completed")throw new Error("Worker manifest is not marked completed; refusing failed or incomplete output.");
  if(manifest.jobId!==job.jobId)throw new Error("Manifest jobId does not match the selected job bundle.");
  if(!["ai_generated","test_pattern"].includes(manifest.kind))throw new Error("Invalid manifest kind; refusing an unrecognized or spoofed kind.");
  const engine=manifest.engine;
  if(!engine||typeof engine.id!=="string"||typeof engine.model!=="string")throw new Error("Manifest engine metadata is missing.");
  if(manifest.kind==="ai_generated"&&(!["ltx-video","wan2.2-ti2v-5b"].includes(engine.id)||({"ltx-video":"Lightricks/LTX-Video","wan2.2-ti2v-5b":"Wan-AI/Wan2.2-TI2V-5B"})[engine.id]!==engine.model))throw new Error("AI kind is not valid for this engine/model; refusing a test-engine or mismatched model claim.");
  if(manifest.kind==="test_pattern"&&(engine.id!=="fake-test-pattern"||engine.model!=="ffmpeg:testsrc"))throw new Error("test_pattern kind requires the test-only FakeEngine identity.");
  const final=manifest.final;
  if(!final||final.file!=="result.mp4"||!/^[0-9a-f]{64}$/.test(final.sha256||""))throw new Error("Manifest final result metadata is invalid.");
  if(!Number.isFinite(final.duration)||final.duration<=0||!Number.isInteger(final.width)||final.width<1||!Number.isInteger(final.height)||final.height<1||!final.fps||typeof final.codec!=="string")throw new Error("Manifest final media metadata is incomplete.");
  if(!Array.isArray(manifest.scenes)||manifest.scenes.length!==job.scenes.length)throw new Error("Manifest scenes do not match the job scene count.");
  for(let i=0;i<manifest.scenes.length;i++){const scene=manifest.scenes[i];if(!scene||scene.index!==i+1||scene.status!=="completed"||!Number.isInteger(scene.frames)||scene.frames<1||typeof scene.file!=="string"||!scene.file.startsWith("scenes/")||scene.file.startsWith("/")||scene.file.includes("..")||!/^[0-9a-f]{64}$/.test(scene.sha256||""))throw new Error(`Manifest scene ${i+1} is incomplete or invalid.`)}
  if(!manifest.hardware||typeof manifest.hardware.gpu!=="string")throw new Error("Manifest hardware metadata is missing.");
  return true;
}
export async function verifyImportedResult(videoFile,manifest,job){if(!videoFile||videoFile.size<=0||videoFile.size>MAX_RESULT_BYTES)throw new Error("result.mp4 is empty or exceeds the 512 MiB browser import limit.");const head=new Uint8Array(await videoFile.slice(0,16).arrayBuffer());if(head.length<12||String.fromCharCode(...head.slice(4,8))!=="ftyp")throw new Error("Selected video does not have an MP4 ftyp signature.");await validateJobBundle(job);validateManifestShape(manifest,job);const actual=await sha256Hex(videoFile);if(actual!==manifest.final.sha256)throw new Error("SHA-256 mismatch: result.mp4 does not match manifest.final.sha256.");return{sha256:actual,kind:manifest.kind,model:manifest.engine.model,gpu:manifest.hardware?.gpu||"unknown",engineId:manifest.engine.id}}
