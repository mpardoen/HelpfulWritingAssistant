---
description: Readers put away their memory of a work and re-read it from the first chapter
argument-hint: <work-folder> [reader ...]
---

Have the readers re-read a whole work from scratch. Arguments: `$ARGUMENTS`. The first is the work folder; any others are reader names, to limit the re-read to those readers. The layout and rules are in `CLAUDE.md`.

Use this after substantial rewriting, when the readers' chapter-by-chapter memories describe drafts that no longer exist.

1. Run `python tools/book.py list "<work>"` (use `python3` if `python` is not found) for the chapters in order and the profile, and `python tools/book.py readers` for the readers. Keep only the named readers if names were given.

2. Run `python tools/book.py extract` on every chapter whose `text` state is `missing` or `stale`.

3. For each reader, run `python tools/book.py archive-memory "<work>" "<name>"`. It moves `readers/<name>/memory/<work>/` to `readers/<name>/memory/_archive/<work>-<timestamp>/`, so the earlier memory is saved, not lost. Report where each one went.

4. Start one `reader` agent per reader, in **reread** mode, all in a single message. Give each one paths, not content:
   - reader name, and `readers/<name>/PERSONALITY.md`
   - the work's title, as `list` printed it
   - the profile, for its `Reader review` and `Reader memory` sections only
   - the chapters in order, each as a triple: `<work>/<key>/text.md`, the review path `<work>/<key>/reviews/<name>.md` and the memory path `readers/<name>/memory/<work>/<key>.md`
   - memory files of other works it may read first, if any exist in `readers/<name>/memory/` (never `_archive/`)
   - verdict output: `<work>/analysis/readers/<name>.md`

   As in `/review`, give them nothing else.

5. When all have returned, check that each reader has a review and a memory file for every chapter and a verdict file, and report any that are missing. Then give the author one line per reader (verdict and reaction), what they agree and disagree on, and the folder holding the verdicts.

The re-read overwrites the per-chapter comments in `<work>/<key>/reviews/` for the readers who took part, so they now describe the latest re-read (git keeps the earlier ones). Comments of readers who were not part of it are left as they are.
