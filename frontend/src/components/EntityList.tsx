"use client";

import { Entity } from "@/lib/api";
import { getEntityColor, getSourceLabel } from "@/lib/entity-colors";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";

interface Props {
  entities: Entity[];
  approved: Record<string, boolean>;
  onToggle: (index: number, value: boolean) => void;
}

export function EntityList({ entities, approved, onToggle }: Props) {
  return (
    <div className="space-y-1">
      {entities.map((ent, i) => {
        const color = getEntityColor(ent.type);
        const isActive = approved[String(i)] !== false;
        return (
          <div
            key={i}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group ${
              isActive ? "hover:bg-neutral-50" : "opacity-40"
            }`}
          >
            <Switch
              checked={isActive}
              onCheckedChange={(v) => onToggle(i, v)}
              className="shrink-0"
            />

            <span className="flex-1 text-sm text-neutral-800 truncate font-medium" title={ent.text}>
              {ent.text.replace(/\n/g, " ").slice(0, 60)}
              {ent.text.length > 60 ? "…" : ""}
            </span>

            <Badge
              variant="outline"
              className={`shrink-0 text-[11px] font-semibold ${color.bg} ${color.fg} border`}
            >
              {color.label}
            </Badge>

            <span className="shrink-0 text-[11px] text-neutral-400 w-24 text-right">
              {ent.source === "llm" ? "🤖" : ent.source === "manual" ? "✋" : "⚙️"}{" "}
              {getSourceLabel(ent.source)}
            </span>

            {ent.reason && (
              <span
                className="shrink-0 text-[11px] text-amber-600 max-w-[200px] truncate"
                title={ent.reason}
              >
                {ent.reason}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
