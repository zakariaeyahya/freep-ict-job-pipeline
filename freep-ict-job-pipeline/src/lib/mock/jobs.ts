import type { JobRecord } from "@/lib/contracts/job";

// Fixtures live as individual JSON files (src/mock/jobs/*.json) so each one
// mirrors what a future GET /jobs/{internal_job_id} response looks like.
// Swap this loader for a fetch to the real API later; callers keep using
// the same JobRecord shape.
import job1231 from "@/mock/jobs/job-1231.json";
import job1232 from "@/mock/jobs/job-1232.json";
import job1233 from "@/mock/jobs/job-1233.json";
import job1238 from "@/mock/jobs/job-1238.json";
import job1239 from "@/mock/jobs/job-1239.json";
import job1240 from "@/mock/jobs/job-1240.json";
import job1241 from "@/mock/jobs/job-1241.json";
import job1242 from "@/mock/jobs/job-1242.json";
import job1243 from "@/mock/jobs/job-1243.json";
import job1244 from "@/mock/jobs/job-1244.json";
import job1245 from "@/mock/jobs/job-1245.json";
import job1246 from "@/mock/jobs/job-1246.json";
import job1247 from "@/mock/jobs/job-1247.json";

const jobs = [
  job1247,
  job1246,
  job1245,
  job1244,
  job1243,
  job1242,
  job1241,
  job1240,
  job1239,
  job1238,
  job1233,
  job1232,
  job1231,
] as JobRecord[];

export function getJobs(): JobRecord[] {
  return jobs;
}

export function getJob(internalJobId: string): JobRecord | null {
  return jobs.find((job) => job.identity.internal_job_id === internalJobId) ?? null;
}
