import type { ScanRun } from "@/lib/contracts/scan";

import scan20250928 from "@/mock/scans/scan-20250928-1714.json";
import scan20250921 from "@/mock/scans/scan-20250921-0930.json";

const scans = [scan20250928, scan20250921] as ScanRun[];

export function getScans(): ScanRun[] {
  return scans;
}

export function getLatestScan(): ScanRun {
  return scans[0];
}

export function getScan(scanId: string): ScanRun | null {
  return scans.find((scan) => scan.scan_id === scanId) ?? null;
}
