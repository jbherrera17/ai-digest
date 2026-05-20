# REQ-004 — Agent Team Assembly for Higgins 2.0

**Owner:** JB Herrera
**Drafted by:** Higgins
**Date:** 2026-05-19
**Status:** Draft — awaiting JB approval
**Project:** ai-tools (`public/higgins2.html`, new `api/lib/teamTools.ts`, `db/skills_schema.sql` extension)
**Depends on / closes:** REQ-001 (Skills Governance Layer) — **REQ-001 Phase 4 ships as part of this REQ.** When JB says *"Higgins, bring the team together,"* that's the per-agent-invocation selection model REQ-001 deferred to implementation time.

---

## 1. Problem

Higgins 2.0 can chat and produce artifacts (REQ-002), but every response comes from Higgins alone. There's no way to assemble a specialist team for a multi-disciplinary task.

JB has ~74 governed skills in `skill_registry` (REQ-001) — finance, customer success, partnerships, compliance, chief-of-staff, etc. They sit there approved but unused. The instinct *"bring the team together for an omni-channel marketing campaign"* should pull in the marketing skill, the brand voice skill, the customer-success-feedback skill, the channel-strategy skill — present them to JB as a team — then proceed with that team's combined context.

Without this layer:
- The skills governance work (REQ-001) has no human-facing payoff yet.
- Higgins can't differentiate itself from generic chat — every task gets one voice.
- JB can't see *which* expertise was applied to a deliverable, which kills traceability and trust.

## 2. Strategic intent

This is the **product moment** for the Synergi vision: not "an AI assistant" but **"an AI org chart you can convene on demand."** The team assembly UI is the visual proof that Higgins is a curator of specialists, not just a wrapper around Claude. It also gives JB a way to ship the same demo to clients ("here's *your* values-aligned team being assembled in real time") — the foundation for i360 deployments later.

## 3. Users

| User | Job-to-be-done | Frequency |
|---|---|---|
| **JB (primary)** | Convene a relevant agent team for multi-disciplinary work — campaigns, strategic reviews, post-mortems. | Daily |
| **Future: Sales calls / demos** | Show the team-assembly moment as a live differentiator. | Per pitch |
| **Future: i360 client deployments** | Each client gets a roster of their values-aligned agents available on demand. | Per onboarding |

v1 ships for JB only.

## 4. Goals & success metrics

| Goal | Metric | Target |
|---|---|---|
| Team assembly feels intentional, not random | % of `assemble_team` calls where JB keeps the proposed roster (no edits) | ≥ 60% |
| The right specialists get pulled | Manual rubric: 5 sample tasks → expected roster matches actual ≥ 80% of agents | 4/5 tasks pass |
| Visual moment lands | Time from user prompt → team display rendered | < 3s |
| Skill catalog actually gets used | % of approved skills used at least once in 30 days | ≥ 40% |
| Traceability holds | Every artifact produced after team assembly references which agents contributed | 100% |

## 5. In scope (v1)

1. **`assemble_team` tool.** New Higgins tool: given a task, returns a curated roster of approved skills (typically 3–6). Driven by the LLM with the skill catalog injected as context, not by keyword matching.
2. **Skills API consumer in Higgins.** Closes **REQ-001 Phase 4**. `api/chat.ts` fetches `GET /api/skills?status=approved` once per request (cached for 5 min in-memory), exposes the catalog to the model via system prompt.
3. **Team assembly UI.** A center-screen modal that renders the proposed team as cards — avatar, name, department, one-line purpose. JB can:
   - Approve (continue with this team)
   - Remove individual agents
   - Add agents from the full roster
   - Cancel (abort the task)
4. **Avatar storage + defaults.** Each skill row gets an `avatar_url` column. v1 uses pre-generated SVG fallbacks (initials + brand-color background) when no avatar is set. Avatars upload to **Vercel Blob** (`higgins/avatars/` prefix), same store as artifacts.
5. **Orchestration model — context injection (not sub-tools).** When JB approves the team, each agent's skill content (the `.agents/skills/{slug}/SKILL.md` body) is injected into the system prompt as a labeled persona block: `## Agent: {name}\n{skill content}`. Higgins orchestrates them via prompt context, not by spawning sub-tool calls per agent. (See §9 for why.)
6. **Agent attribution on artifacts.** When an artifact is created during a team task, its title or footer notes the contributing agents. Stored alongside the artifact in `higgins_artifacts.contributing_agents` (new column).
7. **Team session persistence.** The assembled team for the current conversation lives in a new `higgins_team_sessions` table, restored on reload alongside the conversation.

## 6. Out of scope (v2+)

- Sub-tool-per-agent orchestration (each agent gets its own `streamText` call and Higgins synthesizes — covered in §9 as the rejected option).
- Custom JB-uploaded avatars (v1 uses defaults; uploads come later).
- Per-client/per-tenant agent rosters.
- Dynamic team adjustment mid-task ("add the compliance agent now").
- Agent-to-agent dialogue surfaced in the UI (back-and-forth between team members).
- Confidence scores per agent ("how relevant is this agent to the task?").
- Voice ("Higgins, bring the team together" by voice command — UI button + typed prompt only in v1).

## 7. MVP cut — the smallest version that closes the loop

Three things must all be true:

1. **Catalog flows.** Higgins can see the approved skills from `skill_registry` on every turn.
2. **Visual assembly moment works.** Saying *"bring the team together for X"* opens the modal with 3–6 proposed agents, each with name + avatar + purpose. JB can approve.
3. **Approved team shapes the answer.** With a team approved, Higgins's subsequent responses reflect that team's combined expertise — verifiable by asking *"who contributed to this?"* and getting an accurate list.

Anything else is layered on after.

## 8. Schema deltas

### `skill_registry` (extend)

| Field | Type | Purpose |
|---|---|---|
| `avatar_url` | text, nullable | Vercel Blob URL for the agent's visual identity. NULL → use generated SVG fallback. |
| `display_name` | text, nullable | Human-friendly agent name distinct from `slug`. E.g., `"Marcus, Marketing Strategist"`. Falls back to `name`. |
| `tagline` | text, nullable | One-line purpose for the team-assembly card. ≤ 80 chars. |

### New table: `higgins_team_sessions`

```sql
higgins_team_sessions (
  id              uuid primary key,
  conversation_id uuid references higgins_conversations(id) on delete cascade,
  skill_ids       uuid[] not null,                 -- the approved roster
  task_summary    text,                            -- "Omni-channel marketing campaign for Q3"
  assembled_at    timestamptz not null default now(),
  approved_at     timestamptz                      -- null until JB approves
)
```

One active session per conversation. `approved_at` lets us distinguish *proposed* teams from *approved* ones.

### New column: `higgins_artifacts.contributing_agents`

```sql
ALTER TABLE higgins_artifacts
  ADD COLUMN contributing_agents text[];  -- skill slugs
```

Populated when an artifact is generated during an active team session.

## 9. The orchestration question (key architectural choice)

Two models, choosing one explicitly:

**A — Context injection (chosen for v1).** Approved team's skill content concatenated into the system prompt as persona blocks. Higgins runs as a single `streamText` call but its system prompt carries the team's combined expertise. Pros: one LLM call per turn, low latency, predictable cost, no fan-out complexity, works inside the current Phase 2–5 pipeline. Cons: large prompts when teams are big (mitigated by 1M Opus context); agents don't "talk to each other" in any explicit sense.

**B — Sub-tool fan-out.** Each approved agent becomes its own tool. Higgins calls `agent_marketing({task})`, `agent_brand({task})`, etc., in parallel, then synthesizes their outputs. Pros: visible agent activity (could animate cards lighting up); strict expertise boundaries; aligned with the *"team meeting"* mental model. Cons: N× latency, N× cost per turn, error surface explodes, integration with artifacts/memory is fragile, no clear win for v1.

**Recommendation: A.** Ship the visual + assembly moment with cheap, fast context-injection orchestration. Revisit B in v2 if and only if (1) JB hits a real expertise-bleeding problem or (2) the demo would benefit from animated multi-agent activity. **A is reversible to B** — the schema and UI don't change, only the chat-turn implementation.

## 10. Avatar storage strategy

Three candidates evaluated:

| Option | Verdict |
|---|---|
| **Vercel Blob** | ✅ **Chosen.** Already wired in Phase 4 with `BLOB_READ_WRITE_TOKEN`. Public URLs cache cleanly at the CDN edge. Same prefix scheme as artifacts (`higgins/avatars/{slug}-v1.png`). |
| Supabase Storage | Plausible — but adds a second blob system, more env config, no clear win. Reject. |
| Static `public/avatars/` | Cheapest but inflexible — every avatar change requires a redeploy. Skills are added dynamically via the updater; static files would break that flow. Reject. |

**Default avatars (no upload required):** SVG generated server-side from initials + a deterministic palette pick (Synergi cyan / violet / amber rotated by `skill.id` hash). Renders in <1ms, no fetch needed for fallback. Same look as Slack/Notion default avatars.

**v1 ships with defaults only.** JB-uploaded portraits land in v2 (a tiny upload form in the skill admin UI).

## 11. Phased delivery plan

| Phase | Deliverable | Effort |
|---|---|---|
| **0 — Schema deltas** | Apply `skill_registry` extensions + new `higgins_team_sessions` table + `higgins_artifacts.contributing_agents` column. | 1 session |
| **1 — Skills consumer + default avatars** | `api/chat.ts` fetches approved skills, caches 5 min, injects catalog summary into system prompt. SVG fallback avatar generator. Smoke test: Higgins can name 5 skills accurately when asked. **Closes REQ-001 Phase 4.** | 1 session |
| **2 — `assemble_team` tool + persistence** | New tool definition in `api/lib/teamTools.ts`. LLM picks 3–6 skill ids given the task and catalog. Writes `higgins_team_sessions` row with `approved_at = NULL`. | 1 session |
| **3 — Team assembly modal UI** | Center-screen overlay rendering agent cards on `tool-output-available`. Approve / Cancel / Remove individual agents. On approve: PATCH the session row with `approved_at = now()`. | 2 sessions |
| **4 — Context injection on approved teams** | When the team is approved, subsequent chat turns inject each agent's `SKILL.md` content as labeled blocks. Add `agents_active` indicator badges in the Higgins card header. | 1 session |
| **5 — Agent attribution on artifacts** | Populate `higgins_artifacts.contributing_agents` from the active team session on tool execute. Surface in the artifact window footer ("Generated with: Marcus (Marketing), Sofia (Brand)"). | 1 session |
| **6 — Polish + voice rubric** | Animate the team-assembly modal. QA the team-selection accuracy on 5 sample tasks. Tune the catalog-injection prompt. | 1 session |

**Total to v1-shipped: 7–8 working sessions.**

## 12. Open decisions

| # | Question | Recommendation | Status |
|---|---|---|---|
| 1 | Orchestration model: context-injection vs sub-tool fan-out | **A — context injection.** See §9. | Pending JB |
| 2 | Avatar storage | **Vercel Blob** with SVG-initials fallback. See §10. | Pending JB |
| 3 | Roster size guardrails | Default 3–6 agents. Hard max 8 (system prompt overflow risk). | Pending JB |
| 4 | Team trigger phrase | Open: tool-driven by LLM when the task warrants it, **plus** an explicit `"Higgins, bring the team together"` UI button in the card header. Both routes call `assemble_team`. | Pending JB |
| 5 | Mid-task team edits | v1: team is locked at approval. To change, start a new conversation or explicitly say *"reassemble the team"*. | Pending JB |
| 6 | Default avatar style | Initials on a Synergi-palette circle (cyan / violet / amber rotated). Open: should we instead generate from a pre-rendered SVG set with character variants? Defaults look more "platform-native." | Pending JB |
| 7 | Skill catalog injection format | One-line summary per skill (name + tagline + department), so the model sees the full ~74-skill catalog without burning too much context. Full `SKILL.md` only loaded for approved team members. | Pending JB |

## 13. Risks

| Risk | Mitigation |
|---|---|
| Higgins picks the wrong team for the task | Define a 5-task evaluation rubric (one campaign, one strategy review, one customer issue, one finance question, one ambiguous). Run after each prompt tune. |
| 74-skill catalog blows the system prompt | One-line per-skill summaries (estimated 100 tokens × 74 = ~7,400 tokens). Well within Opus 4.7's 1M. Verified in Phase 1. |
| Assembled team's combined `SKILL.md` content overflows | Hard cap of 8 agents + per-agent token budget (3K each). If a skill exceeds budget, truncate with a footer note. |
| The visual moment feels gimmicky | Hard rule: only `assemble_team` if Higgins genuinely needs the specialist context. Don't fire it for casual chats. System prompt enforces this — and JB-driven button gives explicit user intent when desired. |
| Default avatars look amateur | Phase 0/1 — render 5 default avatars side-by-side, JB approves visual quality before Phase 3 builds on them. |
| `higgins_team_sessions` writes leak across conversations | `conversation_id` is required and indexed. One active session per conversation by uniqueness constraint. |

## 14. Dependencies

- **REQ-001 schema** applied (✅ done 2026-05-18).
- **REQ-002 chat infrastructure** live (✅ shipped 2026-05-19).
- **Skill catalog populated** — the 74 backfilled skills from REQ-001 must be `review_status='approved'` (✅ per REQ-001).
- **Skill `SKILL.md` files** accessible to the server — likely via the `file_path` column in `skill_registry` pointing to `.agents/skills/{slug}/SKILL.md`. Phase 1 verifies the read path works from `api/chat.ts`.
- **Vercel Blob** (✅ wired in REQ-002 Phase 4).

## 15. Definition of done (v1)

- [ ] Schema delta applied: `skill_registry` extensions + `higgins_team_sessions` + `higgins_artifacts.contributing_agents`.
- [ ] `api/chat.ts` consumes `/api/skills?status=approved`, caches 5 min, injects catalog summary.
- [ ] **REQ-001 Phase 4 marked complete** in its archived REQ.
- [ ] `assemble_team` tool defined, callable, picks accurate teams in 4/5 sample-task tests.
- [ ] Team-assembly modal renders cards with avatars, allows approve / cancel / remove-agent.
- [ ] Approved team's skill content is injected into Higgins's system prompt for all subsequent turns until conversation ends.
- [ ] Artifacts generated during an active team session have `contributing_agents` populated and surface that list in the window footer.
- [ ] Default SVG avatars render for all 74 backfilled skills.
- [ ] "Bring the team together" button visible in the card header, triggers `assemble_team` with the latest user message as context.
- [ ] Deployed to production at `https://ai.jbherrera.com/higgins2`.
- [ ] This REQ moved to `requests/archive/` with a one-line "Completed" header.

---

## Appendix A — Sample team-assembly flows for the rubric

| Task | Expected roster |
|---|---|
| "Omni-channel marketing campaign for Q3 launch" | Marketing Strategist, Brand Voice, Customer Success (feedback signals), Channel Strategy, Copywriter |
| "Strategy review — should we sunset Product X?" | Chief of Staff, Strategic Advisor, Finance (revenue impact), Customer Success (retention risk), Product |
| "Customer complaint escalated — how do we respond?" | Customer Success, Communications/PR, Legal (compliance check), Operations (process gap) |
| "Help me prep the Q2 board update" | Chief of Staff, Strategic Advisor, Finance Reporting, Operations Lead |
| "I'm thinking about taking on a new vertical" | Strategic Advisor, Finance Budget Forecast, Partnerships, Marketing Strategist |

## Appendix B — Catalog-injection format (Phase 1 sketch)

System prompt prepends:

```
## Available specialist agents (74)

When a task warrants multi-disciplinary work, call assemble_team with
the relevant slugs. Otherwise, answer as Higgins yourself.

- biz-customer-success — Marcus · Customer Success · Retention signals, churn analysis, NPS deep-dives
- biz-finance-budget — Sofia · Finance · Budget forecasting, scenario modelling, runway math
- biz-strategy-advisor — Diana · Strategy · Pressure-tests big decisions, names blind spots
- ... [74 lines total, ~100 tokens each]
```

One line per skill, approximately 7,400 tokens — well under budget.

## Appendix C — Current state inventory

| Component | Status | Location |
|---|---|---|
| Skill registry | Exists, 74 backfilled | `skill_registry` table (REQ-001) |
| Skills public API | Exists | `api/skills.py` |
| Skill `SKILL.md` files | Exists | `.agents/skills/{slug}/` |
| Higgins chat infrastructure | Exists | `api/chat.ts` (REQ-002) |
| Higgins UI shell | Exists | `public/higgins2.html` (REQ-002) |
| Vercel Blob | Wired | `api/lib/blob.ts` (REQ-002 Phase 4) |
| `assemble_team` tool | Does not exist | — |
| Team assembly modal | Does not exist | — |
| Avatar defaults | Does not exist | — |
| Skill content read path from chat | Does not exist | — |
