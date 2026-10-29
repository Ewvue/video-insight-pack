// Paste into a YouTube watch page (DevTools or a browser automation "run JS" call).
// Draws video frames onto a full-viewport canvas overlay so a screenshot captures them.
// See references/frame-capture.md for the workflow and its caveats.
(() => {
  const player = () => document.getElementById('movie_player');
  const video = () => player().querySelector('video');
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function overlay() {
    let c = document.getElementById('__ov');
    if (!c) {
      c = document.createElement('canvas');
      c.id = '__ov';
      c.style.cssText = 'position:fixed;inset:0;z-index:2147483647;width:100vw;height:100vh;background:#000';
      document.body.appendChild(c);
    }
    c.style.display = 'block';
    return c;
  }
  window.__hide = () => { const c = document.getElementById('__ov'); if (c) c.style.display = 'none'; };

  // Wait out ads (up to 35 s), clicking a skip button when one shows.
  window.__noad = async () => {
    const p = player(); const t0 = Date.now();
    while (p.classList.contains('ad-showing') && Date.now() - t0 < 35000) {
      p.mute(); p.playVideo();
      const s = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button-modern, .ytp-ad-skip-button');
      if (s) s.click();
      await sleep(700);
    }
    p.pauseVideo();
    return !p.classList.contains('ad-showing');
  };

  // Land on time t with a freshly decoded frame. Returns true when within 0.6 s.
  window.__seek = async (t) => {
    const p = player(), v = video(), s = Math.max(0, t - 0.6);
    const has = () => { for (let i = 0; i < v.buffered.length; i++) if (v.buffered.start(i) <= s && v.buffered.end(i) > t + 0.5) return true; return false; };
    if (!has()) { p.seekTo(s, true); p.pauseVideo(); const t0 = Date.now(); while (!has() && Date.now() - t0 < 10000) await sleep(150); }
    v.currentTime = s;
    await new Promise((r) => { v.addEventListener('seeked', r, { once: true }); setTimeout(r, 4000); });
    v.muted = true; v.play().catch(() => {});
    const t0 = Date.now(); while (v.currentTime < t && Date.now() - t0 < 3000) await sleep(30);
    v.pause(); await sleep(100);
    return Math.abs(v.currentTime - t) < 0.6;
  };

  // Full-resolution frame on the overlay; take a screenshot right after.
  window.__cap = async (t) => {
    await window.__noad();
    try { player().setPlaybackQualityRange('hd1080', 'hd1080'); } catch (e) {}
    const ok = await window.__seek(t), v = video(), c = overlay(), d = devicePixelRatio;
    c.width = innerWidth * d; c.height = innerHeight * d;
    const g = c.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height);
    const k = Math.min(c.width / v.videoWidth, c.height / v.videoHeight), w = v.videoWidth * k, h = v.videoHeight * k;
    g.imageSmoothingQuality = 'high'; g.drawImage(v, (c.width - w) / 2, (c.height - h) / 2, w, h);
    return { ok, t: v.currentTime, width: v.videoWidth };
  };

  // Contact sheet of chosen seconds (8 columns). Slow: run without await and poll window.__done.
  window.__sheetTimes = async (times) => {
    window.__done = false;
    const v = video(), c = overlay(), W = innerWidth, H = innerHeight; c.width = W; c.height = H;
    const g = c.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    const cols = 8, cw = W / cols, ch = cw * 9 / 16;
    for (let i = 0; i < times.length; i++) {
      await window.__noad(); const ok = await window.__seek(times[i]);
      const x = (i % cols) * cw, y = Math.floor(i / cols) * ch;
      try { g.drawImage(v, x + 1, y + 1, cw - 2, ch - 2); } catch (e) {}
      g.fillStyle = 'rgba(0,0,0,.75)'; g.fillRect(x + 1, y + 1, 64, 18);
      g.fillStyle = ok ? '#ff0' : '#f44'; g.font = 'bold 14px sans-serif'; g.fillText(String(times[i]), x + 4, y + 15);
    }
    window.__done = true;
  };

  // Whole-video overview from YouTube's storyboard sprites (no seeking). from = tile index (10 s each at level 2).
  const sbCache = {};
  window.__storyboard = async (from = 0, level = 2) => {
    const spec = player().getPlayerResponse().storyboards.playerStoryboardSpecRenderer.spec.split('|');
    const base = spec[0], L = spec[level + 1].split('#');
    const [tw, th, count, sc, sr, interval] = L.slice(0, 6).map(Number), sig = L[7], per = sc * sr;
    const load = (n) => sbCache[n] || (sbCache[n] = new Promise((res) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null); im.src = base.replace('$L', String(level)).replace('$N', 'M' + n) + '&sigh=' + sig; }));
    const c = overlay(), W = innerWidth, H = innerHeight; c.width = W; c.height = H;
    const g = c.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
    const cols = 12, cw = W / cols, ch = cw * 9 / 16, rows = Math.floor(H / ch);
    for (let k = 0; k < cols * rows; k++) {
      const f = from + k; if (f >= count) break;
      const im = await load(Math.floor(f / per)); if (!im) continue;
      const j = f % per, x = (k % cols) * cw, y = Math.floor(k / cols) * ch;
      g.drawImage(im, (j % sc) * tw, Math.floor(j / sc) * th, tw, th, x + 1, y + 1, cw - 2, ch - 2);
      const t = Math.round(f * interval / 1000), hh = Math.floor(t / 3600), mm = Math.floor(t % 3600 / 60), ss = String(t % 60).padStart(2, '0');
      const lab = hh ? hh + ':' + String(mm).padStart(2, '0') + ':' + ss : mm + ':' + ss;
      g.fillStyle = 'rgba(0,0,0,.75)'; g.fillRect(x + 1, y + 1, hh ? 56 : 44, 15);
      g.fillStyle = '#ff0'; g.font = 'bold 12px sans-serif'; g.fillText(lab, x + 3, y + 13);
    }
    return { shown: cols * rows, next: from + cols * rows, total: count };
  };
  return 'browser-capture helpers ready';
})();
