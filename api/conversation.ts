import type { VercelRequest, VercelResponse } from '@vercel/node';
import {
  getConversation,
  listMessages,
  listConversations,
  listArtifacts,
  listArtifactVersions,
} from './lib/higginsRepo.js';
import { requireOwner } from './lib/auth.js';

/**
 * Higgins 2.0 conversation reader — REQ-002 Phase 2.
 *
 *   GET /api/conversation?id=<uuid>   → { conversation, messages }
 *   GET /api/conversation             → { conversations: [...] }  (recent list)
 *
 * Node-style handler required by @vercel/node@3.
 */

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }
  if (!requireOwner(req, res)) return;

  const idParam = req.query.id;
  const id = Array.isArray(idParam) ? idParam[0] : idParam;

  if (!id) {
    const conversations = await listConversations({ limit: 50 });
    res.status(200).json({ conversations });
    return;
  }

  const conversation = await getConversation(id);
  if (!conversation) {
    res.status(404).json({ error: 'Not found' });
    return;
  }

  const messages = await listMessages(id);
  const artifacts = await listArtifacts(id);

  // Hydrate each artifact with its latest version content. Walk versions
  // chronologically (oldest → newest), applying body snapshots and patches
  // in order, so artifacts whose latest version is patch-only still
  // reconstruct correctly.
  const artifactsWithContent = await Promise.all(
    artifacts.map(async (a) => {
      const versions = await listArtifactVersions(a.id);
      const versionsAsc = [...versions].reverse();
      let body = '';
      let language: string | null = null;
      for (const v of versionsAsc) {
        const c = v.content as
          | { body?: string; language?: string | null; patch?: { mode: string; content: string } }
          | null;
        if (c?.body !== undefined && c?.body !== null) {
          body = c.body;
          if (c.language !== undefined) language = c.language;
        } else if (c?.patch) {
          if (c.patch.mode === 'replace') body = c.patch.content;
          else if (c.patch.mode === 'append') body = body + c.patch.content;
        }
      }
      return {
        slug: a.slug,
        type: a.type,
        title: a.title,
        current_version: a.current_version,
        content: body,
        language,
        updated_at: a.updated_at,
      };
    }),
  );

  res.status(200).json({ conversation, messages, artifacts: artifactsWithContent });
}
