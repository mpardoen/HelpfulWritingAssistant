---
description: Cut a whole-book .docx into one .docx per chapter, filed in a work folder
argument-hint: <book.docx> [work-folder]
---

Split a manuscript that is one `.docx` into chapter files. Arguments: `$ARGUMENTS`. The first is the `.docx`; the second, if given, is the work folder to file the chapters in. The layout and rules are in `CLAUDE.md`.

1. Settle the work folder. If one was named and it has a `BOOK.md`, use it. If it does not exist yet, or none was named, create the work first by following `.claude/commands/new-book.md` (suggest a folder name from the file name), then come back here.

2. Preview: run `python tools/book.py split "<book.docx>" "<work>"` (use `python3` if `python` is not found). Without `--write` it changes nothing and prints how it would cut the book: the headings it found, the level it split on, and each chapter file with its title and word count.

3. Judge the plan before writing anything. It is sound when the chapter titles are the book's real chapter titles and the word counts look like chapters. Signs that it is not, and what to do:
   - it split on parts and each file holds several chapters, or it split on scenes: rerun with `--level N`, using the `headings found` line to pick the level;
   - the book has no heading styles and the fallback missed chapters or caught ordinary lines: rerun with `--pattern "<regex>"`, a regular expression that matches a whole chapter-title paragraph (for example `Chapitre \d+.*` or `\d+`);
   - one file is many times larger than the others: a chapter title was probably typed without the style; tell the author which one.

   Show the author the final plan. If it is clearly sound, go on; if you had to guess, ask before writing.

4. Write: rerun the same command with `--write`. It refuses to replace existing files; add `--force` only if the author confirms they want the earlier split replaced, since they may have edited those chapters.

5. Report what was created, and mention:
   - text before the first chapter (title page, dedication) is saved as `_front-matter.docx`, which is kept out of the chapter list;
   - the original file is untouched. If it sits directly in the work folder, rename it with a leading `_` (the tool prints a warning when this applies) so it is not taken for a chapter;
   - from now on the chapter files are the ones to edit and review; the original is a snapshot.

6. Offer the next step without starting it: `/proofread` on the chapters in order (each one builds the record the next is checked against), and `/reread <work>` to have the readers go through the whole book. Both are substantial on a full book, so let the author choose.

Each chapter file keeps the original's styles, page setup, footnotes and formatting; only the body is cut. The split works on headings, so a book whose chapters are separated only by page breaks needs `--pattern`, or heading styles applied in Word first.
