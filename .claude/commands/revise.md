---
description: Have the readers rate a rewritten chapter against their memory of the old one
argument-hint: <old-chapter-file> <new-chapter-file> [reader ...]
---

Have the readers judge a revised chapter. Arguments: `$ARGUMENTS`. The first is the old draft, the second the new one (the chapter file in its work folder); any others are reader names, to limit the revision to those readers. If the author edited the chapter in place, the old and the new file are the same path; the previous extraction (`text.md`) then serves as the old draft. The layout and rules are in `CLAUDE.md`.

1. Run `python tools/book.py revise "<old>" "<new>"` (use `python3` if `python` is not found). It saves the old draft as `<dir>/versions/<timestamp>.md`, extracts the new one, writes the paragraph diff next to the old draft, and prints the chapter's context (`work`, `profile`, `key`, `dir`, `text`, `previous_tomes`, `earlier`, `later_already_reviewed`) and `old_text`, `diff`, `changes`. If it fails, show the author the error and stop; if several chapters match, ask which one.

2. Run `python tools/book.py readers` for the list of readers; keep only the named ones if names were given, report any that do not exist. A reader with no memory file at `readers/<name>/memory/<work>/<key>.md` never read this chapter: skip them and say that `/review` comes first. If `previous_tomes` is not empty, a missing `_tome.md` of a previous tome stops the command: tell the author to run `/close-tome <tome>` first.

3. For each remaining reader, run `python tools/book.py rewind "<work>" "<key>" "<name>"`. It puts away the reader's memory of the chapters after this one, which describe a story that no longer exists. Note where each went.

4. Start one `reader` agent per reader, in **revision** mode, all in a single message. Give each one paths, not content:
   - reader name, and `readers/<name>/PERSONALITY.md`
   - old text: the `old_text` path; new text: `<dir>/text.md`; the diff path
   - the profile, for its `Reader review` and `Reader memory` sections only
   - memory files it may read, in this order: `readers/<name>/memory/<tome>/_tome.md` for each work in `previous_tomes`, oldest first; then `readers/<name>/memory/<work>/<k>.md` for each key `<k>` in `earlier`; then its previous memory of this chapter (`readers/<name>/memory/<work>/<key>.md`), plus anything in `readers/<name>/memory/` belonging to other works (never `_archive/`)
   - its previous comment: `<dir>/reviews/<name>.md`
   - outputs: `<dir>/reviews/<name>.md` and `readers/<name>/memory/<work>/<key>.md`
   - when they exist, `readers/<name>/memory/<work>/_tome.md` and `<work>/analysis/readers/<name>.md`, which it may adjust if the revision changes what it would say there

   Give them nothing else. In particular, do not pass the chapter record, the proofreading report, `BOOK.md`, or anything about the other readers.

5. When all have returned, run `python tools/book.py list <work>` and check that each reader appears in the chapter's `reviews` as `current` and that each memory file exists. Report any that is missing.

6. Give the author a digest: how the diff looks (`changes`), one line per reader (verdict on the change, rating of the new version), what several readers agree on and where they disagree, and the folder holding the comments.

7. Remind the author of what is now out of date: the memories of the chapters after this one were archived for these readers (their comments on those chapters remain but describe the old story), so `/review` on the next chapters, or `/reread <work>`, brings them back in line. If `later_already_reviewed` is not empty, name those chapters. If the revised work has later tomes, say that their `_tome.md` was left as it was, apart from what the readers adjusted.

The comment and the memory of the chapter are replaced; git keeps the earlier ones. A `.diff.md` is generated: it starts with the new `text.md` hash, so `list` is not affected.
