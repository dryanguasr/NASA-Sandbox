import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const web = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const root = path.dirname(web);
const publicRoot = path.join(web, 'public');
const manifest = JSON.parse(fs.readFileSync(path.join(publicRoot, 'media-manifest.json')));
const checksum = bytes => createHash('sha256').update(bytes).digest('hex');
const sourceBytes = (file, ref) => execFileSync('git', ['show', `${ref}:${file}`], { cwd: root, maxBuffer: 64 * 1024 * 1024 });
const walk = directory => fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
  const file = path.join(directory, entry.name);
  return entry.isDirectory() ? walk(file) : [file];
});
const existsInBuild = relative => fs.existsSync(path.join(publicRoot, relative)) || fs.existsSync(path.join(web, relative));

test('AC07/AC08/AC10: every local HTML asset and download resolves beneath the project base path', () => {
  const pages = [{ file: path.join(web, 'index.html'), route: 'index.html' },
    ...walk(publicRoot).filter(file => file.endsWith('.html')).map(file => ({ file, route: path.relative(publicRoot, file).replaceAll('\\', '/') }))];
  const missing = [];
  for (const { file, route } of pages) {
    const html = fs.readFileSync(file, 'utf8');
    for (const match of html.matchAll(/(?:href|src|poster)\s*=\s*["']([^"']+)["']/g)) {
      const href = match[1].replaceAll('&amp;', '&');
      if (/^(?:https?:|mailto:|data:|blob:|#)/i.test(href)) continue;
      assert.ok(!href.startsWith('/'), `Root-relative link breaks a project subpath: ${route} -> ${href}`);
      const url = new URL(href, `https://local.test/NASA-Sandbox/${route}`);
      assert.ok(url.pathname.startsWith('/NASA-Sandbox/'), `Link leaves project base: ${route} -> ${href}`);
      const relative = decodeURIComponent(url.pathname.slice('/NASA-Sandbox/'.length));
      if (!existsInBuild(relative)) missing.push(`${route} -> ${href}`);
    }
  }
  assert.deepEqual(missing, []);
});

test('AC06: required video manifests match packaged immutable bytes, posters, readable reports and decode evidence', () => {
  assert.equal(manifest.schema_version, 1);
  assert.deepEqual(manifest.videos.map(video => video.id).sort(), ['base', 'belva', 'replay']);
  const verification = JSON.parse(fs.readFileSync(path.join(root, 'evidence/ui_draft/media-verification.json')));
  for (const video of manifest.videos) {
    const bytes = fs.readFileSync(path.join(publicRoot, video.src));
    assert.equal(bytes.length, video.bytes);
    assert.equal(checksum(bytes), video.sha256);
    assert.equal(checksum(sourceBytes(video.source_path, video.origin_commit)), video.sha256);
    assert.equal(checksum(fs.readFileSync(path.join(publicRoot, video.poster))), video.poster_sha256);
    assert.ok(video.poster_time_s >= 0 && video.poster_time_s < video.duration_s);
    assert.ok(existsInBuild(video.report));
    assert.ok(video.summary.length > 80 && video.transcript.length > 80);
    assert.equal(video.codec, 'h264');
    assert.equal(video.audio.present, false);
    assert.equal(video.narration, 'no_audio_track');
    assert.equal(video.subtitles, null);
    const decoded = verification.videos.find(item => item.source_path === video.source_path);
    assert.equal(decoded?.sha256, video.sha256);
    assert.equal(decoded?.decode_exit_code, 0);
    assert.deepEqual(decoded?.decode_errors, []);
    assert.equal(decoded?.duration_s, video.duration_s);
  }
  const byId = Object.fromEntries(manifest.videos.map(video => [video.id, video]));
  assert.equal(byId.belva.experiment_type, 'closed_loop_gazebo');
  assert.equal(byId.replay.experiment_type, 'kinematic_replay');
  assert.equal(byId.base.experiment_type, 'gazebo_integration_synthetic');
  assert.notEqual(byId.belva.run_id, byId.replay.run_id);
});

test('AC07/AC11: raw downloads and preparation documents are exact immutable originals', () => {
  for (const item of manifest.downloads) {
    const original = sourceBytes(item.source_path, item.origin_commit);
    const packaged = fs.readFileSync(path.join(publicRoot, item.path));
    assert.equal(packaged.length, item.bytes, item.path);
    assert.equal(checksum(packaged), item.sha256, item.path);
    assert.equal(checksum(original), item.sha256, item.path);
  }
  assert.ok(existsInBuild(manifest.license));
  const prep = manifest.preparation;
  for (const key of ['interactive', 'manual', 'manual_markdown', 'checklist', 'checklist_markdown']) assert.ok(existsInBuild(prep[key]));
  const interactive = fs.readFileSync(path.join(publicRoot, prep.interactive), 'utf8');
  assert.match(interactive, /localStorage/);
  assert.match(interactive, /JSON\.stringify/);
  assert.match(interactive, /JSON\.parse/);
  assert.match(interactive, /type="file"/);
});

test('AC01/AC11: web scope leaves algorithms, pilots, worlds and scientific data unchanged from the inspected revision', () => {
  const protectedRoots = ['pilots', 'worlds', 'models', 'config', 'data'];
  const changed = execFileSync('git', ['diff', '--name-only', manifest.source_commit, '--', ...protectedRoots], { cwd: root, encoding: 'utf8' }).trim();
  assert.equal(changed, '', 'Presentation work must not alter scientific source or algorithms.');
  const scientificScripts = execFileSync('git', ['ls-tree', '-r', '--name-only', manifest.source_commit, 'scripts'], { cwd: root, encoding: 'utf8' }).trim().split('\n').filter(Boolean);
  for (const file of scientificScripts) {
    // Git normalizes text line endings in this checkout; compare the normalized
    // tracked diff rather than Windows working-tree bytes.
    assert.equal(execFileSync('git', ['diff', '--name-only', manifest.source_commit, '--', file], { cwd: root, encoding: 'utf8' }).trim(), '', file);
  }
});
