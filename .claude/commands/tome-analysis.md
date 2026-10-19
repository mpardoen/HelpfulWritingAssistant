---
description: Full re-read of a work by the editor agent, with a whole-work analysis
argument-hint: <work-folder>
---

Produce the overall analysis of the work `$ARGUMENTS`. The layout and rules are in `CLAUDE.md`.

1. Run `python tools/book.py list "$ARGUMENTS"` (use `python3` if `python` is not found) for the chapters in order and the profile. If no work is named and `python tools/book.py works` shows exactly one, use it; otherwise ask.

2. Run `python tools/book.py extract` on every chapter whose `text` state is `missing` or `stale`, so the editor reads the current draft.

3. Start one `book-editor` agent with paths, not content:
   - `<work>/BOOK.md` and the profile
   - every chapter's `<work>/<key>/text.md`, in order
   - if the work follows other tomes (`python tools/book.py list "<work>"` prints `previous_tomes`): each previous tome's `analysis/editor.md` and `BOOK.md` when they exist, oldest first. The editor reads them for continuity and re-reads only this tome in full
   - output: `<work>/analysis/editor.md`
   - today's date

4. When it returns, check that `<work>/analysis/editor.md` exists, and give the author the revision priorities and the path of the analysis.

This re-reads everything and is the expensive command; it is meant for the end of a tome or a major milestone, not for every chapter. It does not involve the readers: use `/reread` for their view of the whole.
