// gta6-meme-x-01 entry (Node 22, standard library only).
//
// The entry is the X post itself: an AI agent made a GTA 6 meme with the
// make.fun ghost in the picture, it is posted on X from a public account
// with make.fun (a link or written out) and/or a tag of @makefunai and a
// play code in its text, and POST.json names the post. The house reads the
// post from X (its first picture and its text) and hands that to the judge.
// So this program only has one job: hand POST.json to the gate by writing
// it into the output directory. Nothing it writes about the post is judged.
//
// Local run (from the repository root):
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
// After that, out/POST.json is byte for byte this directory's POST.json.

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

// The grader runs with /bot and /output; locally the two env vars stand in.
const botDir = process.env.MAKEFUN_BOT_DIR ?? "/bot";
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

const source = join(botDir, "POST.json");
const target = join(outDir, "POST.json");

let text: string;
try {
  text = readFileSync(source, "utf8");
} catch (err) {
  console.error(`cannot read ${source}: ${(err as Error).message}`);
  process.exit(1);
}

// The gate reads POST.json as JSON, so refuse to hand it a broken file.
let parsed: unknown;
try {
  parsed = JSON.parse(text);
} catch (err) {
  console.error(`POST.json is not valid JSON: ${(err as Error).message}`);
  process.exit(1);
}
if (
  typeof parsed !== "object" ||
  parsed === null ||
  typeof (parsed as { url?: unknown }).url !== "string"
) {
  console.error("POST.json must be an object with a string url");
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });
writeFileSync(target, text);
console.log(`wrote ${target}`);
