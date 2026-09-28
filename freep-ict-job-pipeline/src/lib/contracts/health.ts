// Agreed scan frequency, per CLAUDE.md "Review UI > Health":
// "last successful scan and freshness against the agreed frequency".
//
// No frequency is defined elsewhere in the contract yet; this is the
// single source of truth until Dreev formalizes it (see brief §9.1 /
// CLAUDE.md work order step 1, "Discovery report on Freep").
export const AGREED_SCAN_FREQUENCY_HOURS = 24;
