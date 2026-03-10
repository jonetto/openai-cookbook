# Project Instructions

## Output Conventions — Clickable File References

IMPORTANT: Every file or code location reference MUST be a clickable markdown link. Never use backticks alone for file paths.

Format (use relative paths from workspace root):
- File: [filename.js](path/to/filename.js)
- Specific line: [filename.js:42](path/to/filename.js#L42)
- Line range: [filename.js:42-51](path/to/filename.js#L42-L51)
- Folder: [src/utils/](src/utils/)

WRONG: `resources/js/ColppyManager/FuncionesGlobales.js`
RIGHT: [FuncionesGlobales.js:1329](resources/js/ColppyManager/FuncionesGlobales.js#L1329)

This applies to ALL responses — bug reports, explanations, code reviews, etc.

## Post-completion Verification — Docs & Infra

After modifying documentation (README, guides) or infrastructure scripts (shell scripts, docker-compose, CI):

1. **Cross-reference every claim against source.** For every "optional"/"required"/"automatic" statement:
   - `grep` the script for ALL references to that name — not just the one you remember
   - `grep` docker-compose.yml for `image:`, `build:`, `depends_on:` references
   - Check if `set -e` would cause a crash on the missing path
2. **Verify service names exactly.** Service names in commands/healthchecks must match docker-compose.yml service keys character-for-character (e.g. `postgresql` not `postgres` if that's what compose defines).
3. **Trace compose build contexts.** Any service with `build: context:` pointing to a repo path will fail `docker compose up` if that path doesn't exist — this is a compose-level hard dependency even if the setup script handles it gracefully.
4. **Run `bash -n`** on any modified shell scripts to catch syntax errors.
5. **Read the doc as a new developer.** For each instruction, ask: "If I literally follow only these steps on a clean machine with nothing pre-existing, does it work?" If not, document what's missing.
