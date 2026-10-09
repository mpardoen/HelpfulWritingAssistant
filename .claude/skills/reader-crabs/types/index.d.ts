export type CrabReader = {
  name: string
  title: string
  tagline: string
  look: Record<string, string>
  favorite: string | null
  latestRating: number | null
  latestChapter: string | null
  overallRating: number | null
  rated: number
  reviewed: number
  trend: number
}

export type CrabBook = {
  work: string
  title: string
  chapters: number
  readers: CrabReader[]
}

export type CrabSnapshot = {
  works: { work: string; title: string }[]
  book: CrabBook | null
  problem: string | null
}

declare module 'claude-code' {
  interface PluginState {
    'reader-crabs': {
      work: string | null
      snapshot: CrabSnapshot | null
      hidden: string[]
      isPicking: boolean
    }
  }
}
