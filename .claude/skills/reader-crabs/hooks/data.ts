import type { CrabBook, CrabReader, CrabSnapshot } from '../types'
import {
  DEFAULT_LOOK,
  average,
  bookTitle,
  chapterKeys,
  parseCrab,
  parseFavorite,
  parseRating,
  parseTitle,
} from './crab'

/** What the loader needs from the engine; built from `$.fs` in register.tsx. */
export type Files = {
  read: (path: string) => Promise<string | null>
  dirs: (path: string) => Promise<string[]>
  files: (path: string) => Promise<string[]>
  exists: (path: string) => Promise<boolean>
  /** Modification times of the files directly in a folder. */
  stamps: (path: string) => Promise<number[]>
}

export async function listWorks(fs: Files) {
  const found: { work: string; title: string }[] = []
  for (const name of (await fs.dirs('.')).sort()) {
    if (name.startsWith('.')) continue
    const book = await fs.read(`${name}/BOOK.md`)
    if (book !== null) found.push({ work: name, title: bookTitle(book, name) })
  }
  return found
}

async function loadReader(fs: Files, name: string, work: string, keys: string[]): Promise<CrabReader> {
  const personality = (await fs.read(`readers/${name}/PERSONALITY.md`)) ?? ''
  const crab = await fs.read(`readers/${name}/crab.md`)
  const look = { ...DEFAULT_LOOK, ...(crab ? parseCrab(crab) : {}) }
  const tagline = crab ? parseCrab(crab).note ?? '' : 'No crab yet. Run /draw-crabs'

  const ratings: { key: string; rating: number | null }[] = []
  for (const key of keys) {
    const review = await fs.read(`${work}/${key}/reviews/${name}.md`)
    if (review !== null) ratings.push({ key, rating: parseRating(review) })
  }
  // The favourite is carried by the most recent memory file that has one.
  let favorite: string | null = null
  for (const key of [...keys].reverse()) {
    const memory = await fs.read(`readers/${name}/memory/${work}/${key}.md`)
    favorite = memory === null ? null : parseFavorite(memory)
    if (favorite !== null) break
  }
  const numbers = ratings.flatMap(r => (r.rating === null ? [] : [r.rating]))
  const latest = ratings[ratings.length - 1]
  const earlier = average(numbers.slice(0, -1))
  const latestRating = latest?.rating ?? null

  return {
    name,
    title: parseTitle(personality, name),
    tagline,
    look,
    favorite,
    latestRating,
    latestChapter: latest?.key ?? null,
    overallRating: average(numbers),
    rated: numbers.length,
    reviewed: ratings.length,
    trend: latestRating !== null && earlier !== null ? Math.round((latestRating - earlier) * 10) / 10 : 0,
  }
}

export async function loadBook(fs: Files, work: string): Promise<CrabBook | null> {
  const bookMd = await fs.read(`${work}/BOOK.md`)
  if (bookMd === null) return null
  const files = await fs.files(work)
  const keys = chapterKeys(files, bookMd)
  const names: string[] = []
  for (const name of (await fs.dirs('readers')).sort()) {
    if (/^[_.]/.test(name)) continue
    if (await fs.exists(`readers/${name}/PERSONALITY.md`)) names.push(name)
  }
  // Only readers who have reviewed at least one chapter of this book.
  const all = await Promise.all(names.map(n => loadReader(fs, n, work, keys)))
  const readers = all.filter(r => r.reviewed > 0)
  return { work, title: bookTitle(bookMd, work), chapters: keys.length, readers }
}

/** When a review of this work was last written (0 if none). */
async function lastReview(fs: Files, work: string): Promise<number> {
  let newest = 0
  for (const sub of await fs.dirs(work)) {
    for (const t of await fs.stamps(`${work}/${sub}/reviews`)) newest = Math.max(newest, t)
  }
  return newest
}

export async function loadSnapshot(fs: Files, wanted: string | null): Promise<CrabSnapshot> {
  try {
    const works = await listWorks(fs)
    if (works.length === 0) {
      return { works, book: null, problem: 'No book yet. Create one with /new-book.' }
    }
    let work = works.find(w => w.work === wanted)?.work
    if (!work) {
      // Nothing chosen yet: follow the book that was reviewed most recently.
      const times = await Promise.all(works.map(w => lastReview(fs, w.work)))
      work = works[times.indexOf(Math.max(...times))].work
    }
    return { works, book: await loadBook(fs, work), problem: null }
  } catch (error) {
    return { works: [], book: null, problem: `Could not read the books: ${String(error)}` }
  }
}
