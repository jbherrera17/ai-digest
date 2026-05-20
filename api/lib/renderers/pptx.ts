import PptxGenJS from 'pptxgenjs';
import { z } from 'zod';

/**
 * JSON spec → PPTX renderer — REQ-002 Phase 4.
 *
 * Higgins emits a structured deck spec (parsed from the tool's `content`
 * string), and we render it with pptxgenjs in one Synergi-branded
 * template. v1 supports four layouts:
 *
 *   - 'title-card'    : big hero title + optional subtitle
 *   - 'title-bullets' : title at top, bullet list body
 *   - 'two-column'    : title + left/right paragraphs
 *   - 'section-break' : full-bleed colored slide with a single label
 *
 * Phase 4 keeps this lean — one template per type. Richer layouts can
 * be added by extending the discriminated union below.
 */

const BRAND = {
  cyan: '77BDE0',
  violet: 'B78BD3',
  amber: 'DC9171',
  ink: '1C1C1E',
  paper: 'FFFFFF',
  muted: '8E8E93',
  rule: 'E5E5EA',
};

const HEADING_FONT = 'Roboto';
const BODY_FONT = 'Poppins';

// ── schema ────────────────────────────────────────────────────────────
const titleCard = z.object({
  layout: z.literal('title-card'),
  title: z.string(),
  subtitle: z.string().optional(),
});
const titleBullets = z.object({
  layout: z.literal('title-bullets'),
  title: z.string(),
  bullets: z.array(z.string()).min(1).max(8),
});
const twoColumn = z.object({
  layout: z.literal('two-column'),
  title: z.string(),
  left: z.string(),
  right: z.string(),
  leftHeading: z.string().optional(),
  rightHeading: z.string().optional(),
});
const sectionBreak = z.object({
  layout: z.literal('section-break'),
  label: z.string(),
});

const slideSchema = z.discriminatedUnion('layout', [
  titleCard,
  titleBullets,
  twoColumn,
  sectionBreak,
]);

const deckSchema = z.object({
  title: z.string().optional(),
  slides: z.array(slideSchema).min(1).max(40),
});

export type DeckSpec = z.infer<typeof deckSchema>;

export function parseDeckSpec(rawJson: string): DeckSpec {
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawJson);
  } catch (err) {
    throw new Error(
      `pptx content must be valid JSON matching { slides: [{ layout, ... }] }. Parse error: ${(err as Error).message}`,
    );
  }
  const result = deckSchema.safeParse(parsed);
  if (!result.success) {
    throw new Error(`Invalid deck spec: ${result.error.message}`);
  }
  return result.data;
}

// ── rendering helpers ────────────────────────────────────────────────
function applyBranding(pptx: PptxGenJS) {
  pptx.layout = 'LAYOUT_WIDE'; // 13.33 × 7.5 inches
  pptx.defineSlideMaster({
    title: 'HIGGINS_MASTER',
    background: { color: BRAND.paper },
    objects: [
      // Top-left accent rule
      {
        rect: {
          x: 0.4,
          y: 0.4,
          w: 0.5,
          h: 0.06,
          fill: { color: BRAND.cyan },
        },
      },
      // Footer
      {
        text: {
          text: 'Higgins · Synergi AI',
          options: {
            x: 0.4,
            y: 7.0,
            w: 6,
            h: 0.3,
            fontFace: BODY_FONT,
            fontSize: 9,
            color: BRAND.muted,
          },
        },
      },
    ],
  });
}

function addTitleCard(pptx: PptxGenJS, s: z.infer<typeof titleCard>) {
  const slide = pptx.addSlide({ masterName: 'HIGGINS_MASTER' });
  slide.addText(s.title, {
    x: 0.6,
    y: 2.8,
    w: 12,
    h: 1.6,
    fontFace: HEADING_FONT,
    fontSize: 44,
    bold: true,
    color: BRAND.ink,
  });
  if (s.subtitle) {
    slide.addText(s.subtitle, {
      x: 0.6,
      y: 4.4,
      w: 12,
      h: 0.6,
      fontFace: BODY_FONT,
      fontSize: 18,
      color: BRAND.muted,
    });
  }
}

function addTitleBullets(pptx: PptxGenJS, s: z.infer<typeof titleBullets>) {
  const slide = pptx.addSlide({ masterName: 'HIGGINS_MASTER' });
  slide.addText(s.title, {
    x: 0.6,
    y: 0.7,
    w: 12,
    h: 0.8,
    fontFace: HEADING_FONT,
    fontSize: 28,
    bold: true,
    color: BRAND.ink,
  });
  slide.addText(
    s.bullets.map((b) => ({ text: b, options: { bullet: { type: 'bullet' } } })),
    {
      x: 0.7,
      y: 1.7,
      w: 12,
      h: 5,
      fontFace: BODY_FONT,
      fontSize: 18,
      color: BRAND.ink,
      paraSpaceAfter: 8,
    },
  );
}

function addTwoColumn(pptx: PptxGenJS, s: z.infer<typeof twoColumn>) {
  const slide = pptx.addSlide({ masterName: 'HIGGINS_MASTER' });
  slide.addText(s.title, {
    x: 0.6,
    y: 0.7,
    w: 12,
    h: 0.8,
    fontFace: HEADING_FONT,
    fontSize: 28,
    bold: true,
    color: BRAND.ink,
  });

  const colW = 5.9;
  const colY = 1.7;
  const colH = 5;

  if (s.leftHeading) {
    slide.addText(s.leftHeading, {
      x: 0.6, y: colY, w: colW, h: 0.5,
      fontFace: HEADING_FONT, fontSize: 16, bold: true, color: BRAND.violet,
    });
  }
  slide.addText(s.left, {
    x: 0.6, y: s.leftHeading ? colY + 0.5 : colY, w: colW, h: colH,
    fontFace: BODY_FONT, fontSize: 14, color: BRAND.ink,
    paraSpaceAfter: 6,
  });

  if (s.rightHeading) {
    slide.addText(s.rightHeading, {
      x: 6.8, y: colY, w: colW, h: 0.5,
      fontFace: HEADING_FONT, fontSize: 16, bold: true, color: BRAND.amber,
    });
  }
  slide.addText(s.right, {
    x: 6.8, y: s.rightHeading ? colY + 0.5 : colY, w: colW, h: colH,
    fontFace: BODY_FONT, fontSize: 14, color: BRAND.ink,
    paraSpaceAfter: 6,
  });
}

function addSectionBreak(pptx: PptxGenJS, s: z.infer<typeof sectionBreak>) {
  const slide = pptx.addSlide({ masterName: 'HIGGINS_MASTER' });
  // Override the background for full-bleed brand color
  slide.background = { color: BRAND.cyan };
  slide.addText(s.label, {
    x: 0.6,
    y: 3.0,
    w: 12,
    h: 1.5,
    fontFace: HEADING_FONT,
    fontSize: 36,
    bold: true,
    color: BRAND.paper,
  });
}

// ── public renderer ─────────────────────────────────────────────────
export async function renderDeckToPptxBuffer(spec: DeckSpec): Promise<Buffer> {
  const pptx = new PptxGenJS();
  pptx.author = 'Higgins 2.0';
  pptx.company = 'Synergi AI';
  if (spec.title) pptx.title = spec.title;

  applyBranding(pptx);

  for (const s of spec.slides) {
    switch (s.layout) {
      case 'title-card':    addTitleCard(pptx, s); break;
      case 'title-bullets': addTitleBullets(pptx, s); break;
      case 'two-column':    addTwoColumn(pptx, s); break;
      case 'section-break': addSectionBreak(pptx, s); break;
    }
  }

  const data = (await pptx.write({ outputType: 'nodebuffer' })) as Buffer;
  return data;
}
