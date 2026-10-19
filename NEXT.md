# Next features

Feature 2 (tomes) is built. Feature 1 (`/revise`, `rewind`, `versions/`) is built too; not yet run with real readers.
Decision on the open question in feature 1: the revision agent edits `_tome.md` and the verdict only where the
revision changes what it would say, from the new chapter alone; they are not marked stale.

Build order: feature 2 first (chain resolution, `_tome.md`), then `rewind` and `/revise`, which depend on it.

---

## 1. Review of a revised chapter (`/revise`)

The author edits a chapter and asks the readers to rate the change. Each reader judges the new version against
their own impression of the old one, knowing only the earlier chapters.

### Keeping the old draft

- When `extract` sees that a chapter's source hash changed, it first copies the existing `text.md` to
  `<chapter>/versions/<timestamp>.md` (timestamp as `YYYYMMDD-HHMMSS`, same format as `archive-memory`).
  The timestamp, not the hash, names the file so that the order of drafts is known after several revisions.
- The copy keeps its first line, so its source hash is still readable.

### Command

`/revise <old-chapter-file> <new-chapter-file> [reader ...]`

The old chapter is an argument so the command knows which file is the old draft and which is the new one.
The old file is extracted to `text.md` form for reading (or, if it is the previous draft already saved under
`versions/`, that copy is used). The new file is extracted as usual, and becomes the current `text.md`.

Steps:
1. Extract old and new; save the old draft under `versions/` when it is not there yet.
2. `book.py rewind <work> <key> <reader>` for each reader (below).
3. Start one `reader` agent per reader in a new **revision** mode, all in one message, paths only.
4. Check files, digest for the author, same shape as `/review`, centred on the rating of the change.
5. Warn that later chapters' memories were archived (see rewind) and need `/review` or `/reread`.

### What the reader gets

- its memories of **all earlier chapters** (and of previous tomes' `_tome.md`, see feature 2);
- its own previous memory of this chapter and its own previous comment on it (`reviews/<name>.md`);
- the **full text of the old version** and the **full text of the new version**;
- the profile's `Reader review` and `Reader memory` sections, for layout only.

Never: `record.md`, `proofread.md`, `BOOK.md`, other readers' files, later chapters, `_archive/`.

### What the reader writes

- A comment on the **change**, rated against their previous impression and memory of the chapter: what improved,
  what got worse, what they liked in the old version that is gone, whether what bothered them before is fixed,
  what they now expect. Refer to `¶n` of the new text. It replaces `reviews/<name>.md`; the previous comment
  stays in git.
- A new memory of the chapter, replacing the old one, ending with the `<!-- favorite -->` block (same rules as
  today). The reader remembers the new version; it may keep a trace of the old one if the persona would.

### `book.py rewind <work> <key> <reader>`

Moves the reader's memories of every chapter after `<key>` **in the same work** into
`readers/<reader>/memory/_archive/<work>-after-<key>-<timestamp>/`, the way `archive-memory` works. The reader
then stands exactly where they were before reading this chapter, apart from their trace of the old draft.

### Effect on later tomes (see feature 2)

Revising a chapter does **not** invalidate the next tomes. Their chapter memories stay. The revision run may
however update, for a reader, two files describing the revised tome:
- `readers/<reader>/memory/<work>/_tome.md`, the reader's memory of the whole tome;
- the reader's whole-work verdict, `<work>/analysis/readers/<reader>.md`.

The reader changes them only where the revision changes what they would say. (The original note said
"report.md"; this assumes it means the reader's verdict file. Confirm.)

Open question: since `rewind` archives later chapter memories of the revised tome, `_tome.md` is partly built on
archived memories. Decide whether the revision agent edits it from the new chapter alone, or whether `_tome.md`
is marked stale until the tome is re-reviewed.

---

## 2. Tomes that follow earlier tomes

New tomes of a series assume the readers have read the previous ones. Readers **always** read tome 1 before
tome 2: no handling of readers who skipped a tome.

### Model

- A tome is a work (folder with `BOOK.md`). A work links to its predecessor with a front-matter line
  `follows: <work-folder>`. Chains of any length: tome 3 follows tome 2 follows tome 1.
- A reader's memory of a finished tome is one short file, `readers/<name>/memory/<work>/_tome.md` (about 400
  words), so that tome 2 does not need dozens of chapter memories of tome 1. Files starting with `_` are not
  chapters, so there is no clash with a chapter key.
- When reading tome N, a reader knows: the `_tome.md` of every earlier tome (oldest first), its chapter
  memories of the current tome so far, and the chapter.

---

## Implementation plan for feature 2

### Step 1. Chain resolution in `tools/book.py`

- `previous_tomes(work)`: follows `follows:` from `book_meta` to the root, returns the list oldest first.
  Fails clearly on a missing target (no `BOOK.md`) or a cycle.
- `extract` prints `previous_tomes: <work> <work>` (empty when none).
- `list` prints the same line plus, per previous tome, whether `readers/*/memory/<tome>/_tome.md` exists.
- New `book.py tome-memory <work> <reader>` is not needed: commands build the path
  `readers/<name>/memory/<tome>/_tome.md` themselves.

### Step 2. Reader agent (`.claude/agents/reader.md`)

- "What you know": add the `_tome.md` of previous tomes, given in order, before the chapter memories.
- New **tome** mode: given the work's title, the reader's chapter memories of that tome in order, the profile
  and one output path, write `_tome.md`: the story as this reader retains it, their feelings about the
  characters, their theories and open questions, their mood, and the `<!-- favorite -->` block.
  Built from the reader's memory only, never from chapter text: it is what they would still know.
- Favourite rule: when a tome-2 chapter has no earlier chapter memory yet, the "latest earlier favourite" is the
  one in the last previous tome's `_tome.md`. Keep-unless-clearly-beaten still applies across tomes.
- **reread** mode: after the verdict, also write `_tome.md`, so a re-read refreshes it.

### Step 3. New `/close-tome <work> [reader ...]`

Starts one `reader` agent per reader in tome mode (cheap: reads memories, not chapters). Checks that every
reader has memories for every chapter first, and reports the gaps. Run it when a tome is finished, before
starting reviews of the next tome. `/reread` produces the same file as a side effect.

### Step 4. `/review` and `/reread` (`.claude/commands/`)

- Memory list given to each reader becomes: `_tome.md` of each entry of `previous_tomes` in order, then the
  current tome's chapter memories (and other works' memories, as now).
- `archive-memory` stays scoped to the current work, so a re-read of tome 2 never touches tome 1's `_tome.md`.
- If a previous tome's `_tome.md` is missing for a reader, stop and tell the author to run `/close-tome` first
  (a check, not a fallback).

### Step 5. Proofreader, editor, `/new-book`

- `/proofread`: after the previous tomes' records exist, pass them to the proofreader ahead of the current
  tome's, in order. Extract and record any previous-tome chapter missing a record, as step 2 does today.
  Proofreader agent: reading order becomes `BOOK.md`, profile, records of previous tomes, records of earlier
  chapters, chapter.
- `/tome-analysis`: pass the previous tomes' `analysis/editor.md` when they exist, for continuity with what the
  editor already concluded. The editor still re-reads only the current tome in full.
- `/new-book`: ask "Does this work follow another one?" and write `follows:`. Offer to copy the previous tome's
  deliberate choices and glossary into the new `BOOK.md` as a starting point.

### Step 6. Readers panel (`.claude/skills/reader-crabs`)

Check `hooks/data.ts` and `crab.ts` for how they list a reader's memory files and read the favourite: a
`_tome.md` in the folder must not be counted as a chapter (the `_` prefix probably handles it, to be verified).
Decide whether the panel shows a tome's `_tome.md` favourite when the new tome has no chapter yet.

### Step 7. Docs and fixtures

- `CLAUDE.md`: layout gains `_tome.md` and `versions/`; the command table gains `/close-tome` (and `/revise`
  with feature 1); the isolation rule says the reader may read the `_tome.md` of previous tomes.
- `README.md`: author-facing section on series.
- Fixture: `test-serial-2/` with `follows: test-serial`, one chapter, to exercise the chain (`test-*` is
  git-ignored).

### Verification

1. `book.py extract` on a tome-2 chapter prints the right `previous_tomes`; a cycle and a missing target fail.
2. `/close-tome test-serial` writes `_tome.md` for each reader, ending with the favourite block.
3. `/review` on `test-serial-2` chapter 1: each reader's comment refers to tome 1 events, and the agent was
   given `_tome.md` before chapter memories.
4. `/reread test-serial-2` leaves tome 1's `_tome.md` untouched.
5. `/proofread` on tome 2 flags a deliberate contradiction with a tome-1 record.
6. The readers panel still shows the right crabs and satisfaction.
