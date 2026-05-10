"use client";

import { forwardRef } from "react";
import { Entity } from "@/lib/api";
import { getEntityColor } from "@/lib/entity-colors";

interface Props {
  text: string;
  entities: Entity[];
  approved: Record<string, boolean>;
  mode: "original" | "pseudonymized";
  title: string;
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export const DocumentPanel = forwardRef<HTMLDivElement, Props>(
  function DocumentPanel({ text, entities, approved, mode, title }, ref) {
    const active = entities
      .map((ent, i) => ({ ent, i }))
      .filter(({ i }) => approved[String(i)] !== false)
      .sort((a, b) => a.ent.start - b.ent.start);

    const typeCounts: Record<string, number> = {};
    const pseudonymMap: Record<string, string> = {};

    for (const { ent } of active) {
      const key = `${ent.type}::${ent.text}`;
      if (!pseudonymMap[key]) {
        typeCounts[ent.type] = (typeCounts[ent.type] || 0) + 1;
        pseudonymMap[key] = `[${ent.type}_${typeCounts[ent.type]}]`;
      }
    }

    const parts: string[] = [];
    let last = 0;

    for (const { ent } of active) {
      if (ent.start > last) {
        parts.push(escapeHtml(text.slice(last, ent.start)));
      }

      const color = getEntityColor(ent.type);
      const original = escapeHtml(text.slice(ent.start, ent.end));
      const key = `${ent.type}::${ent.text}`;
      const display = mode === "pseudonymized" ? escapeHtml(pseudonymMap[key]) : original;
      const sourceIcon = ent.source === "llm" ? "🤖 " : "";
      const tooltip = `${color.label} (${ent.source})`;

      parts.push(
        `<span class="inline ${color.bg} border rounded px-0.5 cursor-default transition-colors" title="${tooltip}">${sourceIcon}<span class="font-semibold ${color.fg}">${display}</span></span>`
      );
      last = ent.end;
    }

    if (last < text.length) {
      parts.push(escapeHtml(text.slice(last)));
    }

    const html = parts.join("");

    return (
      <div className="flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-3 shrink-0">
          <h3 className="text-sm font-semibold text-neutral-500 uppercase tracking-wide">
            {title}
          </h3>
          {mode === "original" && (
            <span className="text-[11px] text-violet-500 font-medium">
              Zaznacz tekst, aby dodać encję
            </span>
          )}
          {mode === "pseudonymized" && (
            <span className="text-xs text-green-600 font-medium">
              Dane zastąpione
            </span>
          )}
        </div>
        <div
          ref={ref}
          className="relative flex-1 min-h-0 overflow-y-auto rounded-lg border border-neutral-200 bg-neutral-50"
        >
          <div
            className="p-5 font-mono text-[13px] leading-7 whitespace-pre-wrap break-words select-text"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        </div>
      </div>
    );
  }
);
