import {fileURLToPath} from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
const web=path.dirname(fileURLToPath(import.meta.url)),root=path.dirname(web),out=path.join(web,'dist');
for(const script of ['build_web_data.mjs','build_web_media.mjs'])execFileSync(process.execPath,[path.join(root,'scripts',script)],{cwd:root,stdio:'inherit'});
// Only this generated output directory is replaced, never source evidence.
if(path.dirname(out)!==web||path.basename(out)!=='dist')throw new Error('Unsafe output path');
fs.rmSync(out,{recursive:true,force:true});fs.mkdirSync(out,{recursive:true});
for(const file of ['index.html','style.css','app.js','replay.js','copy.js','icon.svg'])fs.copyFileSync(path.join(web,file),path.join(out,file));
fs.cpSync(path.join(web,'public'),out,{recursive:true});fs.writeFileSync(path.join(out,'.nojekyll'),'');
let count=0,bytes=0;function visit(dir){for(const f of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,f.name);if(f.isDirectory())visit(p);else{count++;bytes+=fs.statSync(p).size;}}}visit(out);
console.log(JSON.stringify({build:'complete',directory:out,files:count,bytes,node:process.version}));
