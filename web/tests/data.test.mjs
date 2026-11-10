import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, sep } from 'node:path';
import { AGENTS, SOURCE_COMMIT, buildMission, buildComparison, buildBelva, buildData, parseRecordedViewer, sourceBytes } from '../../scripts/build_web_data.mjs';

const mission = buildMission();
const comparison = buildComparison();
const belva = buildBelva();
const json = path => JSON.parse(sourceBytes(path));
const hash = data => createHash('sha256').update(data).digest('hex');

test('AC03: recorded positions, events, grids and six IDs survive extraction without recomputation', () => {
  const original = parseRecordedViewer(sourceBytes('evidence/jezero/viewer.html').toString());
  for (const field of ['trajectory', 'frames', 'events', 'mean', 'sigma', 'prior', 'reference', 'summary']) {
    assert.deepEqual(mission[field], original[field], field);
  }
  assert.deepEqual(mission.agents, AGENTS);
  assert.equal(mission.source_commit, SOURCE_COMMIT);
  assert.equal(hash(sourceBytes('data/jezero/terrain.npz')), mission.metadata.terrain_sha256);
  assert.equal(mission.trajectory.at(-1).time_s, mission.summary.duration_s);
  assert.equal(Object.values(mission.summary.agents).filter(a => a.returned).length, 6);
  assert.equal(mission.display_grid.scientific_interpolation, false);
});

test('AC03: target detection boundaries and task precedence derive from actual events', () => {
  assert.deepEqual(mission.sites.filter(s => s.detected_s <= 84), []);
  assert.deepEqual(mission.sites.filter(s => s.detected_s <= 85).map(s => s.id), ['S2']);
  for (const site of mission.sites) {
    const detected = mission.events.find(e => e.event === 'site_detected' && e.site === site.id);
    const inspection = mission.events.find(e => e.event === 'completed' && e.task === `inspect:${site.id}`);
    const sampleCreation = mission.events.find(e => e.event === 'task_created' && e.task === `sample:${site.id}`);
    const sampleAssignment = mission.events.find(e => e.event === 'assigned' && e.task === `sample:${site.id}`);
    assert.equal(site.detected_s, detected.time_s);
    assert.ok(sampleCreation.time_s >= inspection.time_s);
    assert.ok(sampleAssignment.time_s >= inspection.time_s);
  }
  for (const frame of mission.frames) {
    assert.deepEqual(frame.seen_sites, mission.sites.filter(s => s.detected_s <= frame.time_s).map(s => s.id).sort());
    const completed = mission.events.filter(e => e.event === 'completed' && e.kind === 'sample' && e.time_s <= frame.time_s).length;
    assert.equal(frame.completed_samples, completed);
  }
});

test('AC02: seven guided milestones reference existing ordered events', () => {
  assert.deepEqual(mission.milestones.map(m => m.time_s), [0, 40, 85, 525, 920, 1335, 1930]);
  for (const milestone of mission.milestones) assert.equal(milestone.time_s, mission.events[milestone.event_index].time_s);
});

test('AC03: task timestamps and final assignments match their own recorded event chain', () => {
  assert.deepEqual(mission.tasks, json('evidence/jezero/tasks.json'));
  for (const task of mission.tasks) {
    const events = mission.events.filter(e => e.task === task.id);
    const assignments = events.filter(e => e.event === 'assigned');
    for (const event of assignments) assert.ok(event.time_s >= task.created_s, task.id);
    if (task.state === 'done') {
      const completed = events.find(e => e.event === 'completed');
      assert.equal(completed?.time_s, task.completed_s, task.id);
      assert.equal(assignments.at(-1)?.agent, task.assigned_to, task.id);
      assert.equal(completed.agent, task.assigned_to, task.id);
    }
    if (task.dependency) {
      const parent = mission.tasks.find(t => t.id === task.dependency);
      assert.ok(parent && parent.completed_s <= task.created_s, task.id);
    }
  }
});

test('AC05: compared metrics are pinned source values with compatible conditions and explicit missing trajectory', () => {
  const original = json('evidence/jezero/benchmark_summary.json');
  assert.deepEqual(comparison.policies, original.policies);
  assert.deepEqual(comparison.seeds, [7, 11, 19]);
  assert.equal(comparison.terrain_sha256, mission.summary.terrain_sha256);
  assert.equal(comparison.policies.information_hungarian.t80_s.mean, 320);
  assert.equal(comparison.policies.nearest_greedy.t80_s.mean, 440);
  assert.equal(comparison.policies.information_hungarian.duration_s.mean, 1930);
  assert.equal(comparison.policies.nearest_greedy.duration_s.mean, 1660);
  assert.ok(comparison.policies.information_hungarian.drone_distance_m.mean > comparison.policies.nearest_greedy.drone_distance_m.mean);
  assert.equal(comparison.trajectory_availability.nearest_greedy, null);
  assert.equal(comparison.mode, 'recorded_final_metrics');
});

test('Belva closed-loop video run stays distinct from 2.5D and consistency repetitions', () => {
  assert.deepEqual(belva.result, json('evidence/jezero_belva/result.json'));
  assert.deepEqual(belva.seedComparison, json('evidence/jezero_belva/seed-comparison.json'));
  assert.equal(belva.execution_type, 'gazebo_closed_loop');
  assert.equal(belva.result.duration_s, 453.77);
  assert.equal(belva.result.returns, 6);
  assert.equal(belva.seedComparison.six_returns, 5);
  assert.ok(belva.seedComparison.runs.every(r => r.verified_count === 6));
  assert.notEqual(belva.result.duration_s, belva.seedComparison.runs[0].duration_s);
  assert.notEqual(belva.result.terrain_sha256, mission.summary.terrain_sha256);
  assert.equal(belva.trajectory, null);
});

test('AC08: missing payload and incompatible agent/grid inputs fail closed', () => {
  assert.throws(() => parseRecordedViewer('<html>Missing payload</html>'), /missing/);
  const original = parseRecordedViewer(sourceBytes('evidence/jezero/viewer.html').toString());
  original.trajectory[0].positions.drone_3 = original.trajectory[0].positions.drone_2;
  assert.throws(() => parseRecordedViewer(`const D=${JSON.stringify(original)};\n`), /agents/);
  delete original.trajectory[0].positions.drone_3;
  original.mean[0] = '';
  assert.throws(() => parseRecordedViewer(`const D=${JSON.stringify(original)};\n`), /grid/);
});

test('AC01/AC11: deterministic output and download hashes equal immutable Git bytes', () => {
  const temporaryRoot = resolve(tmpdir());
  const directory = mkdtempSync(join(temporaryRoot, 'mission-data-test-'));
  try {
    const first = buildData(directory);
    const firstManifest = readFileSync(join(directory, 'manifest.json'));
    const second = buildData(directory);
    assert.deepEqual(first, second);
    assert.deepEqual(firstManifest, readFileSync(join(directory, 'manifest.json')));
    for (const source of first.sources) {
      assert.equal(source.sha256, hash(sourceBytes(source.path)));
      if (source.download) assert.equal(hash(readFileSync(join(directory, source.download))), source.sha256);
    }
    for (const output of first.derived) assert.equal(hash(readFileSync(join(directory, output.path))), output.sha256);
    assert.ok(first.derived.reduce((n, o) => n + o.bytes, 0) < 3_000_000);
  } finally {
    if (!resolve(directory).startsWith(`${temporaryRoot}${sep}mission-data-test-`)) throw new Error('Unsafe temporary directory');
    rmSync(directory, { recursive: true, force: true });
  }
});
