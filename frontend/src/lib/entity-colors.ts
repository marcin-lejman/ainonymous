export const ENTITY_COLORS: Record<string, { fg: string; bg: string; label: string }> = {
  PERSON:       { fg: "text-blue-700",   bg: "bg-blue-50 border-blue-200",   label: "Osoba" },
  LOCATION:     { fg: "text-green-700",  bg: "bg-green-50 border-green-200",  label: "Lokalizacja" },
  ORGANIZATION: { fg: "text-purple-700", bg: "bg-purple-50 border-purple-200", label: "Organizacja" },
  EMAIL_ADDRESS:{ fg: "text-orange-700", bg: "bg-orange-50 border-orange-200", label: "E-mail" },
  PHONE_NUMBER: { fg: "text-teal-700",   bg: "bg-teal-50 border-teal-200",   label: "Telefon" },
  PESEL:        { fg: "text-red-700",    bg: "bg-red-50 border-red-200",     label: "PESEL" },
  NIP:          { fg: "text-red-700",    bg: "bg-red-50 border-red-200",     label: "NIP" },
  REGON:        { fg: "text-red-700",    bg: "bg-red-50 border-red-200",     label: "REGON" },
  KRS:          { fg: "text-red-700",    bg: "bg-red-50 border-red-200",     label: "KRS" },
  IBAN_CODE:    { fg: "text-red-700",    bg: "bg-red-50 border-red-200",     label: "IBAN" },
  CREDIT_CARD:  { fg: "text-red-700",    bg: "bg-red-50 border-red-200",     label: "IBAN" },
  REF_NUMBER:   { fg: "text-slate-700",   bg: "bg-slate-50 border-slate-200",  label: "Nr ref." },
  CONTEXTUAL:   { fg: "text-amber-700",  bg: "bg-amber-50 border-amber-200", label: "Kontekstowy" },
};

export const DEFAULT_COLOR = { fg: "text-gray-700", bg: "bg-gray-50 border-gray-200", label: "Inne" };

export function getEntityColor(type: string) {
  return ENTITY_COLORS[type] || DEFAULT_COLOR;
}

export function getSourceLabel(source: string): string {
  switch (source) {
    case "presidio": return "Automatyczny";
    case "llm": return "AI (Bielik)";
    case "manual": return "Ręczny";
    default: return source;
  }
}
