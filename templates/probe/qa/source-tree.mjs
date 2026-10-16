/**
 * A content identity for the PROBE working tree, including uncommitted files.
 * Advisory/participant-reported only; never a game-exp trusted Candidate identity.
 */
import { createHash } from "node:crypto";
import { lstatSync, readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";

const SOURCE_EXCLUDES = new Set([".git", ".probe", "dist", "node_modules", "artifacts", "coverage", ".cache", ".venv"]);

export function sourceTreeSha256(root) {
  const rootInfo = lstatSync(root);
  if (rootInfo.isSymbolicLink() || !rootInfo.isDirectory()) throw new Error("source root must be a real directory");
  const digest = createHash("sha256");
  function visit(current) {
    const names = readdirSync(current).sort((a, b) => Buffer.compare(Buffer.from(a, "utf8"), Buffer.from(b, "utf8")));
    for (const name of names) {
      if (SOURCE_EXCLUDES.has(name)) continue;
      const full = join(current, name);
      const rel = relative(root, full).replaceAll("\\", "/");
      const entry = lstatSync(full);
      if (entry.isSymbolicLink()) throw new Error("source tree contains symlink: " + rel);
      if (entry.isDirectory()) visit(full);
      else if (entry.isFile()) {
        digest.update(rel, "utf8");
        digest.update("\0");
        digest.update(readFileSync(full));
        digest.update("\0");
      } else throw new Error("unsupported source tree entry: " + rel);
    }
  }
  visit(root);
  return digest.digest("hex");
}
