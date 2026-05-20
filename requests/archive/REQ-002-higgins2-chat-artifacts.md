# REQ-002 — Higgins 2.0 Chat + Floating Artifact Windows

**Owner:** JB Herrera
**Drafted by:** Higgins
**Date:** 2026-05-19
**Status:** ✅ Completed 2026-05-19 — Phases 0–6 shipped and live. Final commit: REQ-002 Phase 6 (de30c0c).
**Project:** ai-tools (`public/higgins2.html`, new `api/chat.ts`, `db/higgins_schema.sql`)
**Depends on / related:** REQ-001 (Skills Governance Layer) — this REQ ships chat first; skills hook-up is REQ-001 Phase 4.

---

## 1. Problem

`/higgins2` is a 2,030-line static prototype. It looks like Higgins, talks like a mock — `sendMessage()` is a `setTimeout()` returning a canned OKR response, and "artifacts" are hardcoded `canvas-block` divs in a single scrollable column. There is no Claude wiring, no streaming, no persistence, and no way for the agent to spawn a working deliverable in the workspace.

The prototype has earned a real backend. JB wants Higgins 2.0 to be the *daily driver* AI surface — branded, voice-aligned, capable of producing real artifacts (docs, decks, code, eventually video), all in floating windows that behave like a workspace instead of a chat scroll.

## 2. Strategic intent

Higgins 2.0 becomes the front door for JB's AI workflow — distinct from ChatGPT/Claude.ai because it (a) speaks in JB's Visionary Pragmatist voice by default, (b) outputs to Synergi-branded artifacts JB can immediately ship or hand to clients, and (c) eventually composes governed skills (REQ-001) on top of the same chat surface. This is the demo JB shows when explaining what "AI augmenting human brilliance" looks like in practice.

## 3. Users

| User | Job-to-be-done | Frequency |
|---|---|---|
| **JB (primary)** | Daily AI driver — chat, draft docs/decks, generate code, iterate on artifacts. | Daily |
| **Future: Synergi/IDB clients** | See a live demo of values-aligned AI assistance during sales calls. | Per pitch |
| **Future: i360 deployments** | Per-client Higgins instance with that client's voice + skill set. | Per onboarding |

V1 ships single-user (JB) only. Auth is a shared bearer token, not user accounts.

## 4. Goals & success metrics

| Goal | Metric | Target |
|---|---|---|
| Chat feels production-grade | First-token latency from send → bubble | < 1.5s p50 |
| Artifacts feel like a workspace, not a chat | Multiple artifact windows open + reorderable simultaneously | ≥ 4 at once with no jank |
| Conversations survive reload | Refresh restores the active conversation + open artifact windows | 100% |
| DocX/PPTX exports usable as-is | Generated file opens cleanly in Word / PowerPoint | 100% (manual QA on 5 samples) |
| Voice consistency | Spot-check 10 responses against the Visionary Pragmatist rubric | 9/10 pass |
| Higgins replaces ad-hoc chats | % of JB's daily AI usage that runs through `/higgins2` after 30 days | ≥ 50% |

## 5. In scope (v1)

1. **Streaming chat backend.** New Node/TS Vercel Function `api/chat.ts` using **Vercel AI SDK v6 + AI Gateway**. Provider string `"anthropic/claude-opus-4-7"` with Sonnet 4.6 → GPT-5 fallback configured at the Gateway.
2. **Real frontend wiring.** Replace `sendMessage()` mock; stream tokens into the active message bubble; render tool calls as artifact events.
3. **Floating artifact windows.** Refactor `canvas-block` into a reusable `ArtifactWindow` class — each window drag/resize/minimize/close/z-stack. Multiple windows coexist. Reuses the existing `.higgins-card` drag/resize patterns.
4. **Artifact types v1.** Six types:
   - **Client-side render** (content streamed inline): `markdown`, `code` (highlight.js), `html` (sandboxed iframe), `table`.
   - **Server-side render → Vercel Blob → signed URL**: `docx` (`docx` npm), `pptx` (`pptxgenjs` npm). Window shows preview + Download button.
5. **Tool schema.** Two tools: `create_artifact({ id, type, title, content })` and `update_artifact({ id, patch })`. Stable model-chosen slug IDs so updates target an existing window.
6. **Higgins identity system prompt.** Addresses JB by name, Visionary Pragmatist voice, current date injected per turn, decision heuristic for artifact-vs-inline.
7. **Persistence.** Supabase tables `higgins_conversations`, `higgins_messages`, `higgins_artifacts`, `higgins_artifact_versions`, `higgins_memories`. Conversations + artifacts restore on reload.
8. **Memory layer foundation.** `higgins_memories` table created in v1 so the foundation exists from day one. Active summarization + memory-injection wired in Phase 5 (see §9).
9. **Auth.** Single-user. `HIGGINS_API_TOKEN` bearer check on `/api/chat`. Frontend stores token in `localStorage` on first prompt.

## 6. Out of scope (v2+)

- **Remotion video artifacts.** Chromium-based renders bust the 60–300s function budget. Defer to v2 via `@remotion/lambda` or Vercel Sandbox. v1 ships the `ArtifactWindow` interface ready to slot it in.
- **Skills integration / agent selection.** Covered by REQ-001 Phase 4.
- **Voice input/output.** Mic UI stays visually, but no wiring.
- **Multi-user / per-client instances.**
- **Public sharing of artifacts.** All artifacts are JB-private signed URLs in v1.
- **In-window editing of artifacts.** Read-only render; iterate by asking Higgins.
- **Cross-conversation artifact reuse / library view.**

## 7. MVP cut — the smallest version that closes the loop

Three things must all be true:

1. **Real chat.** JB types, Claude streams back in Higgins voice, conversation persists across refresh.
2. **Floating artifacts.** Claude opens at least `markdown`, `code`, and `html` artifacts in their own draggable windows; can update them via `update_artifact`.
3. **One heavy export proves the pattern.** Either `docx` *or* `pptx` end-to-end: tool call → server render → Blob upload → window shows Download button → JB downloads a clean file.

Everything else is layered on top.

## 8. Schema deltas

New tables (additive — no touches to existing `skill_*` tables):

```sql
higgins_conversations (
  id              uuid primary key,
  user_id         text not null default 'jb',
  title           text,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
)

higgins_messages (
  id              uuid primary key,
  conversation_id uuid references higgins_conversations(id) on delete cascade,
  role            text check (role in ('user','assistant','system','tool')),
  parts           jsonb not null,                -- AI SDK v6 UIMessage shape
  created_at      timestamptz default now()
)

higgins_artifacts (
  id              uuid primary key,
  conversation_id uuid references higgins_conversations(id) on delete cascade,
  slug            text not null,                 -- model-chosen, stable per conversation
  type            text not null,                 -- markdown|code|html|table|docx|pptx|remotion-video
  title           text,
  current_version int not null default 1,
  blob_url        text,                          -- populated for docx/pptx server-renders
  created_at      timestamptz default now(),
  updated_at      timestamptz default now(),
  unique (conversation_id, slug)
)

higgins_artifact_versions (
  id              uuid primary key,
  artifact_id     uuid references higgins_artifacts(id) on delete cascade,
  version_no      int not null,
  content         jsonb not null,                -- inline content (markdown/code/etc.)
  blob_url        text,                          -- if server-rendered this version
  created_at      timestamptz default now(),
  unique (artifact_id, version_no)
)

higgins_memories (
  id              uuid primary key,
  user_id         text not null default 'jb',
  conversation_id uuid references higgins_conversations(id) on delete set null,
  kind            text not null,                 -- 'summary' | 'fact' | 'preference' | 'project' | 'reference'
  scope           text not null default 'global',-- 'global' | 'conversation' | 'project'
  title           text,
  content         text not null,                 -- distilled prose, retrieval-ready
  source_message_ids uuid[],                     -- which messages this memory was distilled from
  importance      smallint default 3,            -- 1 (low) … 5 (critical), for retrieval ranking
  embedding       vector(1536),                  -- pgvector for semantic recall
  created_at      timestamptz default now(),
  expires_at      timestamptz                    -- null = permanent
)
```

Memory schema mirrors the global-CLAUDE.md memory taxonomy (`user`/`feedback`/`project`/`reference`) plus a `summary` kind for rolling conversation digests. Embeddings are populated lazily — Phase 5 wires retrieval.

Single shared `user_id='jb'` constant for v1. RLS deferred to multi-user phase.

## 9. Phased delivery plan

| Phase | Deliverable | Effort |
|---|---|---|
| **0 — Node/TS coexistence** | Root `package.json` + `tsconfig.json`; `api/chat.ts` stub streaming a fixed string via `toUIMessageStreamResponse()`. Confirm `vercel dev` runs Python + Node side-by-side. | 1 session |
| **1 — Schema + persistence** | Apply `db/higgins_schema.sql`. New `api/lib/higginsRepo.ts` + `api/lib/auth.ts` (bearer token). Smoke-test write/read. | 1 session |
| **2 — Real streaming chat (no artifacts)** | `api/chat.ts` calls `streamText({ model: 'anthropic/claude-opus-4-7', system: HIGGINS_SYSTEM_PROMPT })`. Replace `sendMessage()` mock with vanilla-JS data-stream parser in `public/scripts/higgins-stream.js`. Persist messages. Refresh restores history. | 1–2 sessions |
| **3 — Floating artifact windows (client-side types)** | Extract drag/resize into `public/scripts/artifact-window.js` + `public/styles/artifact-window.css`. New `public/scripts/artifact-renderers.js` for markdown/code/html/table. Tool definitions in `api/lib/artifactTools.ts`. Remove hardcoded `canvas-block` demo. | 2 sessions |
| **4 — DocX + PPTX server-render** | Install `docx`, `pptxgenjs`, `@vercel/blob`. Tool `execute` for `docx`/`pptx` types renders → uploads to Blob → returns signed URL. Window shows download button. | 1–2 sessions |
| **5 — Memory layer** | Token-budget monitor on each turn. When conversation crosses **70% of model context window**, trigger a summarization tool call → distill recent turns into a `summary`-kind memory row → drop the summarized turns from the active window, leaving the summary in place. Add `recall_memory` tool so Higgins can pull relevant memories into context by semantic match. Memory write tools (`save_memory`, `forget_memory`) so Higgins can persist facts/preferences/projects on JB's command. pgvector enabled in Supabase. | 2 sessions |
| **6 — Polish + voice QA** | Tune system prompt against Visionary Pragmatist rubric. Tile-on-spawn artifact placement. Conversation list sidebar (lightweight). Error/cancel UX. Memory inspector UI on `/higgins2/memories`. | 1 session |
| **7 — Remotion (v2)** | `@remotion/lambda` or Vercel Sandbox path for `remotion-video` artifacts. **Out of v1 scope.** | Separate REQ |

**Total to v1-shipped: 9–11 working sessions.**

## 10. Open decisions

| # | Question | Recommendation | Status |
|---|---|---|---|
| 1 | Artifact ID generation: model-chosen slugs or server UUIDs? | Model-chosen slugs (better debug ergonomics, model can refer to "the board-deck artifact"). | **Approved 2026-05-19** |
| 2 | Context window strategy | **Summary + dedicated memory store.** Schema lands in v1 (Phase 1); active summarization + retrieval wired in Phase 5. Trigger summary at 70% of context window. Memories live in `higgins_memories` (Supabase + pgvector), not in the LLM. Five memory kinds: `summary`, `fact`, `preference`, `project`, `reference`. | **Approved 2026-05-19** |
| 3 | Streaming partial artifact content | Default plan: stream `tool-input-delta` into the window if AI SDK v6 surfaces it cleanly. Fall back to "open window on tool completion" if brittle. Final call made when Phase 3 implementation begins. | **Deferred to Phase 3 implementation** |
| 4 | DocX/PPTX styling — start from Synergi brand or generic? | Synergi brand from day one: colors `#77bde0/#b78bd3/#dc9171`, Roboto/Poppins. One template per type for v1. | **Approved 2026-05-19** |
| 5 | Conversation sidebar in v1? | Yes — minimal "recent conversations" list in Phase 6. Refresh-survival is meaningless without a way to find old ones. | **Approved 2026-05-19** |
| 6 | Error/cancellation UX | "Stop" button on the input bar that aborts the fetch; auto-retry on Gateway provider failover; surface tool-call failures inline ("Couldn't open the artifact — try again?"). | **Approved 2026-05-19** |

## 11. Risks

| Risk | Mitigation |
|---|---|
| AI SDK v6 UI message stream protocol assumes React clients — vanilla JS parser is brittle | Write `higgins-stream.js` as a thin line-buffered JSON parser against the documented part types. If unstable, fall back to `toTextStreamResponse()` + a separate SSE channel for tool events. |
| Mixed Python + Node runtimes in `api/` cause Vercel build confusion | `vercel.json` per-file `runtime` declarations; smoke-test `vercel dev` in Phase 0 before any other work. |
| DocX/PPTX outputs look amateurish, undermining the "shippable artifact" claim | Build one strong template per type, design-token-aligned, before declaring v1 done. QA against 5 real prompts. |
| Higgins voice drifts toward generic LLM tone | System prompt + Phase 5 voice-rubric QA. Open Brain capture of any off-voice responses for prompt iteration. |
| Server-rendered artifacts (docx/pptx) tie up function time and hit 60s `maxDuration` | Pure-Node renderers finish in 1–3s; well under budget. Monitor in production; bump to 300s Fluid Compute default if any single render exceeds 30s. |
| Bearer-token-only auth leaks via shared browser | Token entered once per device, stored in `localStorage`. Acceptable for single-user JB-only v1. Revisit when adding clients. |
| Streaming + concurrent artifact opens make `higgins2.html` unmanageable | Phase 3 extracts artifact logic to `public/scripts/*.js` modules. Keep `higgins2.html` as orchestration only. |
| Summarization loses important detail; Higgins "forgets" things JB said | Source message IDs preserved on every memory row — full original turns recoverable from `higgins_messages`. Importance scoring + JB-driven `save_memory`/`forget_memory` give override control. |
| Memory retrieval pulls in irrelevant context, derailing responses | Tight top-K (3–5) with similarity threshold. Memory inspector UI (Phase 6) makes recall behavior auditable so JB can tune. |

## 12. Dependencies

- **Vercel AI Gateway** enabled on the project. `AI_GATEWAY_API_KEY` auto-injected via Vercel integration.
- **Anthropic Claude Opus 4.7** access through the Gateway. Sonnet 4.6 and GPT-5 configured as fallbacks.
- **Vercel Blob** enabled, `BLOB_READ_WRITE_TOKEN` set.
- **Supabase project** (already used for `skill_*` tables). Service-role key available. **pgvector extension** must be enabled for the Phase 5 memory layer (`create extension if not exists vector;`).
- **`HIGGINS_API_TOKEN`** set in Vercel env (Preview + Production).
- **npm packages**: `ai@^6`, `zod`, `@supabase/supabase-js`, `@vercel/node`, `@vercel/blob`, `docx`, `pptxgenjs`. Frontend pulls `marked`, `dompurify`, `highlight.js` from CDN.
- Repo conventions: design tokens from `public/styles/base.css`, kebab-case folders, no hardcoded colors.

## 13. Definition of done (v1)

- [ ] `api/chat.ts` streaming end-to-end against Claude Opus 4.7 via AI Gateway.
- [ ] `higgins2.html` `sendMessage` wired to the real endpoint, tokens stream into bubbles.
- [ ] Conversations + messages persist; refresh restores the active conversation.
- [ ] `ArtifactWindow` class supports drag/resize/minimize/close/z-stack with ≥4 concurrent windows.
- [ ] Markdown, code, HTML, table artifacts render client-side from streamed tool calls.
- [ ] DocX + PPTX artifacts render server-side, upload to Blob, surface download button in the window.
- [ ] `update_artifact` correctly bumps version on the existing window.
- [ ] Voice rubric spot-check: 9/10 responses pass.
- [ ] One sample DocX + one PPTX manually verified to open cleanly in Word + PowerPoint.
- [ ] Memory layer active: summary triggers fire at 70% context, memories persist across conversations, `recall_memory` tool pulls relevant rows into context.
- [ ] `save_memory` + `forget_memory` tools work end-to-end (JB can say "remember that…" / "forget that…").
- [ ] `/api/chat` rejects requests without valid bearer token.
- [ ] Deployed to production; live demo from `https://ai.jbherrera.com/higgins2`.
- [ ] This REQ moved to `requests/archive/` with a one-line "completed" header.

---

## Appendix A — System prompt outline (Phase 2 draft seed)

1. **Identity.** "You are Higgins, JB Herrera's AI assistant and strategic partner."
2. **Addressing.** Always "JB"; current date injected per turn.
3. **Voice.** Visionary Pragmatist — thoughtful, strategic, ethical, innovative, empathetic. Substance over filler. Flesch 60+. Offer options when multiple valid approaches exist. Background → assumptions → recommendation.
4. **Artifact decision rule.** Inline if < 200 words or conversational. Open an artifact for: documents, code > 20 lines, structured data, anything JB will copy/edit/share.
5. **Artifact lifecycle.** Use a stable `id` (slug) so updates target the same window. Announce inline when opening or revising.
6. **Tool budgets.** Don't spawn artifacts for trivial output. Don't answer inline when the user is clearly asking for a deliverable.
7. **Brand context.** Synergi colors `#77bde0 / #b78bd3 / #dc9171`, fonts Roboto + Poppins — use when generating designed artifacts.

## Appendix B — Current state inventory

| Component | Status | Location |
|---|---|---|
| Higgins UI shell (floating card, drag, resize, palette) | Exists | `public/higgins2.html` |
| `sendMessage()` mock with `setTimeout` | Exists, to replace | `public/higgins2.html:1870` |
| Hardcoded demo `canvas-block` markup | Exists, to remove | `public/higgins2.html:1502–1580, 1945` |
| Streaming chat endpoint | Does not exist | — |
| AI SDK v6 / AI Gateway wiring | Does not exist | — |
| Floating artifact window class | Does not exist | — |
| Conversation persistence | Does not exist | — |
| DocX/PPTX server renderers | Does not exist | — |
| Skills hookup | Deferred to REQ-001 Phase 4 | — |

## Appendix C — File-level change map

**New files**
- `package.json`, `tsconfig.json` (root)
- `api/chat.ts`
- `api/lib/supabaseClient.ts`
- `api/lib/higginsRepo.ts`
- `api/lib/auth.ts`
- `api/lib/artifactTools.ts`
- `api/lib/renderers/docx.ts`
- `api/lib/renderers/pptx.ts`
- `db/higgins_schema.sql`
- `public/scripts/higgins-stream.js`
- `public/scripts/artifact-window.js`
- `public/scripts/artifact-renderers.js`
- `public/styles/artifact-window.css`

**Modified files**
- `public/higgins2.html` — replace `sendMessage`, swap `#canvasContent` for `#artifact-layer`, remove demo blocks
- `vercel.json` — per-file runtime declarations for `api/chat.ts`
- `.gitignore` — `node_modules/`, `.vercel/`
- `.env.example` — add `AI_GATEWAY_API_KEY`, `HIGGINS_API_TOKEN`, `BLOB_READ_WRITE_TOKEN`
