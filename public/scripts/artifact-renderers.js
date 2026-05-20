// Higgins 2.0 — Artifact renderers. REQ-002 Phase 3.
//
// Type-dispatched render functions for the artifact window body.
//   markdown → marked + DOMPurify (CDN)
//   code     → highlight.js (CDN), wrapped in <pre><code>
//   html     → sandboxed iframe with srcdoc
//   table    → renders a markdown table via the markdown renderer
//   docx/pptx/remotion-video → placeholder (Phase 4 server-renders)
//
// Libraries are lazy-loaded so a markdown artifact doesn't pay for hljs.

const CDN = {
  marked: 'https://cdn.jsdelivr.net/npm/marked@13.0.3/+esm',
  dompurify: 'https://cdn.jsdelivr.net/npm/dompurify@3.1.6/+esm',
  hljs: 'https://cdn.jsdelivr.net/npm/highlight.js@11.10.0/+esm',
};

let markedMod = null, purifyMod = null, hljsMod = null;

async function ensureMarkdown() {
  if (!markedMod) markedMod = await import(CDN.marked);
  if (!purifyMod) purifyMod = await import(CDN.dompurify);
  return { marked: markedMod.marked, purify: purifyMod.default };
}

async function ensureHljs() {
  if (!hljsMod) hljsMod = await import(CDN.hljs);
  return hljsMod.default;
}

function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function bodyClass(type) {
  return 'aw-body aw-' + type;
}

function extractContent(opts) {
  // tool inputs land as raw strings in `content`, but Supabase versions
  // store as { body, language } — accept either shape.
  if (opts == null) return { body: '', language: undefined };
  if (typeof opts.content === 'string') return { body: opts.content, language: opts.language };
  if (opts.content && typeof opts.content === 'object') {
    return { body: opts.content.body ?? '', language: opts.content.language ?? opts.language };
  }
  return { body: '', language: opts.language };
}

export async function renderArtifact(bodyEl, type, opts) {
  bodyEl.className = bodyClass(type);
  const { body, language } = extractContent(opts);

  try {
    switch (type) {
      case 'markdown':
      case 'table': {
        const { marked, purify } = await ensureMarkdown();
        const raw = marked.parse(body || '');
        bodyEl.innerHTML = purify.sanitize(raw);
        return;
      }
      case 'code': {
        const hljs = await ensureHljs();
        const lang = (language || '').trim();
        const safe = escapeHtml(body || '');
        let highlighted = safe;
        try {
          highlighted = lang && hljs.getLanguage(lang)
            ? hljs.highlight(body || '', { language: lang, ignoreIllegals: true }).value
            : hljs.highlightAuto(body || '').value;
        } catch (err) {
          console.warn('[higgins/renderers] hljs failed', err);
        }
        bodyEl.innerHTML = `<pre><code class="hljs language-${escapeHtml(lang)}">${highlighted}</code></pre>`;
        return;
      }
      case 'html': {
        // Sandboxed iframe — allow scripts so embedded JS works, but no
        // same-origin → no cookies, no localStorage access, no nav.
        bodyEl.innerHTML = '';
        const frame = document.createElement('iframe');
        frame.setAttribute('sandbox', 'allow-scripts');
        frame.srcdoc = body || '<!doctype html><meta charset="utf-8">';
        bodyEl.appendChild(frame);
        return;
      }
      case 'docx':
      case 'pptx': {
        const blobUrl = opts?.blobUrl;
        const ext = type;
        const slug = opts?.slug || 'artifact';
        const version = opts?.version || 1;
        const downloadName = `${slug}-v${version}.${ext}`;

        if (blobUrl) {
          bodyEl.innerHTML = `
            <div class="aw-placeholder">
              <svg class="aw-ph-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              <div><strong>${escapeHtml(ext.toUpperCase())}</strong> ready to download.</div>
              <div class="aw-ph-note">Server-rendered with Synergi branding · v${version}</div>
              <a href="${escapeHtml(blobUrl)}" download="${escapeHtml(downloadName)}"
                 style="display:inline-flex;align-items:center;gap:6px;margin-top:12px;padding:8px 14px;background:var(--agent-accent);color:white;border-radius:var(--radius-md);text-decoration:none;font-size:0.85rem;font-weight:500;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Download ${escapeHtml(ext.toUpperCase())}
              </a>
              <details style="margin-top:14px;max-width:340px;text-align:left;font-size:0.7rem;color:var(--text-muted);">
                <summary style="cursor:pointer;">Source</summary>
                <pre style="white-space:pre-wrap;max-height:160px;overflow:auto;margin-top:6px;font-size:0.7rem;">${escapeHtml((body || '').slice(0, 1200))}${(body || '').length > 1200 ? '\n…' : ''}</pre>
              </details>
            </div>
          `;
        } else {
          bodyEl.innerHTML = `
            <div class="aw-placeholder">
              <svg class="aw-ph-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              <div><strong>${escapeHtml(ext.toUpperCase())}</strong> render failed.</div>
              <div class="aw-ph-note">No blob URL was returned. Check server logs.</div>
            </div>
          `;
        }
        return;
      }
      case 'remotion-video': {
        bodyEl.innerHTML = `
          <div class="aw-placeholder">
            <svg class="aw-ph-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polygon points="23 7 16 12 23 17 23 7"/>
              <rect x="1" y="5" width="15" height="14" rx="2"/>
            </svg>
            <div><strong>Remotion video</strong> render lands in v2 (REQ-002 Phase 7).</div>
            <div class="aw-ph-note">${escapeHtml((body || '').slice(0, 280))}${(body || '').length > 280 ? '…' : ''}</div>
          </div>
        `;
        return;
      }
      default:
        bodyEl.textContent = body || '';
    }
  } catch (err) {
    console.error('[higgins/renderers] render failed', err);
    bodyEl.innerHTML = `<div style="color:var(--status-danger);font-size:0.8rem">Render error: ${escapeHtml(err?.message || String(err))}</div>`;
  }
}
