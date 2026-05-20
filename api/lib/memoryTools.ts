import { tool } from 'ai';
import { z } from 'zod';
import {
  saveMemory,
  recallMemories,
  forgetMemory,
  listMessages,
  type MemoryKind,
  type MemoryScope,
} from './higginsRepo.js';
import { embedText } from './embeddings.js';

/**
 * Memory tools — REQ-002 Phase 5.
 *
 * Higgins reads/writes a dedicated memory store (higgins_memories), not
 * the LLM's context window. Five memory kinds: summary, fact, preference,
 * project, reference. Embeddings (1536-dim, OpenAI text-embedding-3-small)
 * power semantic recall via pgvector + HNSW.
 *
 * Auto-recall on each turn happens in api/chat.ts before streamText —
 * the tools below are for explicit JB-driven save/forget and on-demand
 * lookup beyond the default top-K injection.
 */

const memoryKindSchema = z.enum(['summary', 'fact', 'preference', 'project', 'reference']);
const memoryScopeSchema = z.enum(['global', 'conversation', 'project']);

const saveInput = z.object({
  kind: memoryKindSchema,
  content: z.string().min(3).max(4000),
  title: z.string().max(120).optional(),
  scope: memoryScopeSchema.optional(),
  importance: z.number().int().min(1).max(5).optional(),
});

const recallInput = z.object({
  query: z.string().min(2).max(500),
  kind: memoryKindSchema.optional(),
  scope: memoryScopeSchema.optional(),
  topK: z.number().int().min(1).max(10).optional(),
});

const forgetInput = z.object({
  id: z.string().uuid(),
});

const summarizeInput = z.object({
  note: z.string().max(200).optional().describe('Optional framing label for the summary.'),
});

export function makeMemoryTools(conversationId: string) {
  return {
    save_memory: tool({
      description: [
        "Persist something to JB's long-term memory store.",
        "Call when JB says 'remember that…', states a preference, or mentions an ongoing project worth keeping across sessions.",
        'Kinds: fact, preference, project, reference, summary. Default scope global. Importance 1–5 (3 default).',
        'Memories are embedded for semantic recall and live beyond the current conversation.',
      ].join(' '),
      inputSchema: saveInput,
      execute: async ({ kind, content, title, scope, importance }) => {
        try {
          const embedding = await embedText(`${title ? title + '\n' : ''}${content}`);
          const mem = await saveMemory({
            kind: kind as MemoryKind,
            content,
            title: title ?? null,
            scope: (scope ?? 'global') as MemoryScope,
            conversationId,
            importance: importance ?? 3,
            embedding,
          });
          return {
            status: 'saved',
            id: mem.id,
            kind: mem.kind,
            title: mem.title,
          };
        } catch (err) {
          console.error('[higgins/memoryTools] save_memory failed', err);
          return { status: 'error', error: (err as Error).message };
        }
      },
    }),

    recall_memory: tool({
      description: [
        'Search the memory store for entries semantically related to a query.',
        'Top-K results ranked by cosine similarity over embeddings.',
        'Use when you need context beyond what was auto-injected — JB references a past project, asks about a saved preference, etc.',
        'Memories of all kinds are searched by default; filter with kind/scope when relevant.',
      ].join(' '),
      inputSchema: recallInput,
      execute: async ({ query, kind, scope, topK }) => {
        try {
          const queryEmbedding = await embedText(query);
          const memories = await recallMemories({
            queryEmbedding,
            kind: kind as MemoryKind | undefined,
            scope: scope as MemoryScope | undefined,
            matchCount: topK ?? 5,
          });
          return {
            status: 'ok',
            count: memories.length,
            memories: memories.map((m) => ({
              id: m.id,
              kind: m.kind,
              title: m.title,
              content: m.content,
              importance: m.importance,
              similarity: Number(m.similarity?.toFixed(3) ?? 0),
            })),
          };
        } catch (err) {
          console.error('[higgins/memoryTools] recall_memory failed', err);
          return { status: 'error', error: (err as Error).message };
        }
      },
    }),

    forget_memory: tool({
      description: [
        "Delete a memory by id. Call when JB says 'forget that…' or asks to remove a saved item.",
        'Always confirm the id matches the right memory (use recall_memory first if unsure).',
      ].join(' '),
      inputSchema: forgetInput,
      execute: async ({ id }) => {
        try {
          await forgetMemory(id);
          return { status: 'forgotten', id };
        } catch (err) {
          console.error('[higgins/memoryTools] forget_memory failed', err);
          return { status: 'error', error: (err as Error).message };
        }
      },
    }),

    summarize_conversation: tool({
      description: [
        'Distill the current conversation into a saved summary memory.',
        'Use when the conversation has produced something worth carrying forward (decisions, conclusions, action items).',
        'Returns the memory id of the new summary row.',
      ].join(' '),
      inputSchema: summarizeInput,
      execute: async ({ note }) => {
        try {
          const messages = await listMessages(conversationId);
          if (messages.length === 0) {
            return { status: 'skipped', reason: 'no messages to summarize' };
          }
          // Naive distillation: concatenate user + assistant text parts.
          // Phase 5.5 can replace this with an LLM call for true summarization;
          // for v1 we store the raw transcript as a summary memory so the
          // record exists and is searchable.
          const transcript = messages
            .map((m) => {
              const parts = Array.isArray(m.parts) ? (m.parts as Array<{ type: string; text?: string }>) : [];
              const text = parts
                .filter((p) => p?.type === 'text' && typeof p.text === 'string')
                .map((p) => p.text)
                .join('');
              return text ? `[${m.role}] ${text}` : null;
            })
            .filter(Boolean)
            .join('\n\n');

          const body = note ? `${note}\n\n${transcript}` : transcript;
          const embedding = await embedText(body.slice(0, 8000));
          const mem = await saveMemory({
            kind: 'summary',
            content: body,
            title: note ?? `Conversation summary (${new Date().toISOString().slice(0, 10)})`,
            scope: 'conversation',
            conversationId,
            sourceMessageIds: messages.map((m) => m.id),
            importance: 4,
            embedding,
          });
          return { status: 'summarized', id: mem.id, messageCount: messages.length };
        } catch (err) {
          console.error('[higgins/memoryTools] summarize_conversation failed', err);
          return { status: 'error', error: (err as Error).message };
        }
      },
    }),
  };
}
