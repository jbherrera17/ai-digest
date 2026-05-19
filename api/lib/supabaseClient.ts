import { createClient, type SupabaseClient } from '@supabase/supabase-js';

/**
 * Service-role Supabase client for Higgins 2.0 server code.
 *
 * Mirrors the auth pattern in api/lib/supabase.py: prefer
 * SUPABASE_SERVICE_ROLE_KEY (Vercel integration auto-provisions this),
 * fall back to SUPABASE_SERVICE_KEY for older local .env files.
 *
 * Service role bypasses RLS. v1 is single-user (JB) and ungated — fine.
 */

let cached: SupabaseClient | null = null;

export function getServiceClient(): SupabaseClient {
  if (cached) return cached;

  const url = process.env.SUPABASE_URL;
  const key =
    process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY;

  if (!url) throw new Error('SUPABASE_URL is not set');
  if (!key) {
    throw new Error(
      'SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SERVICE_KEY) is not set',
    );
  }

  cached = createClient(url, key, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
  return cached;
}
