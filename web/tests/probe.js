/* Test-only instrumentation. Never copied into the production artifact. */
(() => {
  const mode = new URL(location.href).searchParams.get('mode') || 'normal';
  window.__qa = {errors:[], rejections:[], consoleErrors:[], fetches:[], started:performance.now(), cspViolations:[]};
  addEventListener('error', e => window.__qa.errors.push({message:e.message || 'resource error', source:e.filename || e.target?.src || e.target?.href || null}));
  addEventListener('unhandledrejection', e => window.__qa.rejections.push(String(e.reason?.message || e.reason)));
  addEventListener('securitypolicyviolation', e => window.__qa.cspViolations.push({blocked:e.blockedURI, directive:e.effectiveDirective}));
  const originalConsole = console.error.bind(console);
  console.error = (...args) => {window.__qa.consoleErrors.push(args.map(String).join(' ')); originalConsole(...args);};
  const nativeFetch = fetch.bind(window);
  window.fetch = async (input, options) => {
    const url = new URL(typeof input === 'string' ? input : input.url, document.baseURI);
    const start = performance.now();
    let response;
    if (url.pathname.endsWith('/data/mission.json') && mode === 'missing') response = new Response('Missing test fixture', {status:404});
    else {
      response = await nativeFetch(input, options);
      if (url.pathname.endsWith('/data/mission.json') && mode === 'incompatible') {
        const data = await response.clone().json(); data.schema_version = 999;
        response = new Response(JSON.stringify(data), {headers:{'Content-Type':'application/json'}});
      }
      if (url.pathname.endsWith('/media-manifest.json') && mode === 'missing-video') {
        const data = await response.clone().json(); data.videos[0].src = 'media/__qa_absent_video__.mp4';
        response = new Response(JSON.stringify(data), {headers:{'Content-Type':'application/json'}});
      }
    }
    window.__qa.fetches.push({url:url.pathname, status:response.status, duration_ms:performance.now()-start});
    return response;
  };
})();
