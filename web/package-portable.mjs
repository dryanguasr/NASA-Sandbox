import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
const web=path.dirname(fileURLToPath(import.meta.url)),dest=path.join(web,'portable');
if(path.dirname(dest)!==web)throw Error('Unsafe package destination');
fs.mkdirSync(dest,{recursive:true});fs.cpSync(path.join(web,'dist'),path.join(dest,'dist'),{recursive:true});
fs.copyFileSync(path.join(web,'serve.mjs'),path.join(dest,'serve.mjs'));
fs.writeFileSync(path.join(dest,'LEEME.txt'),`JEZERO MISSION CONTROL - RESPALDO LOCAL\n\nRequiere Node.js 22 o posterior, sin instalar paquetes.\nDesde esta carpeta: node serve.mjs\nAbrir http://127.0.0.1:4173/NASA-Sandbox/\nPara usar otro puerto en PowerShell: $env:PORT=4174; node serve.mjs\n\nAlternativa Python3: python -m http.server 8000 --directory dist\nAbrir http://localhost:8000/ (rutas relativas funcionan desde la raiz).\nLos3MP4, mapas, informes y manual estan incluidos. Sin CDN ni red externa para la demo.\nNo abrir mediante file://: los modulos y fetch requieren servidor HTTP local.\nLa checklist guarda datos solo en este navegador; exportar JSON para respaldo.\nLos enlaces externos a fuentes originales requieren internet.\n\nRegistro2.5D y medios:450fa0c57b4073e0d96060a2a28c5c50d6393dd9\nPreparacion:87574fc99a11b20870481426e93178bdd87d21a0\nNo se ejecuta una simulacion nueva.\n`);
console.log(dest);
