import http from 'node:http';import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const web=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(process.argv[2]||path.join(web,'dist'));const port=Number(process.env.PORT||4173);
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.jpg':'image/jpeg','.png':'image/png','.mp4':'video/mp4','.md':'text/plain; charset=utf-8','.csv':'text/csv','.vtt':'text/vtt'};
const testCSP="default-src 'self' data: blob: 'unsafe-inline'; connect-src 'self';";
function serveTestDocument(req,res,relative,url){
 const preparation=relative==='/__tests__/preparation.html';
 const mode=url.searchParams.get('mode')||'normal';
 if(!['normal','missing','incompatible','missing-video'].includes(mode)){res.writeHead(400).end('Unknown test mode');return;}
 let html;try{html=fs.readFileSync(path.join(root,preparation?'preparacion/Manual_interactivo_Space_Apps.html':'index.html'),'utf8');}catch{res.writeHead(404).end('Build the local artifact before running browser tests.');return;}
 if(preparation){
  const key="const KEY='space-apps-preparation-v1'";
  if(!html.includes(key)){res.writeHead(409).end('Preparation schema changed; refusing to touch original localStorage.');return;}
  html=html.replace(key,"const KEY='space-apps-preparation-qa-harness-v1'");
 }
 const probe='<base href="/NASA-Sandbox/"><script src="/__tests__/probe.js"></script>';
 html=html.replace(/<head>/i,'<head>'+probe);
 const bytes=Buffer.from(html);
 res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Length':bytes.length,'Cache-Control':'no-store','Content-Security-Policy':testCSP});
 if(req.method==='HEAD')res.end();else res.end(bytes);
}
const server=http.createServer((req,res)=>{let relative,url;try{url=new URL(req.url,'http://localhost');relative=decodeURIComponent(url.pathname);}catch{res.writeHead(400).end();return;}
 relative=relative.replace(/^\/NASA-Sandbox(?=\/|$)/,'');if(relative.endsWith('/'))relative+='index.html';
 if(relative==='/__tests__/app.html'||relative==='/__tests__/preparation.html'){serveTestDocument(req,res,relative,url);return;}
 const testFiles={'/__tests__/browser.html':'browser.html','/__tests__/probe.js':'probe.js'};
 const testRoute=Object.hasOwn(testFiles,relative);
 const file=testRoute?path.join(web,'tests',testFiles[relative]):path.resolve(root,'.'+relative);if(!testRoute&&file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
 let stat;try{stat=fs.statSync(file);if(!stat.isFile())throw Error();}catch{res.writeHead(404,{'Content-Type':'text/plain'}).end('Recurso no disponible');return;}
 const headers={'Content-Type':types[path.extname(file)]||'application/octet-stream','Accept-Ranges':'bytes','Cache-Control':'no-cache'};
 let start=0,end=stat.size-1,status=200;
 if(req.headers.range){const match=/^bytes=(\d+)-(\d*)$/.exec(req.headers.range);if(!match){res.writeHead(416).end();return;}start=Number(match[1]);end=match[2]?Math.min(Number(match[2]),end):end;if(start>end){res.writeHead(416,{'Content-Range':`bytes */${stat.size}`}).end();return;}status=206;headers['Content-Range']=`bytes ${start}-${end}/${stat.size}`;}
 headers['Content-Length']=end-start+1;res.writeHead(status,headers);if(req.method==='HEAD')res.end();else fs.createReadStream(file,{start,end}).pipe(res);
});server.listen(port,'127.0.0.1',()=>console.log(`Local: http://127.0.0.1:${port}/NASA-Sandbox/\nRoot: ${root}`));
