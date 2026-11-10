#!/usr/bin/env node
/** Normalize immutable recorded evidence for the web. No mission code is run. */
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const SOURCE_COMMIT = '450fa0c57b4073e0d96060a2a28c5c50d6393dd9';
export const AGENTS = ['human_1', 'human_2', 'rover_1', 'rover_2', 'drone_1', 'drone_2'];
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const sourceCache = new Map();
const sha256 = buffer => createHash('sha256').update(buffer).digest('hex');

export function sourceBytes(path, root = ROOT) {
  const key = `${root}:${path}`;
  if (!sourceCache.has(key)) {
    sourceCache.set(key, execFileSync('git', ['show', `${SOURCE_COMMIT}:${path}`], {
      cwd: root, maxBuffer: 32 * 1024 * 1024,
    }));
  }
  return sourceCache.get(key);
}
const sourceJSON = path => JSON.parse(sourceBytes(path).toString('utf8'));

export function parseRecordedViewer(html) {
  const match = html.match(/(?:^|\n)const D=(\{[^\n]+\});\r?\n/);
  if (!match) throw new Error('Viewer payload missing; export aborted, no synthetic fallback.');
  const d = JSON.parse(match[1]);
  if (d.n !== 64 || d.side !== 512 || !Array.isArray(d.trajectory) || !d.trajectory.length) {
    throw new Error('Incompatible recorded viewer schema.');
  }
  for (const f of d.trajectory) {
    if (Object.keys(f.positions).sort().join() !== [...AGENTS].sort().join()) {
      throw new Error(`Incompatible agents at ${f.time_s} s.`);
    }
    if (Object.values(f.positions).some(p => p.length !== 4 || p.some(x => !Number.isFinite(x)))) {
      throw new Error(`Invalid recorded position at ${f.time_s} s.`);
    }
  }
  for (const [label, list] of [['trajectory', d.trajectory], ['frames', d.frames], ['events', d.events]]) {
    if (list.some((f, i) => !Number.isFinite(f.time_s) || (i && f.time_s < list[i - 1].time_s))) {
      throw new Error(`Non-monotonic ${label}.`);
    }
  }
  if (d.mean.length !== d.frames.length || d.sigma.length !== d.frames.length) {
    throw new Error('Grid/frame count mismatch.');
  }
  for (const grid of [d.prior, d.reference, ...d.mean]) {
    if (Buffer.from(grid, 'base64').length !== d.n * d.n * 2) throw new Error('Invalid elevation grid.');
  }
  for (const grid of d.sigma) {
    if (Buffer.from(grid, 'base64').length !== d.n * d.n) throw new Error('Invalid uncertainty grid.');
  }
  return d;
}

export function buildMission() {
  const d = parseRecordedViewer(sourceBytes('evidence/jezero/viewer.html').toString('utf8'));
  const summary = sourceJSON('evidence/jezero/summary.json');
  if (JSON.stringify(d.summary) !== JSON.stringify(summary)) throw new Error('Viewer and summary disagree.');
  const events = sourceBytes('evidence/jezero/events.jsonl').toString('utf8').trim().split(/\r?\n/).map(JSON.parse);
  if (JSON.stringify(d.events) !== JSON.stringify(events)) throw new Error('Viewer and events disagree.');
  const tasks = sourceJSON('evidence/jezero/tasks.json');
  const metadata = sourceJSON('data/jezero/metadata.json');
  const terrainHash = sha256(sourceBytes('data/jezero/terrain.npz'));
  if (terrainHash !== summary.terrain_sha256 || terrainHash !== metadata.terrain_sha256) {
    throw new Error('Pinned terrain, metadata and recorded mission hashes disagree.');
  }
  const detected = new Map(events.filter(e => e.event === 'site_detected').map(e => [e.site, e]));
  const eventIndex = predicate => events.findIndex(predicate);
  const milestone = (id, label, predicate, explanation) => {
    const i = eventIndex(predicate);
    if (i < 0) throw new Error(`Required recorded milestone absent: ${id}`);
    return { id, label, time_s: events[i].time_s, event_index: i, explanation };
  };
  const milestones = [
    milestone('initial', 'Mapa inicial', e => e.event === 'initial_base_survey', 'CTX es el conocimiento orbital aproximado. El registro comienza con un reconocimiento previo del hábitat y los sensores ideales activos.'),
    milestone('survey', 'Reconocimiento', e => e.event === 'completed' && e.kind === 'survey', 'Se completa la primera tarea de reconocimiento aéreo registrada. Las observaciones ideales actualizan el mapa estimado.'),
    milestone('discovery', 'Objetivo descubierto', e => e.event === 'site_detected', 'drone_2 detecta el marcador ficticio S2. Se crea inspect:S2 y se asigna a rover_2 en el mismo instante registrado.'),
    milestone('inspection', 'Inspección → muestreo', e => e.event === 'completed' && e.kind === 'inspect', 'rover_2 completa inspect:S2. Esta terminación habilita sample:S2 para un humano; los costos de candidatos no están registrados.'),
    milestone('sample', 'Primera muestra', e => e.event === 'completed' && e.kind === 'sample', 'human_1 completa sample:S2. El muestreo es una actividad ficticia del escenario, sin análisis real de minerales.'),
    milestone('return', 'Retorno del equipo', e => e.event === 'return_phase', 'Finalizados los cuatro muestreos, se crean tareas individuales de regreso para los seis agentes.'),
    milestone('complete', 'Resultado registrado', e => e.event === 'completed' && e.kind === 'return' && e.time_s === summary.duration_s, 'El último regreso completa la misión guardada. El explorador reproduce ese registro; no ejecuta un cálculo nuevo.'),
  ];
  return {
    schema_version: 1,
    run_id: 'jezero-information-7', scenario_id: 'jezero-512m-fixed-targets',
    execution_type: 'simulation_2_5d', playback_mode: 'recorded',
    source_commit: SOURCE_COMMIT, policy: summary.policy, seed: summary.seed,
    communication: summary.communication,
    units: { time: 's', position: 'm', heading: 'rad', uncertainty: 'm', coverage: 'fraction' },
    coordinate_frame: { type: 'Mars_local_equirectangular', north_up: true, row_order: 'north_to_south', side_m: 512, radius_m: 3396190, center_lat_deg: 18.45, center_lon_east_deg: 77.45 },
    display_grid: { n: 64, sample_spacing_m: 8, computational_grid_spacing_m: 4, elevation_encoding: 'base64_uint16_le_normalized', elevation_min_m: null, elevation_max_m: null, elevation_note: 'Escala común normalizada del visor original; extremos métricos no exportados. No interpretar el valor normalizado como altura en metros.', sigma_encoding: 'base64_uint8', sigma_max_m: 3, temporal_sampling: 'previous_recorded_frame', trajectory_sampling: 'previous_recorded_position', scientific_interpolation: false },
    agents: AGENTS,
    ...d,
    sites: d.sites.map(site => ({ ...site, detected_s: detected.get(site.id)?.time_s ?? null, detected_by: detected.get(site.id)?.agent ?? null, injected: true })),
    tasks, milestones,
    metadata,
    source_files: ['evidence/jezero/viewer.html', 'evidence/jezero/summary.json', 'evidence/jezero/events.jsonl', 'evidence/jezero/tasks.json', 'data/jezero/metadata.json'],
    missing: { detailed_assignment_candidates: null, energy: null, operational_eva_safety: null },
  };
}

export function buildComparison() {
  const b = sourceJSON('evidence/jezero/benchmark_summary.json');
  return {
    schema_version: 1, scenario_id: 'jezero-512m-fixed-targets',
    execution_type: 'simulation_2_5d', mode: 'recorded_final_metrics',
    source_commit: SOURCE_COMMIT, source_file: 'evidence/jezero/benchmark_summary.json',
    ...b,
    communication: 'global, instantaneous, lossless',
    compatible: true,
    compatibility_basis: 'Mismo recorte y disposición de objetivos. Las semillas 7, 11 y 19 solo varían el ruido del sensor.',
    trajectory_availability: { information_hungarian: 'jezero-information-7', nearest_greedy: null },
    limitation: 'Comparación de estados finales. La trayectoria de proximidad no está en la evidencia versionada; no se fabrica una animación. Tres semillas no prueban generalización.',
  };
}

export function buildBelva() {
  const result = sourceJSON('evidence/jezero_belva/result.json');
  const seedComparison = sourceJSON('evidence/jezero_belva/seed-comparison.json');
  return {
    schema_version: 1, run_id: 'belva-recorded-steady-7', scenario_id: 'belva-pilot-7',
    execution_type: 'gazebo_closed_loop', playback_mode: 'video_and_summary',
    source_commit: SOURCE_COMMIT, policy: result.policy, seed: result.seed,
    communication: 'ideal', result, seedComparison,
    trajectory: null,
    limitation: 'Gazebo ejecutó percepción simulada y control por velocidad; humanos y drones cinemáticos. No valida aerodinámica ni EVA. El video y esta corrida de 453,77 s son distintos de las cinco repeticiones de consistencia.',
  };
}

export function buildData(out = join(ROOT, 'web/public/data')) {
  mkdirSync(out, { recursive: true });
  mkdirSync(join(out, 'source'), { recursive: true });
  const mission = buildMission();
  const comparison = buildComparison();
  const belva = buildBelva();
  const artifacts = {
    'mission.json': mission, 'comparison.json': comparison, 'belva.json': belva,
    'runs.json': {
      schema_version: 1, source_commit: SOURCE_COMMIT,
      runs: [
        { run_id: mission.run_id, scenario_id: mission.scenario_id, execution_type: mission.execution_type, policy: mission.policy, seed: mission.seed, playback: 'recorded_trajectory', data: 'mission.json' },
        { run_id: 'jezero-nearest-benchmark', scenario_id: mission.scenario_id, execution_type: 'simulation_2_5d', policy: 'nearest_greedy', seed: null, seeds: comparison.seeds, playback: 'metrics_only', data: 'comparison.json', trajectory: null },
        { run_id: belva.run_id, scenario_id: belva.scenario_id, execution_type: belva.execution_type, policy: belva.policy, seed: belva.seed, playback: 'video_and_summary', data: 'belva.json', trajectory: null },
        { run_id: 'jezero-gazebo-replay', scenario_id: mission.scenario_id, execution_type: 'kinematic_replay', policy: mission.policy, seed: 7, playback: 'video_only', data: null, trajectory: null },
      ],
    },
  };
  const copySources = {
    'evidence/jezero/summary.json': 'summary.json',
    'evidence/jezero/benchmark_summary.json': 'benchmark_summary.json',
    'evidence/jezero/benchmark.csv': 'benchmark.csv',
    'evidence/jezero/metrics.csv': 'metrics.csv',
    'evidence/jezero/events.jsonl': 'events.jsonl',
    'evidence/jezero/tasks.json': 'tasks.json',
    'data/jezero/metadata.json': 'metadata.json',
    'evidence/jezero_belva/result.json': 'belva-result.json',
    'evidence/jezero_belva/seed-comparison.json': 'belva-seed-comparison.json',
  };
  const inputs = [...Object.keys(copySources), 'evidence/jezero/viewer.html', 'evidence/jezero/report.md', 'evidence/jezero_belva/report.md', 'data/jezero/terrain.npz'];
  const sources = inputs.map(path => {
    const bytes = sourceBytes(path);
    const isBelva = path.includes('belva');
    const entry = {
      path, bytes: bytes.length, sha256: sha256(bytes), source_commit: SOURCE_COMMIT,
      last_changed_commit: execFileSync('git', ['log', '-1', '--format=%H', SOURCE_COMMIT, '--', path], { cwd: ROOT, encoding: 'utf8' }).trim(),
      execution_type: isBelva ? 'gazebo_closed_loop' : 'simulation_2_5d',
      scenario: isBelva ? 'belva-pilot-7' : 'jezero-512m-fixed-targets',
      policy: path.includes('benchmark') || path.includes('terrain') || path.includes('metadata') ? null : 'information_hungarian',
      seed: path.includes('benchmark') || path.includes('seed-comparison') || path.includes('terrain') || path.includes('metadata') ? null : 7,
      duration_s: null,
      url: `https://github.com/dryanguasr/NASA-Sandbox/blob/${SOURCE_COMMIT}/${path}`,
      download: copySources[path] ? `source/${copySources[path]}` : null,
    };
    if (copySources[path]) writeFileSync(join(out, entry.download), bytes);
    return entry;
  });
  for (const [name, value] of Object.entries(artifacts)) writeFileSync(join(out, name), `${JSON.stringify(value)}\n`);
  const manifest = {
    schema_version: 1, source_commit: SOURCE_COMMIT,
    generation: 'Deterministic extraction of pinned Git blobs; no algorithms or pilots executed.',
    sources,
    derived: Object.entries(artifacts).map(([path, value]) => {
      const bytes = Buffer.from(`${JSON.stringify(value)}\n`);
      return { path, bytes: bytes.length, sha256: sha256(bytes) };
    }),
  };
  writeFileSync(join(out, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  return manifest;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const outIndex = process.argv.indexOf('--out');
  const out = outIndex >= 0 ? resolve(process.argv[outIndex + 1]) : undefined;
  const manifest = buildData(out);
  console.log(`Exported ${manifest.derived.length} data files from ${SOURCE_COMMIT}; ${manifest.derived.reduce((n, x) => n + x.bytes, 0)} bytes.`);
}
