---
description: Readers write their memory of a finished tome, for the tomes that follow it
argument-hint: <work-folder> [reader ...]
---

Have the readers condense their memory of a finished tome. Arguments: `$ARGUMENTS`. The first is the work folder; any others are reader names. The layout and rules are in `CLAUDE.md`.

Run this when a tome is finished, before reviewing the first chapter of a tome that follows it. It reads memories, not chapters, so it is cheap.

1. Run `python tools/book.py list "<work>"` (use `python3` if `python` is not found) for the chapters in order, the title, the profile and `previous_tomes`, and `python tools/book.py readers` for the readers. Keep only the named readers if names were given.

2. For each reader, check that `readers/<name>/memory/<work>/<key>.md` exists for every chapter. If some are missing, report them and ask the author whether to go on without those readers or run `/review` or `/reread` first. If the work has previous tomes, also check `readers/<name>/memory/<tome>/_tome.md` for each; if one is missing, say that `/close-tome <tome>` comes first.

3. Start one `reader` agent per reader, in **tome** mode, all in a single message. Give each one paths, not content:
   - reader name, and `readers/<name>/PERSONALITY.md`
   - the work's title
   - the profile, for its `Reader memory` section only
   - the reader's memory files for every chapter, in order: `readers/<name>/memory/<work>/<key>.md`
   - the `_tome.md` of each previous tome, oldest first
   - output: `readers/<name>/memory/<work>/_tome.md`

   Give them nothing else: no chapter text, no `record.md`, no `BOOK.md`.

4. When all have returned, check that each `_tome.md` exists and report any that is missing. Give the author one line per reader: their favourite part of the tome.

Running it again replaces each reader's `_tome.md` of that work.
