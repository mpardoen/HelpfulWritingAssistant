---
description: Give each reader a crab for the readers panel (or redraw one)
argument-hint: [reader ...]
---

Design the crab each reader shows in the readers panel (`/crabs`). Arguments: `$ARGUMENTS`. With no argument, do every reader that has no `readers/<name>/crab.md` yet; with names, redo those readers even if they have one. The layout and rules are in `CLAUDE.md`.

1. List the readers with `python tools/book.py readers` (use `python3` if `python` is not found), keeping the ones to do.

2. For each, read `readers/<name>/PERSONALITY.md` and write `readers/<name>/crab.md`, four recipe lines plus a note, one `key: value` per line, values only from these lists:
   - `color`: red, orange, yellow, green, teal, cyan, blue, purple, pink, white, grey, brown
   - `eyes`: round, wide, sleepy, sharp, worried, squint, star, happy
   - `claws`: big, small, raised, crossed
   - `accessory`: none, glasses, monocle, scarf, hat, crown, bow, headphones, book, pencil
   - `note`: one short line in the language of the personality file, saying what the crab is meant to say about the person.

3. Make the crab say something true about the person, and different from the other crabs. Rough guide: severe readers get `sharp` or `squint` eyes and `crossed` or `big` claws; dreamy or easily bored ones `sleepy` or `star`; enthusiasts `wide` or `happy` with `raised` claws; careful, note-taking readers `glasses` or `monocle`; romantics `bow` or pink; commuters and skimmers `headphones`; scholars `book`. Colour follows temperament (warm for passionate, cool for detached). Before writing, check the crabs already in `readers/*/crab.md` and avoid repeating a combination.

4. Tell the author, one line per reader: the combination chosen and why. They can edit `crab.md` by hand at any time; the panel picks it up within seconds.
