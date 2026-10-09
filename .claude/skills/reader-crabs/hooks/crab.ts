// Pure helpers: no engine calls, so they can be tested alone.

export type Look = Record<string, string>

const COLORS: Record<string, string> = {
  red: '#e5533d',
  orange: '#f08a24',
  yellow: '#e6c229',
  green: '#4caf50',
  teal: '#22a6a0',
  cyan: '#3bb8e0',
  blue: '#4a7de8',
  purple: '#8e5bd6',
  pink: '#e86aa8',
  white: '#e8e8e8',
  grey: '#9a9a9a',
  gray: '#9a9a9a',
  brown: '#a56a3c',
}

export const DEFAULT_LOOK: Look = {
  color: 'grey',
  eyes: 'round',
  claws: 'small',
  accessory: 'none',
}

/** `readers/<name>/crab.md`: `key: value` lines; anything else is ignored. */
export function parseCrab(text: string): Look {
  const look: Look = {}
  for (const line of text.split(/\r?\n/)) {
    const m = line.match(/^\s*[-*]?\s*([a-z]+)\s*:\s*(.+?)\s*$/i)
    if (m) look[m[1].toLowerCase()] = m[2]
  }
  return look
}

export function bodyColor(look: Look): string {
  const c = (look.color ?? '').toLowerCase()
  if (/^#[0-9a-f]{6}$/.test(c)) return c
  return COLORS[c] ?? COLORS.grey
}

/** Reader name as their PERSONALITY.md gives it: the first `# ` heading. */
export function parseTitle(personality: string, fallback: string): string {
  const m = personality.match(/^#\s+(.+?)\s*$/m)
  return m ? m[1] : fallback
}

// The crab is a 16x12 pixel grid drawn with half blocks: each terminal cell
// holds two pixels (upper `▀` in the foreground colour, lower in the background).

const EYES: Record<string, [string, string]> = {
  round: ['KK/KK', 'KK/KK'],
  wide: ['WK/WW', 'KW/WW'],
  sleepy: ['BB/KK', 'BB/KK'],
  sharp: ['KB/KK', 'BK/KK'],
  worried: ['BK/KK', 'KB/KK'],
  squint: ['KB/BK', 'BK/KB'],
  star: ['YY/YY', 'YY/YY'],
  happy: ['BK/KB', 'KB/BK'],
}

/** Left claw, columns 0-2, from `row`; the right claw is its mirror. */
const CLAWS: Record<string, { row: number; rows: string[] }> = {
  small: { row: 3, rows: ['B.B', 'BBB'] },
  big: { row: 1, rows: ['B.B', 'BBB', 'BBB', 'BBB'] },
  raised: { row: 0, rows: ['B.B', 'BBB', '.B.', '.B.', '.BB'] },
  crossed: { row: 7, rows: ['..DDD', '..DDD'] },
}

/** Overlays as `[row, col, pixels]`; `.` leaves the pixel alone. */
const HEAD: Record<string, [number, number, string][]> = {
  hat: [[1, 6, 'HHHH'], [2, 4, 'HHHHHHHH']],
  crown: [[1, 5, 'Y.YY.Y'], [2, 5, 'YYYYYY']],
  bow: [[1, 5, 'PP..PP'], [2, 5, 'PPRRPP']],
  headphones: [[1, 5, 'GGGGGG'], [2, 4, 'G......G'], [3, 3, 'G......G'], [4, 2, 'KK....KK'], [5, 2, 'KK....KK'], [6, 2, 'KK....KK']],
  book: [[1, 5, 'NNNNNN'], [2, 5, 'WWNNWW']],
  pencil: [[0, 8, 'PP'], [1, 8, 'YY'], [2, 8, 'YY']],
}

const ACCESSORIES: Record<string, [number, number, string][]> = {
  glasses: [
    [4, 3, 'FFFF..FFFF'], [5, 3, 'F..FFFF..F'], [6, 3, 'F..F..F..F'], [7, 3, 'FFFF..FFFF'],
  ],
  monocle: [[4, 9, 'YYYY'], [5, 9, 'Y..Y'], [6, 9, 'Y..Y'], [7, 9, 'YYYY'], [8, 12, 'YY']],
  scarf: [[9, 2, 'RRRRRRRRRRRR'], [10, 10, 'RR']],
}

export const OPTIONS = {
  color: Object.keys(COLORS).filter(c => c !== 'gray'),
  eyes: Object.keys(EYES),
  claws: Object.keys(CLAWS),
  accessory: ['none', ...Object.keys(ACCESSORIES), ...Object.keys(HEAD)],
}

const BODY = [
  '................',
  '................',
  '................',
  '....BBBBBBBB....',
  '...BLLLBBBBBB...',
  '..BBBBBBBBBBBB..',
  '..BBBBBBBBBBBB..',
  '..BBBBBBBBBBBB..',
  '..BBBBBBBBBBBB..',
  '..BBBBBBBBBBBB..',
  '...DDDDDDDDDD...',
  '..D.D.D..D.D.D..',
]

const WIDTH = 16
const FIXED: Record<string, string> = {
  K: '#1b1b22', W: '#ffffff', Y: '#f2c94c', H: '#2d2d3a', P: '#ee82b4',
  R: '#d6403a', G: '#c9ccd4', N: '#8a5a33', F: '#f4f4f4',
}

function mix(hex: string, to: number, amount: number): string {
  const ch = [1, 3, 5].map(i => Number.parseInt(hex.slice(i, i + 2), 16))
  return '#' + ch.map(c => Math.round(c + (to - c) * amount).toString(16).padStart(2, '0')).join('')
}

function put(grid: string[][], row: number, col: number, pixels: string) {
  for (let i = 0; i < pixels.length; i++) {
    const x = col + i
    if (pixels[i] !== '.' && grid[row] && x >= 0 && x < WIDTH) grid[row][x] = pixels[i]
  }
}

const mirror = (s: string) => [...s].reverse().join('')

/** The crab as a 16x12 grid of pixel codes (`.` is empty). `rating` sets the mouth. */
export function crabPixels(look: Look, rating: number | null): string[][] {
  const grid = BODY.map(r => [...r])
  const [le, re] = EYES[look.eyes] ?? EYES.round
  const [ltop, lbot] = le.split('/')
  const [rtop, rbot] = re.split('/')
  const eyes: [number, number, string][] = [
    [5, 4, ltop], [6, 4, lbot], [5, 10, rtop], [6, 10, rbot],
  ]
  for (const [r, c, p] of eyes) for (let i = 0; i < p.length; i++) if (p[i] !== 'B') put(grid, r, c + i, p[i])

  const claw = CLAWS[look.claws] ?? CLAWS.small
  claw.rows.forEach((p, i) => {
    put(grid, claw.row + i, 0, p)
    put(grid, claw.row + i, WIDTH - p.length, mirror(p))
  })

  if (rating !== null && rating >= 4) { put(grid, 8, 6, 'K..K'); put(grid, 9, 7, 'KK') }
  else if (rating !== null && rating < 3) { put(grid, 8, 7, 'KK'); put(grid, 9, 6, 'K..K') }
  else put(grid, 9, 6, 'KKKK')

  const acc = look.accessory ?? 'none'
  for (const [r, c, p] of ACCESSORIES[acc] ?? HEAD[acc] ?? []) put(grid, r, c, p)
  return grid
}

export type Cell = { text: string; color?: string; backgroundColor?: string }

/** Rows of runs for `<Text color backgroundColor>`: two pixel rows per terminal row. */
export function drawCrab(look: Look, rating: number | null): Cell[][] {
  const body = bodyColor(look)
  const colors: Record<string, string> = {
    ...FIXED, B: body, D: mix(body, 0, 0.3), L: mix(body, 255, 0.3),
  }
  const grid = crabPixels(look, rating)
  const rows: Cell[][] = []
  for (let y = 0; y < grid.length; y += 2) {
    const runs: Cell[] = []
    for (let x = 0; x < WIDTH; x++) {
      const top = colors[grid[y][x]]
      const bottom = colors[grid[y + 1]?.[x]]
      const cell: Cell = top && bottom ? { text: '▀', color: top, backgroundColor: bottom }
        : top ? { text: '▀', color: top }
        : bottom ? { text: '▄', color: bottom }
        : { text: ' ' }
      const last = runs[runs.length - 1]
      if (last && last.color === cell.color && last.backgroundColor === cell.backgroundColor) last.text += cell.text
      else runs.push(cell)
    }
    rows.push(runs)
  }
  return rows
}

/** `4.5` from `4,5/5`, `8/10` (scaled to 5), `4 sur 5`; the last one in the text. */
export function parseRating(text: string): number | null {
  const section = text.split(/^#{1,3}\s/m).pop() ?? text
  const re = /(\d+(?:[.,]\d+)?)\s*(?:\/|sur|out of|of|de)\s*(\d+)/gi
  let found: number | null = null
  for (const m of section.matchAll(re)) {
    const value = Number(m[1].replace(',', '.'))
    const scale = Number(m[2])
    if (scale > 0 && value <= scale) found = Math.round((value / scale) * 50) / 10
  }
  return found
}

const NOT_CHAPTERS = new Set(['book.md', 'readme.md'])
const SOURCE_EXT = /\.(docx|md|txt|tex)$/i

/** Chapter keys in reading order, as tools/book.py orders them. */
export function chapterKeys(files: string[], bookMd: string): string[] {
  const section = bookMd.match(/^#+\s*chapter order\s*\n([\s\S]*?)(?=^#|(?![\s\S]))/im)
  const order = section
    ? [...section[1].matchAll(/^\s*(?:[-*]|\d+\.)\s+`?([^`\n]+?)`?\s*$/gm)].map(m => m[1])
    : []
  const stem = (f: string) => f.replace(/\.[^.]+$/, '')
  const chapters = files.filter(
    f => SOURCE_EXT.test(f) && !NOT_CHAPTERS.has(f.toLowerCase()) && !/^[~_.]/.test(f),
  )
  if (order.length) {
    const rank = (f: string) =>
      order.findIndex(o => o.toLowerCase() === f.toLowerCase() || o.toLowerCase() === stem(f).toLowerCase())
    return chapters.filter(f => rank(f) >= 0).sort((a, b) => rank(a) - rank(b)).map(stem)
  }
  const num = (f: string) => {
    const m = f.match(/\d+/)
    return m ? Number(m[0]) : Infinity
  }
  return [...chapters]
    .sort((a, b) => num(stem(a)) - num(stem(b)) || a.toLowerCase().localeCompare(b.toLowerCase()))
    .map(stem)
}

export function bookTitle(bookMd: string, fallback: string): string {
  const m = bookMd.match(/^title:\s*["']?(.+?)["']?\s*$/im)
  return m ? m[1] : fallback
}

export function bookProfile(bookMd: string): string {
  const m = bookMd.match(/^profile:\s*["']?(.+?)["']?\s*$/im)
  return m ? m[1] : ''
}

export function average(xs: number[]): number | null {
  return xs.length ? Math.round((xs.reduce((a, b) => a + b, 0) / xs.length) * 10) / 10 : null
}

/** `████░░░░░░` for a rating out of 5. */
export function bar(rating: number | null, width = 10): string {
  if (rating === null) return '·'.repeat(width)
  const filled = Math.round((rating / 5) * width)
  return '█'.repeat(filled) + '░'.repeat(width - filled)
}

export function ratingColor(rating: number | null): string {
  if (rating === null) return 'inactive'
  return rating >= 4 ? 'success' : rating >= 3 ? 'warning' : 'error'
}
