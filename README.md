# Helpful Writing Assistant

A [Claude Code](https://claude.com/claude-code) workspace for authors who write long works one chapter at a time. Drop a chapter in, and get:

- **a proofread**: spelling, grammar and typography, style, and consistency with everything written before, as a report with paragraph references. Your chapter is never modified.
- **a panel of readers**: personas you define, each with their own tastes and their own memory of your work so far, who comment on the new chapter the way that person would.
- **a whole-work analysis** when a tome is finished, and a way to have your readers re-read everything from the start after a rewrite.

It is not tied to fiction. What gets checked comes from a *profile*; two are included (`fiction`, `academic`) and you can write your own.

## Requirements

- Claude Code
- Python 3 (no packages to install)

## Getting started

1. Create your own copy with **Use this template** on GitHub (or clone and re-point the remote). Keep your copy **private** while your manuscript is unpublished: the reports quote it.
2. Open the folder in Claude Code.
3. Create a work: `/new-book book-1`
4. Create one or more readers: `/new-reader marguerite`
5. Save a chapter in the work's folder, with a number in its name: `book-1/chapter-1.docx`. Word (`.docx`), Markdown, plain text and LaTeX are supported.
6. Run `/proofread chapter-1.docx` and `/review chapter-1.docx`, in either order.

## Commands

| Command | What it does |
|---|---|
| `/new-book <folder>` | Creates a work and its `BOOK.md` (title, profile, your deliberate choices). |
| `/new-reader <name>` | Creates a reader persona by asking you about them. |
| `/split-book <book.docx> [work]` | Cuts a whole-book `.docx` into one `.docx` per chapter and files them in the work folder. |
| `/proofread <chapter-file>` | Editorial pass. Writes `proofread.md` and a neutral `record.md` of the chapter. |
| `/review <chapter-file> [reader ...]` | Every reader (or only those named) reads the chapter, writes a comment and updates their memory. |
| `/tome-analysis <work>` | An editor re-reads the entire work and writes an analysis of the whole. |
| `/reread <work> [reader ...]` | Readers set aside their memory of the work and re-read it from chapter one, then give a verdict on the whole. |

## Where things go

```
book-1/
  BOOK.md                     about the work; read by the proofreader, never by readers
  chapter-1.docx              your file
  chapter-1/
    text.md                   your chapter as text, with [¶n] paragraph numbers
    proofread.md              the editorial report
    record.md                what the chapter establishes
    reviews/marguerite.md     one comment per reader
  analysis/
    editor.md                 from /tome-analysis
    readers/marguerite.md     from /reread
readers/
  marguerite/
    PERSONALITY.md            who she is
    memory/book-1/chapter-1.md    what she remembers of each chapter
```

Reports point at passages with the paragraph numbers of `text.md` and quote the words, so you can search for them in your own file.

## How it works

**Proofreading stays fast on a long work** because earlier chapters are not re-read. Each `/proofread` leaves a `record.md` listing what the chapter established (names, descriptions, dates, definitions, numbers), and the next chapter is checked against those records. The trade-off: a contradiction with a detail that no record noted will not be caught until `/tome-analysis`, which reads everything.

**Readers remember subjectively.** After each chapter, a reader writes down what *they* retained, in their own words. A skimmer forgets names; a nitpicker remembers the eye colour. That file is all they know of the chapter when the next one arrives. Readers never see the records, the proofreading report or each other's comments.

**Rewriting a chapter** and running a command on it again replaces the earlier report, comment or memory for that chapter. Git keeps the old versions, and `text.md` gives you a readable diff of a `.docx` between drafts. Run `python tools/book.py list book-1` to see which reports are based on an older draft.

**Language.** Everything is written in the language of the chapter, with that language's spelling and typographic rules.

## Starting from a finished manuscript

If your book is a single `.docx`, run `/split-book my-book.docx book-1`. It shows how it would cut the book (chapter titles and word counts) before writing anything, then creates `book-1/01-<title>.docx`, `02-<title>.docx` and so on. Each chapter file keeps your styles, formatting and footnotes; your original is left untouched, and anything before the first chapter goes to `_front-matter.docx`.

It cuts at Word heading styles (Heading 1 by default, or another level if your Heading 1 is used for parts). If your chapter titles are plain text, it looks for lines such as "Chapter 3" or "Chapitre III", and you can give it your own pattern. From then on, edit and review the chapter files.

## Two examples

### A web serial

`/new-book arc-1` with the `fiction` profile. In `BOOK.md`, under *Deliberate choices*, note the tense and point of view and list invented names in the glossary so they are not flagged as typos. Publish rhythm suggests running `/proofread` before posting and `/review` to see whether the instalment gives readers a reason to return.

A reader for it, `readers/kev/PERSONALITY.md`:

> **Who they are.** Kevin, 24, night-shift nurse. Reads serials on his phone during breaks, three or four at a time, and drops one the moment it bores him.
> **What they love.** Momentum, banter, a cliffhanger. Characters who are competent at something.
> **What they cannot stand.** Two paragraphs of landscape. Recaps. A protagonist who whines.
> **How they read.** Fast, skipping description. Remembers who is funny and who betrayed whom; forgets place names and anything said only once.
> **Their voice.** Three lines, lower case, blunt. "ok the lighthouse bit was cool but i skipped half of it ngl".

### A PhD thesis

`/new-book thesis` with the `academic` profile, chapters as `.tex` or `.md`. In `BOOK.md`, state the thesis in a few sentences, list your notation, and name the citation style if you want it enforced. Here consistency means terminology, notation, numbers and claims: the proofreader will tell you when chapter 5 uses "latency" differently from the definition in chapter 2, or reports a sample size that chapter 3 gave otherwise.

A reader for it, `readers/examiner/PERSONALITY.md`:

> **Who they are.** Professor in a neighbouring field, twenty years of sitting on committees, agreed to be external examiner and reads the thesis over two weekends with a pencil.
> **What they love.** A claim, the evidence, and the limits, in that order. A chapter that says early what it will show.
> **What they cannot stand.** "It is well known that". Results presented before the method. A contribution announced in the introduction and never mentioned again.
> **How they read.** Every page, in order, writing questions in the margin. Remembers each promise the author makes and checks it later.
> **Their voice.** Courteous, numbered points, each ending in a question the candidate will have to answer.

## Writing your own profile

Copy `profiles/_TEMPLATE.md` to `profiles/<name>.md` and fill in its seven sections: what a chapter record must contain, what consistency means, what to look at in the style, how a reader's comment and memory are laid out, the rubric for the whole-work analysis, and example readers. Then set `profile: <name>` in your work's `BOOK.md`. A memoir, a textbook, a screenplay or a game script each deserve their own.

## Costs to be aware of

`/proofread` runs one agent on one chapter plus the short records of earlier chapters. `/review` runs one agent per reader, in parallel. `/tome-analysis` and `/reread` read the whole work (once for the editor, once per reader) and are meant for milestones. To use a cheaper model for readers, add `model: sonnet` to the front matter of `.claude/agents/reader.md`.

## Getting template updates

The template's own files are `README.md`, `LICENSE`, `CLAUDE.md`, `.claude/`, `tools/`, `profiles/fiction.md`, `profiles/academic.md`, `profiles/_TEMPLATE.md` and `readers/_TEMPLATE/`. Your works, readers and added profiles live elsewhere, so you can merge from the template without conflicts:

```
git remote add template <url of the template repository>
git fetch template
git merge template/main --allow-unrelated-histories
```

If you customise an included profile, copy it under a new name first so that an update does not overwrite your changes.

## Limits

- The proofreader is a language model. It catches most errors and misses some, and it will occasionally flag something that is correct; items it is unsure about are listed separately as questions.
- Reader personas are simulations. They are good at showing where a chapter drags or confuses, and no substitute for real readers.
- In `.docx` files, text in tracked deletions is ignored and tracked insertions are read as accepted. Comments, images, equations and tables' layout are not extracted (table text is).

## Licence

MIT. See `LICENSE`. The licence covers the template, not what you write with it.
