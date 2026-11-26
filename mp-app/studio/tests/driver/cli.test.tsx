// نقطهٔ ورود CLI: فقط وقتی که scripts/agent_drive.mjs فرمان را از محیط می‌گیرد اجرا می‌شود.
import { writeFileSync } from "node:fs";
import { it } from "vitest";
import { parseArgv, runSteps } from "../../scripts/agent_drive.mjs";

it.skipIf(!process.env.MP_DRIVE_ARGV)("اجرای فرمان CLI و نوشتن JSON نتیجه", async () => {
  const argv = JSON.parse(process.env.MP_DRIVE_ARGV as string) as string[];
  const result = await runSteps(parseArgv(argv));
  writeFileSync(process.env.MP_DRIVE_OUT as string, JSON.stringify(result, null, 2) + "\n", "utf8");
});
