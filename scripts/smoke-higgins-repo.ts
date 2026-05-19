/**
 * Phase 1 smoke test for the Higgins repo layer.
 *
 * Verifies a full round-trip against Supabase:
 *   conversation → message → artifact + version → memory → list → cleanup.
 *
 * Usage:
 *   npx tsx scripts/smoke-higgins-repo.ts
 *
 * Requires .env (or .env.vercel.tmp) with SUPABASE_URL +
 * SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SERVICE_KEY).
 *
 * Safe to run repeatedly — every run creates a fresh conversation
 * and deletes it on success.
 */

import {
  createConversation,
  appendMessage,
  listMessages,
  upsertArtifact,
  appendArtifactVersion,
  listArtifacts,
  listArtifactVersions,
  saveMemory,
  listMemories,
  deleteConversation,
} from '../api/lib/higginsRepo.js';

function log(step: string, payload?: unknown) {
  process.stdout.write(`\n→ ${step}\n`);
  if (payload !== undefined) {
    process.stdout.write(`  ${JSON.stringify(payload, null, 2).replace(/\n/g, '\n  ')}\n`);
  }
}

async function main() {
  log('1. createConversation');
  const conv = await createConversation({ title: 'Phase 1 smoke test' });
  log('   created', { id: conv.id, title: conv.title });

  log('2. appendMessage (user)');
  const userMsg = await appendMessage({
    conversationId: conv.id,
    role: 'user',
    parts: [{ type: 'text', text: 'Hello Higgins.' }],
  });
  log('   appended', { id: userMsg.id, role: userMsg.role });

  log('3. appendMessage (assistant)');
  const aiMsg = await appendMessage({
    conversationId: conv.id,
    role: 'assistant',
    parts: [{ type: 'text', text: 'Hello, JB. Smoke test underway.' }],
  });
  log('   appended', { id: aiMsg.id, role: aiMsg.role });

  log('4. listMessages');
  const msgs = await listMessages(conv.id);
  log('   count', msgs.length);
  if (msgs.length !== 2) throw new Error(`expected 2 messages, got ${msgs.length}`);

  log('5. upsertArtifact (create)');
  const art = await upsertArtifact({
    conversationId: conv.id,
    slug: 'smoke-doc',
    type: 'markdown',
    title: 'Smoke test doc',
  });
  log('   created', { id: art.id, slug: art.slug, version: art.current_version });

  log('6. appendArtifactVersion');
  const v2 = await appendArtifactVersion({
    artifactId: art.id,
    content: { markdown: '# v2\n\nUpdated content.' },
    versionNote: 'second pass',
  });
  log('   appended', { version: v2.version_no, note: v2.version_note });

  log('7. upsertArtifact (re-upsert with same slug — should update, not insert)');
  const artAgain = await upsertArtifact({
    conversationId: conv.id,
    slug: 'smoke-doc',
    type: 'markdown',
    title: 'Smoke test doc (renamed)',
  });
  if (artAgain.id !== art.id) {
    throw new Error('upsert created a new row instead of updating');
  }
  log('   ok — same id, updated title', { title: artAgain.title });

  log('8. listArtifacts');
  const arts = await listArtifacts(conv.id);
  log('   count', arts.length);
  if (arts.length !== 1) throw new Error(`expected 1 artifact, got ${arts.length}`);

  log('9. listArtifactVersions');
  const versions = await listArtifactVersions(art.id);
  log('   versions', versions.map((v) => v.version_no));
  if (versions.length !== 1) {
    // We only ever appended one version row (v2). v1 is implicit via current_version default.
    throw new Error(`expected 1 version row, got ${versions.length}`);
  }

  log('10. saveMemory');
  const mem = await saveMemory({
    kind: 'fact',
    content: 'Smoke test ran on ' + new Date().toISOString(),
    title: 'Phase 1 smoke marker',
    importance: 1,
    conversationId: conv.id,
    sourceMessageIds: [userMsg.id, aiMsg.id],
  });
  log('   saved', { id: mem.id, kind: mem.kind, importance: mem.importance });

  log('11. listMemories (filter by kind=fact)');
  const mems = await listMemories({ kind: 'fact', conversationId: conv.id });
  log('   count', mems.length);
  if (mems.length < 1) throw new Error('expected at least 1 memory');

  log('12. deleteConversation (cascades to messages + artifacts + versions)');
  await deleteConversation(conv.id);
  const after = await listMessages(conv.id);
  if (after.length !== 0) throw new Error('cascade delete did not remove messages');
  log('   ok — conversation + dependents removed');

  // Memory rows have ON DELETE SET NULL on conversation_id — leave the marker
  // memory in the table so JB can spot the row if anything looks off. It's
  // tagged with importance=1 and easy to scrub.
  log('\n✓ Phase 1 smoke test passed.');
}

main().catch((err) => {
  process.stderr.write(`\n✗ Smoke test failed: ${err?.message || err}\n`);
  if (err?.stack) process.stderr.write(err.stack + '\n');
  process.exit(1);
});
