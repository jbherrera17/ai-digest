import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
} from 'docx';

/**
 * Minimal markdown → DocX renderer — REQ-002 Phase 4.
 *
 * Recognised markdown:
 *   # H1   ## H2   ### H3
 *   - bullet     * bullet
 *   1. numbered
 *   **bold**   *italic*   `code`
 *   blank line → paragraph break
 *
 * One Synergi-branded template: Roboto for headings, Poppins for body.
 * Phase 4 ships a single template per type; richer styling lands later.
 */

const BRAND_PRIMARY = '77BDE0'; // Synergi cyan (no leading #)
const HEADING_FONT = 'Roboto';
const BODY_FONT = 'Poppins';

// ── inline parse ─────────────────────────────────────────────────────────
type Inline = { text: string; bold?: boolean; italic?: boolean; code?: boolean };

function parseInline(line: string): Inline[] {
  const out: Inline[] = [];
  let i = 0;
  while (i < line.length) {
    // Code (single backtick)
    if (line[i] === '`') {
      const end = line.indexOf('`', i + 1);
      if (end > i) {
        out.push({ text: line.slice(i + 1, end), code: true });
        i = end + 1;
        continue;
      }
    }
    // Bold (**...**)
    if (line.startsWith('**', i)) {
      const end = line.indexOf('**', i + 2);
      if (end > i) {
        out.push({ text: line.slice(i + 2, end), bold: true });
        i = end + 2;
        continue;
      }
    }
    // Italic (*...*) — single asterisk, not part of bold
    if (line[i] === '*' && line[i + 1] !== '*') {
      const end = line.indexOf('*', i + 1);
      if (end > i) {
        out.push({ text: line.slice(i + 1, end), italic: true });
        i = end + 1;
        continue;
      }
    }
    // Plain text — read until next marker
    let nextMarker = line.length;
    for (const m of ['`', '**', '*']) {
      const at = line.indexOf(m, i);
      if (at >= 0 && at < nextMarker) nextMarker = at;
    }
    if (nextMarker === i) nextMarker++;
    out.push({ text: line.slice(i, nextMarker) });
    i = nextMarker;
  }
  return out;
}

function toRuns(inlines: Inline[]): TextRun[] {
  return inlines.map(
    (i) =>
      new TextRun({
        text: i.text,
        bold: i.bold,
        italics: i.italic,
        font: i.code ? { name: 'Courier New' } : { name: BODY_FONT },
        color: i.code ? '8E8E93' : undefined,
      }),
  );
}

// ── block parse ─────────────────────────────────────────────────────────
function paragraph(text: string, style?: { bullet?: number; numbered?: boolean }) {
  return new Paragraph({
    children: toRuns(parseInline(text)),
    spacing: { after: 120 },
    bullet: style?.bullet !== undefined ? { level: style.bullet } : undefined,
    numbering: style?.numbered
      ? { reference: 'higgins-numbered', level: 0 }
      : undefined,
  });
}

function heading(text: string, level: (typeof HeadingLevel)[keyof typeof HeadingLevel]) {
  const fontSize = level === HeadingLevel.HEADING_1 ? 36 : level === HeadingLevel.HEADING_2 ? 28 : 24;
  return new Paragraph({
    heading: level,
    spacing: { before: 240, after: 120 },
    children: [
      new TextRun({
        text,
        bold: true,
        font: { name: HEADING_FONT },
        size: fontSize,
        color: BRAND_PRIMARY,
      }),
    ],
  });
}

function parseMarkdown(md: string): Paragraph[] {
  const lines = md.replace(/\r\n/g, '\n').split('\n');
  const paragraphs: Paragraph[] = [];

  for (const raw of lines) {
    const line = raw.trimEnd();

    if (!line.trim()) {
      // Blank line — skip; docx handles spacing via `spacing.after`.
      continue;
    }
    if (line.startsWith('# ')) {
      paragraphs.push(heading(line.slice(2), HeadingLevel.HEADING_1));
    } else if (line.startsWith('## ')) {
      paragraphs.push(heading(line.slice(3), HeadingLevel.HEADING_2));
    } else if (line.startsWith('### ')) {
      paragraphs.push(heading(line.slice(4), HeadingLevel.HEADING_3));
    } else if (/^(\-|\*)\s+/.test(line)) {
      paragraphs.push(paragraph(line.replace(/^(\-|\*)\s+/, ''), { bullet: 0 }));
    } else if (/^\d+\.\s+/.test(line)) {
      paragraphs.push(paragraph(line.replace(/^\d+\.\s+/, ''), { numbered: true }));
    } else if (line === '---' || line === '***') {
      paragraphs.push(
        new Paragraph({
          children: [new TextRun({ text: '', color: 'D1D1D6' })],
          border: { bottom: { color: 'D1D1D6', size: 6, style: 'single' } },
          spacing: { before: 120, after: 120 },
        }),
      );
    } else {
      paragraphs.push(paragraph(line));
    }
  }

  return paragraphs;
}

// ── public renderer ──────────────────────────────────────────────────────
export async function renderMarkdownToDocxBuffer(
  markdown: string,
  title?: string,
): Promise<Buffer> {
  const children: Paragraph[] = [];
  if (title) {
    children.push(
      new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { after: 240 },
        children: [
          new TextRun({
            text: title,
            bold: true,
            font: { name: HEADING_FONT },
            size: 44,
            color: BRAND_PRIMARY,
          }),
        ],
      }),
    );
  }
  children.push(...parseMarkdown(markdown));

  const doc = new Document({
    creator: 'Higgins 2.0 — Synergi AI',
    title: title || 'Higgins Artifact',
    styles: {
      default: {
        document: {
          run: { font: BODY_FONT, size: 22 },
        },
      },
    },
    numbering: {
      config: [
        {
          reference: 'higgins-numbered',
          levels: [
            {
              level: 0,
              format: 'decimal',
              text: '%1.',
              alignment: AlignmentType.START,
            },
          ],
        },
      ],
    },
    sections: [{ properties: {}, children }],
  });

  return Packer.toBuffer(doc);
}
