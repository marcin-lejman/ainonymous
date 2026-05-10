"use client";

import { getEntityColor } from "@/lib/entity-colors";

interface Props {
  text: string;
  mapping: Record<string, string>; // placeholder -> real value
  mode: "pseudonymized" | "restored";
  title: string;
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function highlightPlaceholders(text: string, mapping: Record<string, string>, mode: "pseudonymized" | "restored"): string {
  const regex = /\[([A-Z_]+?)_(\d+)\]/g;
  const matches: { match: string; type: string; index: number }[] = [];
  let m;
  while ((m = regex.exec(text)) !== null) {
    matches.push({ match: m[0], type: m[1], index: m.index });
  }

  if (matches.length === 0) return escapeHtml(text);

  const parts: string[] = [];
  let last = 0;

  for (const { match, type, index } of matches) {
    if (index > last) parts.push(escapeHtml(text.slice(last, index)));

    const color = getEntityColor(type);
    const realValue = mapping[match];
    const display = mode === "restored" && realValue ? escapeHtml(realValue) : escapeHtml(match);
    const tooltip = realValue ? `${match} → ${realValue}` : match;

    parts.push(
      `<span class="inline ${color.bg} border rounded px-0.5 cursor-default" title="${escapeHtml(tooltip)}"><span class="font-semibold ${color.fg}">${display}</span></span>`
    );
    last = index + match.length;
  }

  if (last < text.length) parts.push(escapeHtml(text.slice(last)));
  return parts.join("");
}

function highlightRestoredValues(text: string, mapping: Record<string, string>): string {
  // Build: real value → { placeholder, type } sorted by length desc to avoid partial matches
  const entries = Object.entries(mapping)
    .map(([placeholder, realValue]) => {
      const typeMatch = placeholder.match(/\[([A-Z_]+?)_\d+\]/);
      return { placeholder, realValue, type: typeMatch?.[1] || "OTHER" };
    })
    .sort((a, b) => b.realValue.length - a.realValue.length);

  // Find all occurrences of real values in text
  const highlights: { start: number; end: number; type: string; placeholder: string; realValue: string }[] = [];

  for (const { placeholder, realValue, type } of entries) {
    let searchFrom = 0;
    while (true) {
      const idx = text.indexOf(realValue, searchFrom);
      if (idx < 0) break;
      // Check no overlap with existing highlights
      const overlaps = highlights.some(
        (h) => !(idx + realValue.length <= h.start || idx >= h.end)
      );
      if (!overlaps) {
        highlights.push({ start: idx, end: idx + realValue.length, type, placeholder, realValue });
      }
      searchFrom = idx + 1;
    }
  }

  if (highlights.length === 0) return escapeHtml(text);

  highlights.sort((a, b) => a.start - b.start);

  const parts: string[] = [];
  let last = 0;

  for (const h of highlights) {
    if (h.start > last) parts.push(escapeHtml(text.slice(last, h.start)));

    const color = getEntityColor(h.type);
    const tooltip = `${h.placeholder} → ${h.realValue}`;

    parts.push(
      `<span class="inline ${color.bg} border rounded px-0.5 cursor-default" title="${escapeHtml(tooltip)}"><span class="font-semibold ${color.fg}">${escapeHtml(h.realValue)}</span></span>`
    );
    last = h.end;
  }

  if (last < text.length) parts.push(escapeHtml(text.slice(last)));
  return parts.join("");
}

export function RestorePanel({ text, mapping, mode, title }: Props) {
  const html = mode === "pseudonymized"
    ? highlightPlaceholders(text, mapping, mode)
    : highlightRestoredValues(text, mapping);

  return (
    <div className="flex flex-col min-h-0">
      <div className="flex items-center justify-between mb-2 shrink-0">
        <h3 className="text-sm font-medium text-neutral-600">{title}</h3>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto rounded-lg border border-neutral-200 bg-neutral-50">
        <div
          className="p-5 font-mono text-sm leading-7 whitespace-pre-wrap break-words"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      </div>
    </div>
  );
}
