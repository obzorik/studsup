/* ============================================
   StudsUp.com — Shared JavaScript
   All pages import this file
   ============================================ */

'use strict';

// ── NAV: highlight current page ──────────────────────────────────────────────
(function highlightNav() {
  const page = location.pathname.split('/').pop().replace('.html','');
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = (link.getAttribute('href') || '').replace('.html','').replace('../pages/','').replace('pages/','');
    if (href && page.includes(href)) link.classList.add('active');
  });
})();

// ── TOAST ────────────────────────────────────────────────────────────────────
function toast(msg, type = 'default') {
  const existing = document.querySelectorAll('.toast-el');
  existing.forEach(el => el.remove());
  const el = document.createElement('div');
  el.className = 'toast-el';
  if (type === 'error')   el.style.background = '#CC0000';
  if (type === 'success') el.style.cssText += ';background:#1a1a2e;color:#22c55e';
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 380); }, 2400);
}

// ── MODAL ────────────────────────────────────────────────────────────────────
function openModal(id)  { const el = document.getElementById(id); if (el) el.classList.add('open'); }
function closeModal(id) { const el = document.getElementById(id); if (el) el.classList.remove('open'); }

// Close modals on backdrop click
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-bg')) e.target.classList.remove('open');
});

// ── TABS ─────────────────────────────────────────────────────────────────────
/**
 * Simple tab switcher.
 * Usage: switchTab('tabName', clickedButton, ['tab1','tab2',...], 'prefix-')
 */
function switchTab(name, btn, allNames, prefix = 'tab-') {
  allNames.forEach(t => {
    const el = document.getElementById(prefix + t);
    if (el) el.style.display = t === name ? '' : 'none';
  });
  if (btn) {
    const group = btn.closest('[data-tabgroup]');
    const btns  = group ? group.querySelectorAll('[data-tab]') : document.querySelectorAll('[data-tab]');
    btns.forEach(b => b.classList.remove('active', 'on'));
    btn.classList.add('active');
    btn.classList.add('on');
  }
}

// ── DOWNLOAD PROGRESS ────────────────────────────────────────────────────────
/**
 * Simulates a download with animated progress.
 * @param {string} filename - shown in the UI
 * @param {function} onDone  - called when animation finishes
 */
function simulateDownload(filename, onDone) {
  const existing = document.getElementById('_dlProgress');
  if (existing) existing.remove();

  const wrap = document.createElement('div');
  wrap.id = '_dlProgress';
  wrap.style.cssText = `position:fixed;bottom:22px;right:22px;background:#fff;border:1px solid #e8e7e2;border-radius:12px;padding:16px 20px;z-index:600;min-width:260px;box-shadow:0 8px 28px rgba(0,0,0,.12)`;
  wrap.innerHTML = `
    <div style="font-size:13px;font-weight:700;margin-bottom:8px;color:#1a1a1a">⬇️ ${filename}</div>
    <div style="height:6px;background:#f0f0ec;border-radius:3px;overflow:hidden;margin-bottom:6px">
      <div id="_dlFill" style="height:6px;background:#FFD700;border-radius:3px;width:0;transition:width .08s linear"></div>
    </div>
    <div id="_dlPct" style="font-size:11px;color:#888">0%</div>
  `;
  document.body.appendChild(wrap);

  let p = 0;
  const fill = document.getElementById('_dlFill');
  const pct  = document.getElementById('_dlPct');
  const iv = setInterval(() => {
    p += Math.round(4 + Math.random() * 9);
    if (p >= 100) {
      p = 100;
      clearInterval(iv);
      fill.style.background = '#22c55e';
      pct.textContent = '✅ Complete';
      if (typeof onDone === 'function') onDone();
      setTimeout(() => wrap.remove(), 1800);
    }
    fill.style.width  = p + '%';
    pct.textContent   = p < 100 ? p + '%' : pct.textContent;
  }, 70);
}

// ── FILTER / SEARCH HELPER ───────────────────────────────────────────────────
/**
 * Live-filter a list of elements by text content.
 * @param {string} query    - search string
 * @param {string} selector - CSS selector for items
 */
function liveFilter(query, selector) {
  const q = query.toLowerCase().trim();
  document.querySelectorAll(selector).forEach(el => {
    el.style.display = (!q || el.textContent.toLowerCase().includes(q)) ? '' : 'none';
  });
}

// ── CHART.JS COLOUR HELPERS ──────────────────────────────────────────────────
const CHART_COLORS = {
  yellow : '#FFD700',
  dark   : '#1a1a2e',
  red    : '#FF4444',
  green  : '#22c55e',
  blue   : '#3b82f6',
  purple : '#8b5cf6',
};

// ── PAGE-SPECIFIC INIT HOOK ──────────────────────────────────────────────────
// Each page can define window.pageInit() and it will be called on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  if (typeof window.pageInit === 'function') window.pageInit();
});
