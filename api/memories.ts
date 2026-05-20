import type { VercelRequest, VercelResponse } from '@vercel/node';
import { listMemories, forgetMemory, type MemoryKind } from './lib/higginsRepo.js';
import { requireOwner } from './lib/auth.js';

/**
 * Higgins 2.0 memory inspector API — REQ-002 Phase 6.
 *
 *   GET    /api/memories                  → { memories: [...] } (recent first)
 *   GET    /api/memories?kind=preference  → filtered by kind
 *   DELETE /api/memories?id=<uuid>        → { status: 'forgotten' }
 *
 * Read-only listing + delete. The save/forget tools used by Higgins
 * itself live in api/lib/memoryTools.ts; this endpoint serves the
 * memory inspector UI inside /higgins2.
 */

const VALID_KINDS: MemoryKind[] = ['summary', 'fact', 'preference', 'project', 'reference'];

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (!requireOwner(req, res)) return;

  if (req.method === 'GET') {
    const kindParam = req.query.kind;
    const kindRaw = Array.isArray(kindParam) ? kindParam[0] : kindParam;
    const kind = kindRaw && VALID_KINDS.includes(kindRaw as MemoryKind)
      ? (kindRaw as MemoryKind)
      : undefined;

    const limitRaw = Array.isArray(req.query.limit) ? req.query.limit[0] : req.query.limit;
    const limit = Number.isFinite(Number(limitRaw)) ? Math.min(500, Number(limitRaw)) : 200;

    const memories = await listMemories({ kind, limit });
    res.status(200).json({
      memories: memories.map((m) => ({
        id: m.id,
        kind: m.kind,
        scope: m.scope,
        title: m.title,
        content: m.content,
        importance: m.importance,
        conversation_id: m.conversation_id,
        created_at: m.created_at,
      })),
    });
    return;
  }

  if (req.method === 'DELETE') {
    const idParam = req.query.id;
    const id = Array.isArray(idParam) ? idParam[0] : idParam;
    if (!id) {
      res.status(400).json({ error: 'id query parameter required' });
      return;
    }
    await forgetMemory(id);
    res.status(200).json({ status: 'forgotten', id });
    return;
  }

  res.status(405).json({ error: 'Method not allowed' });
}
