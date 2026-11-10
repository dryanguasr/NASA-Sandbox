/** Package immutable evidence for Mission Control. Does not run any simulation. */
import { execFileSync, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, 'web/public');
const sourceCommit = '450fa0c57b4073e0d96060a2a28c5c50d6393dd9';
const preparationCommit = '87574fc99a11b20870481426e93178bdd87d21a0';
const git = (...args) => execFileSync('git', args, { cwd: root, maxBuffer: 64 * 1024 * 1024 });
const readSource = (file, ref = sourceCommit) => git('show', `${ref}:${file}`);
const hash = buffer => createHash('sha256').update(buffer).digest('hex');
const write = (file, content) => { const dest = path.join(output, file); fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.writeFileSync(dest, content); };
const readJson = file => JSON.parse(readSource(file).toString('utf8'));
const sourceUrl = (file, ref = sourceCommit, raw = false) => raw
  ? `https://raw.githubusercontent.com/dryanguasr/NASA-Sandbox/${ref}/${file}`
  : `https://github.com/dryanguasr/NASA-Sandbox/blob/${ref}/${file}`;
const classify = file => file.startsWith('evidence/jezero_replay/') ? 'kinematic_replay'
  : /^evidence\/jezero_(belva|live|56)\//.test(file) ? 'closed_loop_gazebo'
  : file.startsWith('evidence/jezero/') ? 'simulation_2_5d' : 'gazebo_integration_synthetic';
const scenario = file => file.includes('/jezero_belva/') ? 'Belva · 128 × 128 m'
  : file.includes('/jezero_replay/') || file.includes('/jezero/') ? 'Jezero · 512 × 512 m'
  : file.includes('/jezero_') ? 'Jezero · escenarios históricos' : 'Piloto base · terreno sintético';

const videos = [
  { id: 'belva', title: 'Belva · el relieve decide el camino', source_path: 'evidence/jezero_belva/belva.mp4',
    src: 'media/belva.mp4', poster: 'media/belva.jpg', poster_time_s: 7,
    experiment_type: 'closed_loop_gazebo', fidelity_label: 'Gazebo · lazo cerrado', scenario: 'Belva · 128 × 128 m',
    policy: 'information_hungarian', seed: 7, run_id: 'belva-steady-seed-7',
    report: 'evidence/jezero_belva/report.html', report_source: 'evidence/jezero_belva/report.md',
    summary: 'Cámaras de la ejecución registrada en Gazebo. Los drones descubren dos marcadores ficticios; rover_2 inspecciona S1 y human_1 lo muestrea. S2 queda inaccesible por tierra. Se confirman seis regresos en 453,77 s simulados. Humanos y drones cinemáticos; este video no corresponde a las cinco semillas posteriores.' },
  { id: 'replay', title: 'Jezero · seis perspectivas de una misión', source_path: 'evidence/jezero_replay/jezero_multivista.mp4',
    src: 'media/jezero_multivista.mp4', poster: 'media/jezero_multivista.jpg', poster_time_s: 18,
    experiment_type: 'kinematic_replay', fidelity_label: 'Reproducción cinemática', scenario: 'Jezero · 512 × 512 m',
    policy: 'information_hungarian', seed: 7, run_id: 'jezero-replay-multivista',
    report: 'docs/jezero_diagnostico.html', report_source: 'docs/jezero_diagnostico.md',
    summary: 'Mapa cenital y seis cámaras sincronizadas de la misión 2.5D existente de 1930 s. Gazebo mueve agentes estáticos por poses a 40×. Es una reproducción visual registrada, sin cálculo nuevo, control cerrado ni validación dinámica.' },
  { id: 'base', title: 'Piloto base · integración de seis agentes', source_path: 'evidence/piloto_marciano.mp4',
    src: 'media/piloto_marciano.mp4', poster: 'media/piloto_marciano.jpg', poster_time_s: 18,
    experiment_type: 'gazebo_integration_synthetic', fidelity_label: 'Gazebo · integración sintética', scenario: 'Piloto base · 90 × 90 m',
    policy: null, seed: null, run_id: 'mars-sandbox-p0-p2',
    report: 'docs/pilot_results.html', report_source: 'docs/pilot_results.md',
    summary: 'Cámaras reales del simulador Gazebo: carga y sensores, movimiento individual, movimiento simultáneo y parada de los seis agentes. Terreno local sintético. Drones y humanos cinemáticos, sin aerodinámica ni biomecánica validadas. El montaje incluye rótulos de fase y no tiene narración.' },
];

const paths = git('ls-tree', '-r', '--name-only', sourceCommit, 'evidence').toString('utf8').trim().split('\n');
const copied = new Map();
const downloads = [];
const copySource = (file, dest = file, ref = sourceCommit) => {
  const buffer = readSource(file, ref); write(dest, buffer); copied.set(file, dest);
  downloads.push({ path: dest, source_path: file, origin_commit: ref, bytes: buffer.length, sha256: hash(buffer) });
};

// Raw reports and numerical evidence remain byte-identical to their pinned Git source.
for (const file of paths.filter(file => /\.(md|json|csv)$/.test(file))) copySource(file);
for (const file of ['evidence/jezero/events.jsonl', 'evidence/jezero_belva/telemetry.tar.gz', 'evidence/jezero_belva/seed-telemetry.tar.gz',
  'data/jezero/metadata.json', 'data/jezero_live/belva/metadata.json', 'data/scenario.json',
  'docs/data_provenance.md', 'docs/jezero_diagnostico.md', 'docs/jezero_pilot_codex.md', 'docs/pilot_results.md',
  'pilots/jezero/README.md', 'pilots/jezero/LIVE.md', 'LICENSE']) copySource(file);
const preparationPaths = git('ls-tree', '-r', '--name-only', preparationCommit, 'docs/space_apps_preparacion').toString('utf8').trim().split('\n');
for (const file of preparationPaths) copySource(file, `preparacion/${path.basename(file)}`, preparationCommit);
copySource('docs/codex/GOAL_interfaz_web.md', 'codex/GOAL_interfaz_web.md', preparationCommit);

const probeVideo = file => {
  const metadata = JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-show_entries',
    'stream=codec_type,codec_name,width,height,nb_frames,r_frame_rate:format=duration', '-of', 'json', file], { encoding: 'utf8' }));
  const stream = metadata.streams.find(item => item.codec_type === 'video');
  const audio = metadata.streams.filter(item => item.codec_type === 'audio');
  const decode = spawnSync('ffmpeg', ['-v', 'error', '-i', file, '-f', 'null', '-'], { encoding: 'utf8', maxBuffer: 4 * 1024 * 1024 });
  if (!stream || decode.status !== 0 || decode.stderr.trim()) throw new Error(`Invalid video ${file}: ${decode.stderr || decode.error || 'missing stream'}`);
  return { duration_s: Number(metadata.format.duration), codec: stream.codec_name, width: stream.width, height: stream.height,
    frames: stream.nb_frames ? Number(stream.nb_frames) : null, frame_rate: stream.r_frame_rate,
    audio: audio.length ? { present: true, codecs: audio.map(item => item.codec_name) } : { present: false, codecs: [] },
    narration: audio.length ? 'not_transcribed' : 'no_audio_track', decode_exit_code: decode.status, decode_errors: [] };
};
const verification = [];
for (const video of videos) {
  const buffer = readSource(video.source_path); write(video.src, buffer); copied.set(video.source_path, video.src);
  const metadata = probeVideo(path.join(output, video.src));
  Object.assign(video, metadata, { bytes: buffer.length, sha256: hash(buffer), origin_commit: sourceCommit,
    source_url: sourceUrl(video.source_path), status: 'available', transcript: video.summary, subtitles: null,
    subtitles_note: metadata.audio.present ? 'La pista requiere revisión antes de publicar subtítulos.' : 'Sin pista de audio ni narración. Resumen textual accesible disponible.' });
  const posterPath = path.join(output, video.poster);
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-ss', String(video.poster_time_s), '-i', path.join(output, video.src), '-frames:v', '1', '-q:v', '2', posterPath]);
  video.poster_sha256 = hash(fs.readFileSync(posterPath));
  verification.push({ source_path: video.source_path, packaged_path: video.src, sha256: video.sha256,
    bytes: video.bytes, ...metadata, poster: video.poster, poster_time_s: video.poster_time_s, poster_sha256: video.poster_sha256 });
}

// Full catalogue links unbundled originals to the immutable source revision.
const inventory = [];
for (const file of paths.filter(file => /\.(mp4|gif|png|md|tar\.gz|json|csv|jsonl)$/.test(file))) {
  const buffer = readSource(file);
  const selected = videos.find(video => video.source_path === file);
  const type = file.endsWith('.mp4') ? 'video' : /\.(png|gif)$/.test(file) ? 'image'
    : file.endsWith('.tar.gz') || file.endsWith('.jsonl') ? 'telemetry' : file.endsWith('.md') ? 'report' : 'data';
  const local = path.join(root, file);
  let metadata = selected ? { duration_s: selected.duration_s, codec: selected.codec, width: selected.width, height: selected.height, audio: selected.audio } : {};
  if (type === 'video' && !selected && fs.existsSync(local) && hash(fs.readFileSync(local)) === hash(buffer)) {
    metadata = probeVideo(local);
    verification.push({ source_path: file, packaged_path: null, sha256: hash(buffer), bytes: buffer.length, ...metadata });
  }
  inventory.push({ source_path: file, type, bytes: buffer.length, sha256: hash(buffer), origin_commit: sourceCommit,
    experiment_type: classify(file), scenario: scenario(file), policy: selected?.policy ?? null, seed: selected?.seed ?? null,
    historical_communication_trial: file.includes('piloto_4'), bundled: copied.has(file), local_path: copied.get(file) ?? null,
    source_url: sourceUrl(file), download_url: sourceUrl(file, sourceCommit, true), ...metadata });
}

// A small escaped Markdown renderer keeps the copied originals downloadable while
// making their reports readable in the browser. Links resolve to packaged files
// where present and otherwise to the immutable Git source, never to missing media.
const escape = text => text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const htmlDest = dest => dest.replace(/\.md$/, '.html');
const resolveLink = (href, sourceFile, destFile) => {
  if (/^(https?:|mailto:|#)/.test(href)) return href;
  if (/^[a-z][a-z\d+.-]*:/i.test(href)) return '#';
  const [target, fragment] = href.split('#');
  const sourceTarget = path.posix.normalize(path.posix.join(path.posix.dirname(sourceFile), target));
  const local = copied.get(sourceTarget);
  const result = local ? path.posix.relative(path.posix.dirname(destFile), htmlDest(local))
    : sourceUrl(sourceTarget, sourceTarget.startsWith('docs/space_apps_preparacion/') ? preparationCommit : sourceCommit);
  return result + (fragment ? `#${fragment}` : '');
};
const inline = (text, src, dest) => escape(text)
  .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, label, href) => `<a href="${escape(resolveLink(href, src, dest))}">${label || 'Imagen de evidencia'}</a>`)
  .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => `<a href="${escape(resolveLink(href, src, dest))}">${label}</a>`)
  .replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
function renderMarkdown(text, src, dest) {
  let fenced = false, table = false; const body = [];
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith('```')) { body.push(fenced ? '</code></pre>' : '<pre><code>'); fenced = !fenced; continue; }
    if (fenced) { body.push(escape(line) + '\n'); continue; }
    if (line.startsWith('|')) {
      if (!table) { body.push('<div class="table-wrap"><table>'); table = true; }
      if (/^\|[\s:|-]+\|$/.test(line)) continue;
      body.push('<tr>' + line.split('|').slice(1,-1).map(cell => `<td>${inline(cell.trim(), src, dest)}</td>`).join('') + '</tr>'); continue;
    }
    if (table) { body.push('</table></div>'); table = false; }
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) body.push(`<h${heading[1].length}>${inline(heading[2], src, dest)}</h${heading[1].length}>`);
    else if (line.trim()) body.push(`<p>${inline(line, src, dest)}</p>`);
  }
  if (table) body.push('</table></div>');
  const title = text.match(/^#\s+(.+)/m)?.[1] ?? src;
  const home = path.posix.relative(path.posix.dirname(dest), 'index.html');
  return `<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escape(title)} · Evidencia</title><style>:root{color-scheme:dark}body{margin:0 auto;max-width:980px;padding:clamp(20px,5vw,64px);font:17px/1.7 system-ui;background:#101a21;color:#e4e9ed}a{color:#8de1ec}a:focus-visible{outline:3px solid #f3ba79}h1{line-height:1.15;font-size:clamp(28px,5vw,46px)}h2{margin-top:2em}p{overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:20px;background:#1c2932}code{font-size:.9em}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%}td{padding:10px;border-bottom:1px solid #3b4a55;min-width:100px}nav{display:flex;flex-wrap:wrap;gap:24px}.origin{color:#b3c0c7;font-size:13px}</style><nav><a href="${home}#evidencia">← Mission Control</a><a href="${path.posix.basename(src)}" download>Descargar Markdown original</a></nav><p class="origin">Copia de evidencia existente · commit ${src.startsWith('docs/space_apps_preparacion/') || src.startsWith('docs/codex/') ? preparationCommit : sourceCommit}. Las instrucciones del documento describen su ejecución original.</p>${body.join('\n')}</html>`;
}
for (const [sourceFile, dest] of copied) {
  if (!sourceFile.endsWith('.md')) continue;
  const text = fs.readFileSync(path.join(output, dest), 'utf8');
  write(htmlDest(dest), renderMarkdown(text, sourceFile, htmlDest(dest)));
}

const manifest = { schema_version: 1, source_commit: sourceCommit, preparation_commit: preparationCommit,
  note: 'Paquete de evidencia existente; exportación y decodificación no ejecutan una nueva misión.',
  license: 'LICENSE', videos, inventory, downloads,
  preparation: { interactive: 'preparacion/Manual_interactivo_Space_Apps.html',
    manual: 'preparacion/Manual_y_checklist_Space_Apps.html', manual_markdown: 'preparacion/Manual_y_checklist_Space_Apps.md',
    checklist: 'preparacion/Checklist_tecnica_Space_Apps.html', checklist_markdown: 'preparacion/Checklist_tecnica_Space_Apps.md',
    persistence: 'localStorage del navegador; no hay sincronización de equipo' } };
write('media-manifest.json', JSON.stringify(manifest, null, 2) + '\n');
const evidenceDir = path.join(root, 'evidence/ui_draft'); fs.mkdirSync(evidenceDir, { recursive: true });
const version = program => execFileSync(program, ['-version'], { encoding: 'utf8' }).split(/\r?\n/)[0];
fs.writeFileSync(path.join(evidenceDir, 'media-verification.json'), JSON.stringify({ schema_version: 1,
  checked_at: new Date().toISOString(), source_commit: sourceCommit, node: process.version,
  ffprobe: version('ffprobe'), ffmpeg: version('ffmpeg'),
  commands: ['ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,nb_frames,r_frame_rate:format=duration -of json <video>',
    'ffmpeg -v error -i <video> -f null -', 'ffmpeg -v error -y -ss <verified timestamp> -i <video> -frames:v 1 -q:v 2 <poster.jpg>'],
  videos: verification, browser_playback_and_seek: 'Verified separately in browser validation; decoding alone is insufficient.',
  original_files_modified: false }, null, 2) + '\n');
console.log(`Packaged ${videos.length} videos, ${downloads.length} source files; inventoried ${inventory.length} resources; decoded ${verification.length} videos.`);
