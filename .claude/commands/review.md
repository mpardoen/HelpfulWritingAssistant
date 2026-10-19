---
description: Have every reader persona read a chapter, comment on it and update their memory
argument-hint: <chapter-file> [reader ...]
---

Have the readers read a chapter. Arguments: `$ARGUMENTS`. The first is the chapter; any others are reader names, to limit the review to those readers. The layout and rules are in `CLAUDE.md`.

1. Run `python tools/book.py extract "<chapter>"` (use `python3` if `python` is not found). It writes the chapter's `text.md` and prints its context: `work`, `profile`, `key`, `dir`, `text`, `previous_tomes`, `earlier`, `later_already_reviewed`. If it fails, show the author the error and stop; if several chapters match, ask which one.

2. Run `python tools/book.py readers` for the list of readers. If names were given, keep only those and report any that do not exist. If there are no readers at all, say so and point to `/new-reader`. If `previous_tomes` is not empty, check that every reader has a `_tome.md` for each of those works; if one is missing, stop and tell the author to run `/close-tome <tome>` first.

3. Start one `reader` agent per reader, in **chapter** mode, all in a single message so they read in parallel. Give each one paths, not content:
   - reader name, and `readers/<name>/PERSONALITY.md`
   - chapter text: `<dir>/text.md`
   - the profile, for its `Reader review` and `Reader memory` sections only
   - memory files it may read, in this order: `readers/<name>/memory/<tome>/_tome.md` for each work in `previous_tomes`, oldest first; then `readers/<name>/memory/<work>/<key>.md` for each key in `earlier` (some may not exist if the reader skipped a chapter; say so); plus anything in `readers/<name>/memory/` belonging to other works
   - outputs: `<dir>/reviews/<name>.md` and `readers/<name>/memory/<work>/<key>.md`

   Give them nothing else. In particular, do not pass the chapter record, the proofreading report, `BOOK.md`, or anything about the other readers: a reader who knows more than a reader would stops being useful.

4. When all have returned, run `python tools/book.py list <work>` and check that each reader appears in the chapter's `reviews` as `current`, and that each memory file exists. Report any reader whose files are missing.

5. Give the author a digest: one line per reader (rating and reaction), each followed by their favourite part so far when it changed with this chapter, then what several readers agree on and where they disagree, then the folder holding the comments. Build this from the agents' replies; open the review files only if a reply is unclear.

6. If `later_already_reviewed` is not empty, add a note: the readers' memories of those later chapters were formed from the previous draft of this one, and `/review` on them (or `/reread <work>`) would refresh them.

Reviewing a chapter again replaces each reader's earlier comment and memory of it.
