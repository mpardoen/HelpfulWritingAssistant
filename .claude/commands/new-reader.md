---
description: Create a reader persona from the template
argument-hint: <reader-name>
---

Create the reader `$ARGUMENTS`. The layout and rules are in `CLAUDE.md`.

1. If no name was given, ask for one. The folder name is the name in lower case with hyphens (`readers/aunt-lucie/`). Names starting with `_` or `test-` are reserved. If the reader exists, say so and stop.

2. Read `readers/_TEMPLATE/PERSONALITY.md` for the sections, and look at which works exist (`python tools/book.py works`) and at their profiles' `Typical readers` section, so your questions fit the kind of work this reader will read.

3. Ask the author about this person, in one round: who they are and why they are reading, what they usually read, what they love, what they cannot stand, how attentively they read and how well they remember, how severe they are, and how their comments sound. Take a free-form description if the author prefers to give one, and ask only about what is missing.

4. Write `readers/<name>/PERSONALITY.md` with the template's sections filled in and its comments removed. Make the person specific. Where the author left a gap, choose something concrete that fits the rest and tell the author what you chose, so they can change it. A reader described only as "critical but fair" produces comments nobody could tell apart from any other reader's.

5. Design the reader's crab for the readers panel, following steps 2 and 3 of `.claude/commands/draw-crabs.md` for this one reader, and write `readers/<name>/crab.md`. Mention the choice in one line.

6. Tell the author the reader will take part in the next `/review`, starting with no memory of any work. To have them catch up on chapters already written, run `/reread <work> <name>`.
