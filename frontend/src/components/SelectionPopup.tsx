"use client";

import { useEffect, useRef, useState } from "react";
import { getEntityColor } from "@/lib/entity-colors";

interface Props {
  containerRef: React.RefObject<HTMLDivElement | null>;
  onAdd: (text: string, type: string) => void;
}

const ENTITY_OPTIONS = [
  { type: "PERSON", label: "Osoba" },
  { type: "LOCATION", label: "Lokalizacja" },
  { type: "ORGANIZATION", label: "Organizacja" },
  { type: "PESEL", label: "PESEL" },
  { type: "NIP", label: "NIP" },
  { type: "KRS", label: "KRS" },
  { type: "REGON", label: "REGON" },
  { type: "IBAN_CODE", label: "IBAN / Nr konta" },
  { type: "PHONE_NUMBER", label: "Telefon" },
  { type: "EMAIL_ADDRESS", label: "E-mail" },
  { type: "REF_NUMBER", label: "Nr referencyjny" },
  { type: "CONTEXTUAL", label: "Kontekstowy" },
];

export function SelectionPopup({ containerRef, onAdd }: Props) {
  const [visible, setVisible] = useState(false);
  const [selectedText, setSelectedText] = useState("");
  const [position, setPosition] = useState({ x: 0, y: 0, below: false });
  const popupRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    function handleMouseUp() {
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed || !selection.toString().trim()) {
        return;
      }

      // Check if selection is within our container
      const range = selection.getRangeAt(0);
      if (!container!.contains(range.commonAncestorContainer)) {
        return;
      }

      const text = selection.toString().trim();
      if (text.length < 2) return;

      const rect = range.getBoundingClientRect();
      const containerRect = container!.getBoundingClientRect();

      const relX = rect.left - containerRect.left + rect.width / 2;
      const relTop = rect.top - containerRect.top;
      const relBottom = rect.bottom - containerRect.top;
      // Show below if selection is within 120px of container top
      const showBelow = relTop < 120;

      setSelectedText(text);
      setPosition({
        x: relX,
        y: showBelow ? relBottom + 8 : relTop - 8,
        below: showBelow,
      });
      setVisible(true);
    }

    function handleMouseDown(e: MouseEvent) {
      if (popupRef.current && popupRef.current.contains(e.target as Node)) {
        return;
      }
      setVisible(false);
    }

    container.addEventListener("mouseup", handleMouseUp);
    document.addEventListener("mousedown", handleMouseDown);

    return () => {
      container.removeEventListener("mouseup", handleMouseUp);
      document.removeEventListener("mousedown", handleMouseDown);
    };
  }, [containerRef]);

  function handleSelect(type: string) {
    onAdd(selectedText, type);
    setVisible(false);
    window.getSelection()?.removeAllRanges();
  }

  if (!visible) return null;

  return (
    <div
      ref={popupRef}
      className="absolute z-50 animate-in fade-in-0 zoom-in-95 duration-150"
      style={{
        left: position.x,
        top: position.y,
        transform: position.below ? "translate(-50%, 0)" : "translate(-50%, -100%)",
      }}
    >
      {/* Arrow on top (when popup is below selection) */}
      {position.below && (
        <div className="flex justify-center">
          <div className="w-2.5 h-2.5 bg-white border-l border-t border-neutral-200 transform rotate-45 mb-[-6px]" />
        </div>
      )}
      <div className="bg-white rounded-xl shadow-lg shadow-neutral-200/50 border border-neutral-200 p-1.5 min-w-[180px]">
        <p className="px-2 py-1 text-[11px] text-neutral-400 font-medium truncate max-w-[200px]">
          &quot;{selectedText.slice(0, 30)}{selectedText.length > 30 ? "…" : ""}&quot;
        </p>
        <div className="h-px bg-neutral-100 my-1" />
        {ENTITY_OPTIONS.map(({ type, label }) => {
          const color = getEntityColor(type);
          return (
            <button
              key={type}
              onClick={() => handleSelect(type)}
              className="flex items-center gap-2 w-full px-2 py-1.5 text-sm text-left rounded-lg hover:bg-neutral-50 transition-colors"
            >
              <span className={`w-2 h-2 rounded-full ${color.bg} border shrink-0`} />
              <span className="text-neutral-700">{label}</span>
            </button>
          );
        })}
      </div>
      {/* Arrow on bottom (when popup is above selection) */}
      {!position.below && (
        <div className="flex justify-center">
          <div className="w-2.5 h-2.5 bg-white border-r border-b border-neutral-200 transform rotate-45 -mt-[6px]" />
        </div>
      )}
    </div>
  );
}
