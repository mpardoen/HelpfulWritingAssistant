---
description: Create a new work (book, tome, serial arc, thesis) with its BOOK.md
argument-hint: <folder-name>
---

Create a new work in the folder `$ARGUMENTS` at the project root. The layout and rules are in `CLAUDE.md`.

1. If no folder name was given, ask for one (short, no spaces: `book-1`, `thesis`, `arc-2`). If the folder already has a `BOOK.md`, say so and stop.

2. Ask the author, in one round of questions:
   - the title;
   - the profile: list the files in `profiles/` (except `_TEMPLATE.md`) with their first line. If none fits, offer to write a new profile from `profiles/_TEMPLATE.md` first;
   - what the work is, in a few sentences (premise or thesis statement, intended audience);
   - deliberate choices the proofreader must not flag: spelling variant, narrative tense and point of view, invented names and words, house notation, a citation style to enforce.

   Anything the author does not want to answer now can stay empty.

3. Write `<folder>/BOOK.md` in the author's language:

   ```
   ---
   title: <title>
   profile: <profile name, without .md>
   ---

   # <title>

   ## About
   <what the work is, who it is for>

   ## Deliberate choices
   <one bullet per choice; the proofreader and the editor leave these alone>

   ## Glossary
   <names, invented words and technical terms with their correct spelling; grows over time>
   ```

   Chapters are ordered by the first number in their file name. Only if the author's file names carry no usable number, add a `## Chapter order` section with one file name per bullet.

4. Tell the author where to put chapter files (directly in `<folder>/`, as `.docx`, `.md`, `.txt` or `.tex`, with a number in the name) and that `/proofread <file>` and `/review <file>` are the next steps. If `readers/` has no reader yet, mention `/new-reader`.

`BOOK.md` is read by the proofreader and the editor, never by the readers.
