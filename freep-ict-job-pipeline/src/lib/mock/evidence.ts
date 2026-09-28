// Mock source-evidence store, keyed by evidence_ref.
//
// The real pipeline stores a source excerpt per evidence_ref (raw text
// around the extracted value, per brief §4.1 "Raw content"). Until the
// API exists, this simulates what a future
// GET /jobs/{id}/evidence/{evidence_ref} would return, so evidence links
// in Job detail show something real instead of a dead link.

export type SourceEvidence = {
  evidence_ref: string;
  excerpt: string;
  source_url: string;
};

const EVIDENCE: Record<string, SourceEvidence> = {
  "src-1247-1": {
    evidence_ref: "src-1247-1",
    excerpt: "…gezocht: een ervaren Data Analyst. Vereisten: minimaal 5 jaar ervaring met data-analyse in een vergelijkbare rol…",
    source_url: "https://www.freep.nl/opdracht/88213",
  },
  "src-1247-2": {
    evidence_ref: "src-1247-2",
    excerpt: "…kennis van SQL en Python is een harde eis voor deze opdracht…",
    source_url: "https://www.freep.nl/opdracht/88213",
  },
  "src-1247-3": {
    evidence_ref: "src-1247-3",
    excerpt: "…ervaring met Power BI is een pre, maar geen harde eis…",
    source_url: "https://www.freep.nl/opdracht/88213",
  },
  "src-1247-4": {
    evidence_ref: "src-1247-4",
    excerpt: "…gunningscriteria: CV en motivatie wegen voor 60% mee in de beoordeling…",
    source_url: "https://www.freep.nl/opdracht/88213",
  },
  "src-1247-5": {
    evidence_ref: "src-1247-5",
    excerpt: "…het interview weegt voor 40% mee in de eindbeoordeling…",
    source_url: "https://www.freep.nl/opdracht/88213",
  },
  "src-1247-6": {
    evidence_ref: "src-1247-6",
    excerpt: "…gewenste competentie: sterk analytisch vermogen…",
    source_url: "https://www.freep.nl/opdracht/88213",
  },
};

export function getEvidence(evidenceRef: string): SourceEvidence | null {
  return EVIDENCE[evidenceRef] ?? null;
}
