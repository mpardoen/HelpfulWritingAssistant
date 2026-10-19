---
description: Editorial pass on a chapter (spelling, style, consistency with earlier chapters)
argument-hint: <chapter-file>
---

Run the editorial pass on the chapter `$ARGUMENTS`. The layout and rules are in `CLAUDE.md`.

1. Run `python tools/book.py extract "$ARGUMENTS"` (use `python3` if `python` is not found). It writes the chapter's `text.md` and prints its context: `work`, `book`, `profile`, `dir`, `text`, `previous_tomes`, `earlier`, `earlier_without_record`. If it fails, show the author the error and stop; if several chapters match, ask which one. If the profile is marked MISSING, stop and say that `BOOK.md` names a profile that does not exist in `profiles/`.

2. For each chapter of each work in `previous_tomes` that has no `record.md` (see `python tools/book.py list <tome>`), and for each chapter in `earlier_without_record`: run `python tools/book.py extract` on it, then start a `proofreader` agent in **record only** mode with that chapter's `text.md`, the `BOOK.md` of the work it belongs to, the profile, and the output path `<tome>/<key>/record.md`. Run `extract` first with the chapter's path inside its own work. Start them all in one message so they run in parallel, and wait for them to finish: the next step needs their files.

3. Start one `proofreader` agent in **proofread** mode. Give it paths, not content:
   - chapter text: `<dir>/text.md`
   - `BOOK.md` and the profile
   - the records of the previous tomes, oldest first, each tome's chapters in order: `<tome>/<key>/record.md`
   - the earlier records of this work, in order: `<work>/<key>/record.md` for each key in `earlier`
   - outputs: `<dir>/proofread.md` and `<dir>/record.md`

4. When it returns, run `python tools/book.py list <work>` and check that the chapter shows `record=current` and `proofread=current`. If one is missing, say so plainly; if the agent's reply contains the content it could not write, write it to the intended path yourself.

5. Tell the author in a few lines: the count of items per section, the three priorities, and the path of the report. If `extract` printed `source: unchanged` and a report already existed, mention that the chapter had not changed since the last extraction.

Do not read the chapter or write the report yourself; the agent does both, which keeps this conversation small enough to proofread many chapters in a row.
