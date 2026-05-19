import type { VercelRequest, VercelResponse } from '@vercel/node';

/**
 * Single-user bearer-token gate for Higgins 2.0 endpoints (v1).
 *
 * The token lives in HIGGINS_API_TOKEN. Frontend stores it once in
 * localStorage and sends `Authorization: Bearer <token>` on every call.
 *
 * If HIGGINS_API_TOKEN is unset, requests are allowed through (dev mode) —
 * matches the same convenience pattern as the existing Python admin routes
 * (api/admin/*.py skip auth when ADMIN_API_TOKEN is unset).
 */

export const OWNER_USER_ID = 'jb';

/**
 * Web-style auth check used by streaming endpoints that return a Web Response.
 * Returns null on success; returns a 401 Response on failure (caller should
 * return that Response directly).
 */
export function requireOwnerFromRequest(req: Request): Response | null {
  const expected = process.env.HIGGINS_API_TOKEN;

  // Dev mode: no token configured → allow.
  if (!expected) return null;

  const header = req.headers.get('authorization') ?? '';
  const match = header.match(/^Bearer\s+(.+)$/i);
  const provided = match?.[1];

  if (provided !== expected) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    });
  }
  return null;
}

/**
 * Node-style auth check retained for any future Vercel functions that use
 * the classic (VercelRequest, VercelResponse) signature.
 */
export function requireOwner(req: VercelRequest, res: VercelResponse): boolean {
  const expected = process.env.HIGGINS_API_TOKEN;
  if (!expected) return true;

  const header = req.headers.authorization || '';
  const match = header.match(/^Bearer\s+(.+)$/i);
  const provided = match?.[1];

  if (provided !== expected) {
    res.status(401).json({ error: 'Unauthorized' });
    return false;
  }
  return true;
}
