#!/usr/bin/env python3
"""Helper for the writing-review workflow. Standard library only.

  book.py extract <chapter>          write <work>/<chapter>/text.md and print the chapter's context
  book.py list <work>                chapters of a work, in order, with the state of their reports
                                     (and the tomes it follows, with each reader's memory of them)
  book.py works                      folders that contain a BOOK.md
  book.py readers                    folders in readers/ that contain a PERSONALITY.md
  book.py archive-memory <work> <reader>
                                     move a reader's memory of a work to memory/_archive/
  book.py split <book.docx> <work> [--level N] [--pattern REGEX] [--write] [--force]
                                     cut a whole-book .docx into one .docx per chapter in <work>/
                                     (prints the plan; nothing is written without --write)

<chapter> is a path, a file name, or a file name without extension.
"""
import argparse
import datetime
import difflib
import hashlib
import html
import re
import shutil
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_EXTS = {".docx", ".md", ".txt", ".tex"}
NOT_CHAPTERS = {"book.md", "readme.md"}

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
# Tracked deletions and the legacy duplicate of drawing content are not part of the text.
SKIP = {W + "del", W + "moveFrom", MC + "Fallback"}
NOTE_SEPARATORS = {"separator", "continuationSeparator", "continuationNotice"}


def fail(message, code=1):
    print("error: " + message, file=sys.stderr)
    sys.exit(code)


def rel(path):
    return path.resolve().relative_to(ROOT).as_posix()


# ---------------------------------------------------------------- works and chapters

def works():
    return sorted(
        d for d in ROOT.iterdir()
        if d.is_dir() and not d.name.startswith(".") and (d / "BOOK.md").is_file()
    )


def book_meta(work):
    """Front matter of BOOK.md as a dict, plus the optional explicit chapter order."""
    text = (work / "BOOK.md").read_text(encoding="utf-8-sig")
    meta = {}
    front = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.S)
    if front:
        for line in front.group(1).splitlines():
            key, sep, value = line.partition(":")
            if sep:
                meta[key.strip().lower()] = value.strip().strip("\"'")
    order = []
    section = re.search(r"^#+\s*chapter order\s*\n(.*?)(?=^#|\Z)", text, re.S | re.M | re.I)
    if section:
        order = re.findall(r"^\s*(?:[-*]|\d+\.)\s+`?([^`\n]+?)`?\s*$", section.group(1), re.M)
    return meta, order


def chapters(work):
    files = [
        f for f in work.iterdir()
        if f.is_file() and f.suffix.lower() in SOURCE_EXTS
        and f.name.lower() not in NOT_CHAPTERS and f.name[0] not in "~_."
    ]
    _, order = book_meta(work)
    if order:
        rank = {name.lower(): i for i, name in enumerate(order)}
        listed = [f for f in files if f.name.lower() in rank or f.stem.lower() in rank]
        listed.sort(key=lambda f: rank.get(f.name.lower(), rank.get(f.stem.lower())))
        return listed

    def natural(f):
        number = re.search(r"\d+", f.stem)
        return (number is None, int(number.group()) if number else 0, f.name.lower())

    return sorted(files, key=natural)


def resolve_work(name):
    work = (ROOT / name.strip("/\\")).resolve()
    if not (work / "BOOK.md").is_file():
        known = ", ".join(w.name for w in works()) or "none yet, create one with /new-book"
        fail(f"'{name}' is not a work (no BOOK.md). Works: {known}")
    return work


def previous_tomes(work):
    """Works that `work` follows (BOOK.md `follows:`), oldest first."""
    chain, seen = [], {work.name}
    current = work
    while True:
        target = book_meta(current)[0].get("follows", "")
        if not target:
            return list(reversed(chain))
        if target in seen:
            fail(f"'follows' loops back to {target} (from {current.name})")
        folder = ROOT / target.strip("/\\")
        if not (folder / "BOOK.md").is_file():
            fail(f"{current.name}/BOOK.md says it follows '{target}', which is not a work (no BOOK.md)")
        seen.add(target)
        chain.append(folder.resolve())
        current = folder.resolve()


def resolve_chapter(name):
    for base in (Path.cwd(), ROOT):
        candidate = (base / name).resolve()
        if candidate.is_file():
            if not (candidate.parent / "BOOK.md").is_file():
                fail(f"{candidate.parent.name}/ has no BOOK.md. Create the work with /new-book first.")
            return candidate
    wanted = Path(name).name.lower()
    matches = [
        f for work in works() for f in chapters(work)
        if wanted in (f.name.lower(), f.stem.lower())
    ]
    if not matches:
        fail(f"no chapter named '{name}' in any work")
    if len(matches) > 1:
        fail("several chapters match, give the path: " + ", ".join(rel(m) for m in matches), 2)
    return matches[0]


# ---------------------------------------------------------------- extraction

def is_on(run_props, tag):
    el = run_props.find(W + tag) if run_props is not None else None
    return el is not None and el.get(W + "val", "true") not in ("0", "false", "none")


def iter_paragraphs(node):
    for child in node:
        if child.tag in SKIP:
            continue
        if child.tag == W + "p":
            yield child
        yield from iter_paragraphs(child)


def run_pieces(node, out):
    """Collect (text, bold, italic) for the runs of one paragraph."""
    for child in node:
        if child.tag in SKIP or child.tag == W + "p":
            continue
        if child.tag != W + "r":
            run_pieces(child, out)
            continue
        props = child.find(W + "rPr")
        bold, italic = is_on(props, "b"), is_on(props, "i")
        for el in child:
            if el.tag == W + "t":
                text = el.text or ""
            elif el.tag == W + "tab":
                text = " "
            elif el.tag in (W + "br", W + "cr"):
                text = "\n"
            elif el.tag == W + "noBreakHyphen":
                text = "‑"
            elif el.tag == W + "footnoteReference":
                text = "[^%s]" % el.get(W + "id")
            elif el.tag == W + "endnoteReference":
                text = "[^e%s]" % el.get(W + "id")
            else:
                continue
            if text:
                out.append((text, bold, italic))


def render(pieces, emphasis=True):
    merged = []
    for text, bold, italic in pieces:
        if merged and merged[-1][1:] == [bold, italic]:
            merged[-1][0] += text
        else:
            merged.append([text, bold, italic])
    out = []
    for text, bold, italic in merged:
        mark = ("**" if bold else "") + ("*" if italic else "")
        core = text.strip()
        if mark and emphasis and core:
            start = text.index(core)
            text = text[:start] + mark + core + mark + text[start + len(core):]
        out.append(text)
    return "".join(out).strip()


def paragraph_text(p, emphasis=True):
    pieces = []
    run_pieces(p, pieces)
    return render(pieces, emphasis)


def heading_levels(archive, title_is_heading=True):
    """Style id -> heading level. Style names are canonical whatever the language of Word."""
    levels = {}
    if "word/styles.xml" in archive.namelist():
        for style in ET.fromstring(archive.read("word/styles.xml")).iter(W + "style"):
            name = style.find(W + "name")
            label = (name.get(W + "val") if name is not None else "").lower()
            match = re.fullmatch(r"heading (\d)", label)
            if match:
                levels[style.get(W + "styleId")] = int(match.group(1))
            elif label == "title" and title_is_heading:
                levels[style.get(W + "styleId")] = 1
    return levels


def docx_blocks(path):
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        fail(f"{path.name} is not a valid .docx file")
    with archive:
        levels = heading_levels(archive)
        body = ET.fromstring(archive.read("word/document.xml")).find(W + "body")
        blocks = []
        for p in iter_paragraphs(body):
            props = p.find(W + "pPr")
            style = props.find(W + "pStyle") if props is not None else None
            style_id = style.get(W + "val") if style is not None else ""
            level = levels.get(style_id)
            if level is None:
                guess = re.fullmatch(r"(?:Heading|Titre)(\d)", style_id or "")
                level = int(guess.group(1)) if guess else None
            text = paragraph_text(p, emphasis=level is None)
            if not text:
                continue
            if level:
                text = "#" * level + " " + text
            elif props is not None and props.find(W + "numPr") is not None:
                text = "- " + text
            blocks.append((None, text))
        notes = []
        for part, tag, prefix in (("word/footnotes.xml", "footnote", ""), ("word/endnotes.xml", "endnote", "e")):
            if part not in archive.namelist():
                continue
            for note in ET.fromstring(archive.read(part)).iter(W + tag):
                if note.get(W + "type") in NOTE_SEPARATORS:
                    continue
                text = " ".join(filter(None, (paragraph_text(p) for p in iter_paragraphs(note))))
                if text:
                    notes.append("[^%s%s]: %s" % (prefix, note.get(W + "id"), text))
    return blocks, notes


def text_blocks(path):
    """Plain-text sources: one block per run of non-blank lines, with its first line number."""
    blocks, current, start = [], [], 0
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    for number, line in enumerate(lines + [""], 1):
        if line.strip():
            if not current:
                start = number
            current.append(line.rstrip())
        elif current:
            blocks.append((start, "\n".join(current)))
            current = []
    return blocks, []


def source_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def recorded_hash(path):
    """The source hash a generated file was based on (first line), or None."""
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as handle:
        match = re.search(r"sha256: ([0-9a-f]{12})", handle.readline())
    return match.group(1) if match else None


def state(path, current):
    if not path.is_file():
        return "missing"
    return "current" if recorded_hash(path) == current else "stale"


def render_text(source):
    """The text.md content of a source file: (header, blocks, full text)."""
    if source.suffix.lower() not in SOURCE_EXTS:
        fail(f"unsupported format {source.suffix} (supported: {', '.join(sorted(SOURCE_EXTS))})")
    blocks, notes = docx_blocks(source) if source.suffix.lower() == ".docx" else text_blocks(source)
    if not blocks:
        fail(f"{source.name} contains no text")
    header = f"<!-- source: {source.name} | sha256: {source_hash(source)} | generated by tools/book.py, do not edit -->"
    parts = [header]
    for index, (line, text) in enumerate(blocks, 1):
        tag = f"[¶{index} L{line}]" if line else f"[¶{index}]"
        parts.append(f"{tag} {text}")
    parts.extend(notes)
    return header, blocks, "\n\n".join(parts) + "\n"


def save_draft(out_dir, content):
    """Keep a draft's text.md under versions/, named by the time it is saved so that drafts stay in order."""
    folder = out_dir / "versions"
    folder.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    target, n = folder / f"{stamp}.md", 1
    while target.exists():
        n += 1
        target = folder / f"{stamp}-{n}.md"
    target.write_text(content, encoding="utf-8", newline="\n")
    return target


def cmd_extract(args):
    extract_chapter(resolve_chapter(args.chapter), keep_old=True)


def extract_chapter(source, keep_old):
    """Write <chapter>/text.md and print the chapter's context. When the source changed since the last
    extraction and keep_old is set, the previous text.md is first saved under versions/."""
    work = source.parent
    header, blocks, content = render_text(source)
    digest = source_hash(source)
    out_dir = work / source.stem
    out = out_dir / "text.md"
    before = recorded_hash(out)
    saved = None
    if keep_old and before is not None and before != digest:
        saved = save_draft(out_dir, out.read_text(encoding="utf-8"))
    out_dir.mkdir(exist_ok=True)
    out.write_text(content, encoding="utf-8", newline="\n")

    ordered = chapters(work)
    keys = [f.stem for f in ordered]
    position = keys.index(source.stem) if source.stem in keys else len(keys)
    earlier, later = ordered[:position], ordered[position + 1:]
    meta, _ = book_meta(work)
    profile = meta.get("profile", "")
    words = sum(len(re.findall(r"\w+", text)) for _, text in blocks)

    print(f"work: {work.name}")
    print(f"book: {rel(work / 'BOOK.md')}")
    print(f"profile: profiles/{profile}.md" + ("" if (ROOT / "profiles" / f"{profile}.md").is_file() else "  (MISSING)"))
    print(f"chapter: {rel(source)}")
    print(f"key: {source.stem}")
    print(f"dir: {rel(out_dir)}")
    print(f"text: {rel(out)}")
    print(f"header: {header}")
    print(f"paragraphs: {len(blocks)}")
    print(f"words: {words}")
    print("source: " + ("first extraction" if before is None else "unchanged" if before == digest else "changed since last extraction"))
    if saved is not None:
        print(f"previous_draft_saved: {rel(saved)}")
    print("previous_tomes: " + " ".join(t.name for t in previous_tomes(work)))
    print("earlier: " + " ".join(f.stem for f in earlier))
    print("earlier_without_record: " + " ".join(f.stem for f in earlier if not (work / f.stem / "record.md").is_file()))
    print("later_already_reviewed: " + " ".join(f.stem for f in later if any((work / f.stem / "reviews").glob("*.md"))))


# ---------------------------------------------------------------- listings

def cmd_list(args):
    work = resolve_work(args.work)
    meta, _ = book_meta(work)
    print(f"work: {work.name}")
    print(f"title: {meta.get('title', '')}")
    print(f"profile: profiles/{meta.get('profile', '')}.md")
    tomes = previous_tomes(work)
    print("previous_tomes: " + " ".join(t.name for t in tomes))
    for tome in tomes:
        have = [r for r in reader_names() if (ROOT / "readers" / r / "memory" / tome.name / "_tome.md").is_file()]
        print(f"tome {tome.name}: _tome.md for {','.join(have) or 'no reader'}")
    for index, source in enumerate(chapters(work), 1):
        digest = source_hash(source)
        folder = work / source.stem
        reviews = [f"{f.stem}:{state(f, digest)}" for f in sorted((folder / "reviews").glob("*.md"))]
        print(
            f"{index}. {source.name} | key={source.stem}"
            f" | text={state(folder / 'text.md', digest)}"
            f" | record={state(folder / 'record.md', digest)}"
            f" | proofread={state(folder / 'proofread.md', digest)}"
            f" | reviews={','.join(reviews) or 'none'}"
        )


def cmd_works(args):
    for work in works():
        meta, _ = book_meta(work)
        print(f"{work.name} | profile={meta.get('profile', '')} | chapters={len(chapters(work))}")


def reader_names():
    folder = ROOT / "readers"
    if not folder.is_dir():
        return []
    return sorted(
        d.name for d in folder.iterdir()
        if d.is_dir() and d.name[0] not in "_." and (d / "PERSONALITY.md").is_file()
    )


def cmd_readers(args):
    for name in reader_names():
        print(name)


def cmd_archive_memory(args):
    work = resolve_work(args.work)
    if args.reader not in reader_names():
        fail(f"no reader named '{args.reader}'. Readers: {', '.join(reader_names()) or 'none'}")
    memory = ROOT / "readers" / args.reader / "memory"
    source = memory / work.name
    if not source.is_dir() or not any(source.iterdir()):
        print("archived: nothing (no memory of this work yet)")
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = memory / "_archive" / f"{work.name}-{stamp}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    print(f"archived: {rel(target)}")


def cmd_rewind(args):
    work = resolve_work(args.work)
    if args.reader not in reader_names():
        fail(f"no reader named '{args.reader}'. Readers: {', '.join(reader_names()) or 'none'}")
    keys = [f.stem for f in chapters(work)]
    wanted = Path(args.chapter).stem.lower()
    matches = [k for k in keys if k.lower() == wanted]
    if not matches:
        fail(f"'{args.chapter}' is not a chapter of {work.name}. Chapters: {', '.join(keys)}")
    key = matches[0]
    memory = ROOT / "readers" / args.reader / "memory"
    later = [k for k in keys[keys.index(key) + 1:] if (memory / work.name / f"{k}.md").is_file()]
    if not later:
        print("archived: nothing (no memory of the chapters after this one)")
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = memory / "_archive" / f"{work.name}-after-{key}-{stamp}"
    target.mkdir(parents=True)
    for k in later:
        shutil.move(str(memory / work.name / f"{k}.md"), str(target / f"{k}.md"))
    print(f"archived: {rel(target)}")
    print("chapters: " + " ".join(later))


def paragraphs_of(text):
    """The paragraph texts of a text.md, without header or [¶n] tags."""
    return [re.sub(r"^\[¶\d+(?: L\d+)?\]\s*", "", p) for p in text.split("\n\n")[1:] if p.startswith("[¶")]


def write_diff(old_text, new_text, new_header, target, old_name):
    old, new = paragraphs_of(old_text), paragraphs_of(new_text)
    changed, added, removed = [], [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag == "replace":
            changed.append((i1, i2, j1, j2))
        elif tag == "insert":
            added.append((j1, j2))
        elif tag == "delete":
            removed.append((i1, i2))

    def span(a, b):
        return f"¶{a + 1}" if b - a == 1 else f"¶{a + 1}-{b}"

    lines = [
        new_header,
        f"# Differences between the previous draft (versions/{old_name}) and the current text.md",
        "",
        "Old ¶ numbers are those of the previous draft, new ¶ numbers those of the current text.md.",
        "A paragraph that moved appears as removed and added.",
        "",
        "## Changed",
    ]
    for i1, i2, j1, j2 in changed:
        lines += [f"- old {span(i1, i2)} → new {span(j1, j2)}", f"  old: {' / '.join(old[i1:i2])}", f"  new: {' / '.join(new[j1:j2])}"]
    lines += ["", "## Added"]
    lines += [f"- new {span(j1, j2)}: {' / '.join(new[j1:j2])}" for j1, j2 in added]
    lines += ["", "## Removed"]
    lines += [f"- old {span(i1, i2)}: {' / '.join(old[i1:i2])}" for i1, i2 in removed]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return len(changed), len(added), len(removed)


def cmd_revise(args):
    new = resolve_chapter(args.chapter)
    old = None
    for base in (Path.cwd(), ROOT):
        if (base / args.old).resolve().is_file():
            old = (base / args.old).resolve()
            break
    if old is None:
        fail(f"no old draft at '{args.old}'")
    out_dir = new.parent / new.stem
    text = out_dir / "text.md"
    if old == new.resolve():
        # Edited in place: the old draft is the text.md extracted before the edit.
        if recorded_hash(text) in (None, source_hash(new)):
            fail(f"{new.name} has no earlier extracted draft to compare with; give the old draft as a separate file")
        old_content = text.read_text(encoding="utf-8")
    else:
        if source_hash(old) == source_hash(new):
            fail("the old draft and the new one are identical")
        old_content = render_text(old)[2]
    saved = save_draft(out_dir, old_content)
    header, _, new_content = render_text(new)
    extract_chapter(new, keep_old=False)
    diff = saved.with_name(saved.stem + ".diff.md")
    changed, added, removed = write_diff(old_content, new_content, header, diff, saved.name)
    print(f"old_text: {rel(saved)}")
    print(f"diff: {rel(diff)}")
    print(f"changes: {changed} changed, {added} added, {removed} removed")


# ---------------------------------------------------------------- splitting a whole book

# A paragraph that starts a chapter when the document has no heading styles.
CHAPTER_LINE = (
    r"(chapter|chapitre|cap[ií]tulo|capitolo|kapitel|hoofdstuk|part|partie|prologue|[eé]pilogue|epilog)\b.{0,80}"
    r"|\d{1,3}\.?|[IVXLC]{1,7}\.?"
)
TAG = re.compile(r"<(/?)([\w:.-]+)[^>]*?(/?)>")


def top_level_spans(body):
    """(start, end) of each direct child of <w:body>, found on the raw XML.

    The document is cut as text and never re-serialised: a parser would rename
    namespace prefixes that Word's compatibility attributes refer to by name.
    """
    spans, depth, start = [], 0, 0
    for tag in TAG.finditer(body):
        closing, _, self_closing = tag.groups()
        if closing:
            depth -= 1
            if depth == 0:
                spans.append((start, tag.end()))
        elif self_closing:
            if depth == 0:
                spans.append((tag.start(), tag.end()))
        else:
            if depth == 0:
                start = tag.start()
            depth += 1
    return spans


def span_text(xml):
    return html.unescape("".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", xml)))


def is_paragraph(xml):
    return re.match(r"<w:p[\s>]", xml) is not None


def span_level(xml, levels):
    """Heading level of a top-level paragraph, or None."""
    if not is_paragraph(xml):
        return None
    style = re.search(r'<w:pStyle w:val="([^"]+)"', xml)
    if style:
        style_id = html.unescape(style.group(1))
        if style_id in levels:
            return levels[style_id]
        guess = re.fullmatch(r"(?:Heading|Titre)(\d)", style_id)
        if guess:
            return int(guess.group(1))
    outline = re.search(r'<w:outlineLvl w:val="(\d)"', xml)
    return int(outline.group(1)) + 1 if outline else None


def slug(text, limit=40):
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    plain = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")
    return plain[:limit].rstrip("-")


def cmd_split(args):
    source = Path(args.book)
    if not source.is_file():
        source = ROOT / args.book
    if not source.is_file() or source.suffix.lower() != ".docx":
        fail(f"'{args.book}' is not a .docx file")
    work = resolve_work(args.work)
    try:
        archive = zipfile.ZipFile(source)
    except zipfile.BadZipFile:
        fail(f"{source.name} is not a valid .docx file")
    with archive:
        document = archive.read("word/document.xml").decode("utf-8")
        levels = heading_levels(archive, title_is_heading=False)
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    opening = re.search(r"<w:body(?:\s[^>]*)?>", document)
    closing = document.rfind("</w:body>")
    if not opening or closing < 0:
        fail("unexpected document structure (no <w:body>); cannot split this file")
    body = document[opening.end():closing]
    spans = [body[a:b] for a, b in top_level_spans(body)]
    final_section = spans.pop() if spans and spans[-1].startswith("<w:sectPr") else ""

    def matching(pattern, max_length=None):
        return [
            i for i, xml in enumerate(spans)
            if is_paragraph(xml) and pattern.fullmatch(span_text(xml).strip())
            and (max_length is None or len(span_text(xml)) < max_length)
        ]

    if args.pattern:
        starts = matching(re.compile(args.pattern, re.I))
        method = "pattern " + args.pattern
    else:
        found = [span_level(xml, levels) for xml in spans]
        counts = {}
        for level in found:
            if level:
                counts[level] = counts.get(level, 0) + 1
        if counts:
            print("headings found: " + ", ".join(f"level {n} x{counts[n]}" for n in sorted(counts)))
        level = args.level or next((n for n in sorted(counts) if counts[n] >= 2), None)
        if level:
            starts = [i for i, n in enumerate(found) if n == level and span_text(spans[i]).strip()]
            method = f"heading level {level}"
        else:
            starts = matching(re.compile(CHAPTER_LINE, re.I), max_length=90)
            method = "no heading styles; lines that look like chapter titles"
    if len(starts) < 2:
        fail(f"found {len(starts)} chapter start(s) using {method}. Try --level N or --pattern REGEX.")

    pieces = []
    front = spans[:starts[0]]
    if span_text("".join(front)).strip():
        pieces.append((0, "front-matter", front))
    for number, (begin, end) in enumerate(zip(starts, starts[1:] + [len(spans)]), 1):
        pieces.append((number, span_text(spans[begin]).strip(), spans[begin:end]))

    width = max(2, len(str(len(starts))))
    plan = []
    for number, title, chunk in pieces:
        # Title page, dedication and the like: kept, but the leading "_" keeps it out of the chapters.
        name = f"{number:0{width}d}-{slug(title) or 'chapter'}.docx" if number else "_front-matter.docx"
        words = len(re.findall(r"\w+", span_text("".join(chunk))))
        plan.append((name, title, words, chunk))

    print(f"source: {source.name}")
    print(f"split on: {method}")
    print(f"into: {work.name}/")
    for name, title, words, _ in plan:
        exists = "  (EXISTS)" if (work / name).exists() else ""
        print(f"  {name} | {words} words | {title}{exists}")
    if source.resolve().parent == work and source.name[0] not in "_~.":
        print(f"warning: {source.name} is in the work folder and will be listed as a chapter; rename it to _{source.name}")
    if not args.write:
        print("dry run: nothing written. Add --write to create the files.")
        return
    clashes = [name for name, _, _, _ in plan if (work / name).exists()]
    if clashes and not args.force:
        fail("these files already exist (use --force to replace them): " + ", ".join(clashes))

    head, tail = document[:opening.end()], document[closing:]
    for name, _, _, chunk in plan:
        content = (head + "".join(chunk) + final_section + tail).encode("utf-8")
        with zipfile.ZipFile(work / name, "w", zipfile.ZIP_DEFLATED) as out:
            for info, data in entries:
                out.writestr(info, content if info.filename == "word/document.xml" else data)
    print(f"written: {len(plan)} files")


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract")
    extract.add_argument("chapter")
    extract.set_defaults(run=cmd_extract)
    listing = commands.add_parser("list")
    listing.add_argument("work")
    listing.set_defaults(run=cmd_list)
    commands.add_parser("works").set_defaults(run=cmd_works)
    commands.add_parser("readers").set_defaults(run=cmd_readers)
    archive = commands.add_parser("archive-memory")
    archive.add_argument("work")
    archive.add_argument("reader")
    archive.set_defaults(run=cmd_archive_memory)
    rewind = commands.add_parser("rewind")
    rewind.add_argument("work")
    rewind.add_argument("chapter")
    rewind.add_argument("reader")
    rewind.set_defaults(run=cmd_rewind)
    revise = commands.add_parser("revise")
    revise.add_argument("old")
    revise.add_argument("chapter")
    revise.set_defaults(run=cmd_revise)
    split = commands.add_parser("split")
    split.add_argument("book")
    split.add_argument("work")
    split.add_argument("--level", type=int)
    split.add_argument("--pattern")
    split.add_argument("--write", action="store_true")
    split.add_argument("--force", action="store_true")
    split.set_defaults(run=cmd_split)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
