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
      case 'pptx':
      case 'remotion-video': {
        bodyEl.innerHTML = `
          <div class="aw-placeholder">
            <svg class="aw-ph-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <div><strong>${escapeHtml(type.toUpperCase())}</strong> render lands in Phase 4.</div>
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
