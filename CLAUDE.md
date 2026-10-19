# Writing-review workspace

This repository is a workspace for reviewing long-form writing chapter by chapter: novels, web serials, theses, any work written in chapters. The author writes; Claude proofreads, plays a panel of reader personas, and analyses the whole. `README.md` is the author-facing guide.

## Layout

```
profiles/<profile>.md               what to check for a kind of work (fiction, academic, ...)
readers/<name>/PERSONALITY.md       a reader persona
readers/<name>/crab.md              the reader's crab in the readers panel (colour, eyes, claws, accessory)
readers/<name>/memory/<work>/<chapter>.md    what that reader retains of each chapter
readers/<name>/memory/<work>/_tome.md   what that reader retains of a whole finished tome (from /close-tome or /reread)
readers/<name>/memory/_archive/     memories put away by /reread
tools/book.py                       extraction and listings (Python 3, standard library)
<work>/BOOK.md                      title, profile, deliberate choices, glossary
<work>/<chapter>.docx|.md|.txt|.tex the author's chapter
<work>/<chapter>/text.md            extracted text with [¶n] paragraph numbers
<work>/<chapter>/record.md         neutral record of the chapter
<work>/<chapter>/proofread.md       editorial report
<work>/<chapter>/reviews/<name>.md  one comment per reader
<work>/analysis/editor.md           whole-work analysis
<work>/analysis/readers/<name>.md   readers' verdicts after a full re-read
```

A work is any top-level folder with a `BOOK.md`. A later tome of a story is its own work whose `BOOK.md` front matter has `follows: <previous-work-folder>`; `python tools/book.py list <work>` shows the chain. Chapters are ordered by the first number in their file name, unless `BOOK.md` has a `## Chapter order` section. Files whose name starts with `_` are not chapters (a whole-book original, `_front-matter.docx`). `python tools/book.py list <work>` shows the order and the state of every report.

## Commands

| Command | Does |
|---|---|
| `/new-book <folder>` | creates a work and its `BOOK.md` |
| `/new-reader <name>` | creates a reader persona |
| `/split-book <book.docx> [work]` | cuts a whole-book `.docx` into one `.docx` per chapter in the work folder |
| `/proofread <chapter-file>` | spelling, style, consistency against earlier records; writes `proofread.md` and `record.md` |
| `/review <chapter-file> [reader ...]` | each reader comments on the chapter and updates their memory |
| `/draw-crabs [reader ...]` | designs the crab of each reader for the readers panel |
| `/close-tome <work> [reader ...]` | readers condense their chapter memories into one memory of the finished tome (`_tome.md`) |
| `/crabs [work]` | opens the readers panel: each reader's crab with satisfaction for the latest chapter and the whole work |
| `/tome-analysis <work>` | the editor re-reads everything and writes `analysis/editor.md` |
| `/reread <work> [reader ...]` | readers archive their memory and re-read the work from the start |

The work is done by the agents in `.claude/agents/` (`proofreader`, `reader`, `book-editor`). The commands only resolve paths and start them.

## Rules

- **Never write to a chapter's source file.** All feedback goes into reports. The author applies what they agree with. `text.md` is written only by `tools/book.py`.
- **Paths, not content.** Commands pass file paths to agents and relay their short replies. Do not read chapters into the main conversation for a review; that is what makes many chapters in one session possible.
- **Earlier chapters (and previous tomes) are known through `record.md` only** during `/proofread`. Only `/tome-analysis` re-reads full text.
- **Readers are isolated.** A reader agent sees its personality, its own memory of earlier chapters, its `_tome.md` of each previous tome, and the chapter. Never `record.md`, `proofread.md`, `BOOK.md`, other readers' files, later chapters, or `_archive/`.
- **Language follows the chapter.** Reports, records, comments and memories are written in the language of the chapter, applying that language's spelling and typography. Personality and profile files can be in any language.
- **Re-running replaces.** Generated files are overwritten; git keeps the history. Every generated file starts with the first line of the `text.md` it was based on, which carries the source's hash, so `tools/book.py list` can tell which reports describe an older draft (`stale`).
- **Profiles decide the criteria.** Nothing about what counts as consistency, what a chapter record contains or how a reader's comment is laid out belongs in commands or agents; it goes in `profiles/`.

## Engine and content

`README.md`, `LICENSE`, `CLAUDE.md`, `.claude/` (including the `reader-crabs` mod in `.claude/skills/`), `tools/`, `profiles/fiction.md`, `profiles/academic.md`, `profiles/_TEMPLATE.md` and `readers/_TEMPLATE/` are the shared template. Works, readers and any added profile are the author's content. Keep changes to the two apart so that template updates merge cleanly.

`test-*/` and `readers/test-*/` are local validation fixtures, ignored by git.

When the author asks for help outside the commands (discussing a scene, restructuring an argument, brainstorming), the same rules hold: read what is needed, answer in the conversation, and do not edit their chapter files unless they ask for that explicitly.
