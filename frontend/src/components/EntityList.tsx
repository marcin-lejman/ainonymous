"use client";

import { Entity } from "@/lib/api";
import { getEntityColor, getSourceLabel } from "@/lib/entity-colors";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";

interface Props {
  entities: Entity[];
  approved: Record<string, boolean>;
  onToggleGroup: (indices: number[], value: boolean) => void;
}

interface EntityGroup {
  key: string;
  text: string;
  type: string;
  indices: number[];
  source: string;
  reason?: string;
}

function groupEntities(entities: Entity[]): EntityGroup[] {
  const map = new Map<string, EntityGroup>();

  entities.forEach((ent, i) => {
    const key = `${ent.type}::${ent.text}`;
    if (map.has(key)) {
      map.get(key)!.indices.push(i);
    } else {
      map.set(key, {
        key,
        text: ent.text,
        type: ent.type,
        indices: [i],
        source: ent.source,
        reason: ent.reason,
      });
    }
  });

  return Array.from(map.values());
}

export function EntityList({ entities, approved, onToggleGroup }: Props) {
  const groups = groupEntities(entities);

  return (
    <div className="space-y-0.5">
      {groups.map((group) => {
        const color = getEntityColor(group.type);
        const allActive = group.indices.every((i) => approved[String(i)] !== false);
        const count = group.indices.length;

        return (
          <div
            key={group.key}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
              allActive ? "hover:bg-neutral-50" : "opacity-40"
            }`}
          >
            <Switch
              checked={allActive}
              onCheckedChange={(v) => onToggleGroup(group.indices, v)}
              className="shrink-0"
            />

            <span className="flex-1 text-sm text-neutral-800 truncate font-medium" title={group.text}>
              {group.text.replace(/\n/g, " ").slice(0, 55)}
              {group.text.length > 55 ? "…" : ""}
            </span>

            {count > 1 && (
              <span className="shrink-0 text-[11px] text-neutral-400 tabular-nums">
                ×{count}
              </span>
            )}

            <Badge
              variant="outline"
              className={`shrink-0 text-[11px] font-semibold ${color.bg} ${color.fg} border`}
            >
              {color.label}
            </Badge>

            <span className="shrink-0 text-[11px] text-neutral-400 w-24 text-right">
              {group.source === "llm" ? "🤖" : group.source === "manual" ? "✋" : "⚙️"}{" "}
              {getSourceLabel(group.source)}
            </span>

            {group.reason && (
              <span
                className="shrink-0 text-[11px] text-amber-600 max-w-[200px] truncate"
                title={group.reason}
              >
                {group.reason}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
