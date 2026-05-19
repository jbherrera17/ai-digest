import { tool } from 'ai';
import { z } from 'zod';
import {
  upsertArtifact,
  appendArtifactVersion,
  listArtifactVersions,
  type ArtifactType,
} from './higginsRepo.js';

/**
 * Artifact tools — REQ-002 Phase 3.
 *
 * Higgins emits `create_artifact` to open a new floating window, then
 * `update_artifact` to revise an existing one. The model picks a stable
 * `id` slug per conversation so updates target the right window.
 *
 * Each tool persists to Supabase via higginsRepo so windows survive reload.
 * Heavy types (docx/pptx/remotion-video) still produce a row in v1 but
 * render server-side files in Phase 4 — for now the frontend shows a
 * "rendering coming in Phase 4" placeholder.
 *
 * Tools are constructed per-request so they can close over conversationId.
 */

const artifactTypeSchema = z.enum([
  'markdown',
  'code',
  'html',
  'table',
  'docx',
  'pptx',
  'remotion-video',
]);

const createArtifactInput = z.object({
  id: z
    .string()
    .min(1)
    .max(60)
    .regex(/^[a-z0-9-]+$/, 'lowercase letters, digits, hyphens'),
  type: artifactTypeSchema,
  title: z.string().min(1).max(120),
  content: z.string().min(1),
  language: z
    .string()
    .max(20)
    .optional()
    .describe('Programming language identifier for code artifacts (e.g. "ts", "python")'),
});

const updateArtifactInput = z.object({
  id: z.string().min(1).max(60),
  patch: z.discriminatedUnion('mode', [
    z.object({ mode: z.literal('replace'), content: z.string() }),
    z.object({ mode: z.literal('append'), content: z.string() }),
  ]),
  versionNote: z.string().max(200).optional(),
});

export function makeArtifactTools(conversationId: string) {
  return {
    create_artifact: tool({
      description: [
        'Open a new floating artifact window in the workspace.',
        'Use for deliverables JB will copy, edit, or share: documents, code blocks > 20 lines, structured data, designed content.',
        'Pick a stable lowercase-slug `id` (e.g. "q2-board-deck"). Reuse the same id with update_artifact for revisions so the same window is targeted.',
        'For `markdown`, write GitHub-flavored markdown. For `code`, set `language`. For `html`, output a complete document — it renders in a sandboxed iframe. For `table`, write a markdown table.',
        'docx, pptx, remotion-video types are accepted but server-side rendering ships in Phase 4 — the window will show a placeholder.',
      ].join(' '),
      inputSchema: createArtifactInput,
      execute: async ({ id, type, title, content, language }) => {
        const artifact = await upsertArtifact({
          conversationId,
          slug: id,
          type: type as ArtifactType,
          title,
        });
        await appendArtifactVersion({
          artifactId: artifact.id,
          content: { body: content, language: language ?? null },
          versionNote: 'initial',
        });
        return { status: 'opened', id, type, title };
      },
    }),

    update_artifact: tool({
      description: [
        'Revise an existing artifact window in place. The `id` must match a previously opened artifact in this conversation.',
        'Use `mode: "replace"` for a full rewrite, `mode: "append"` to add to the end.',
        'Adds a new version row so JB can see edit history.',
      ].join(' '),
      inputSchema: updateArtifactInput,
      execute: async ({ id, patch, versionNote }) => {
        const artifact = await upsertArtifact({
          conversationId,
          slug: id,
          type: 'markdown' as ArtifactType, // ignored when row already exists
        });

        // Reconstruct the current body from prior versions so we can store a
        // resolved snapshot. Walk oldest → newest, applying body snapshots and
        // patches in order.
        const versions = await listArtifactVersions(artifact.id);
        const versionsAsc = [...versions].reverse();
        let currentBody = '';
        let currentLanguage: string | null = null;
        for (const v of versionsAsc) {
          const c = v.content as
            | { body?: string; language?: string | null; patch?: { mode: string; content: string } }
            | null;
          if (c?.body !== undefined && c?.body !== null) {
            currentBody = c.body;
            if (c.language !== undefined) currentLanguage = c.language;
          } else if (c?.patch) {
            if (c.patch.mode === 'replace') currentBody = c.patch.content;
            else if (c.patch.mode === 'append') currentBody = currentBody + c.patch.content;
          }
        }

        const newBody =
          patch.mode === 'replace' ? patch.content : currentBody + patch.content;

        await appendArtifactVersion({
          artifactId: artifact.id,
          content: { body: newBody, language: currentLanguage, patch },
          versionNote: versionNote ?? patch.mode,
        });
        return { status: 'updated', id, mode: patch.mode };
      },
    }),
  };
}
