import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import { bar, bodyColor, drawCrab, ratingColor } from './crab'
import { loadSnapshot } from './data'

const PANE = 'reader-crabs'
const REFRESH_MS = 5000

const work = atom({ plugin: 'reader-crabs', key: 'work' } as const, null)
const snapshot = atom({ plugin: 'reader-crabs', key: 'snapshot' } as const, null)
const hidden = atom({ plugin: 'reader-crabs', key: 'hidden' } as const, [])
const isPicking = atom({ plugin: 'reader-crabs', key: 'isPicking' } as const, false)

const fmt = (n: number | null) => (n === null ? ' – ' : n.toFixed(1))
const arrow = (t: number) => (t >= 0.5 ? ' ▲' : t <= -0.5 ? ' ▼' : '')

type Engine = any

const readFile = async ($: Engine, path: string): Promise<string | null> => {
  try {
    return (await $.fs.read(path)) as string
  } catch {
    return null
  }
}

async function listKind($: Engine, path: string, kind: string): Promise<string[]> {
  try {
    const entries = await $.fs.list(path)
    return entries.filter((e: { kind: string }) => e.kind === kind).map((e: { name: string }) => e.name)
  } catch {
    return []
  }
}

async function refresh($: Engine) {
  const wanted = await read($, work)
  const files = {
    read: (path: string) => readFile($, path),
    dirs: (path: string) => listKind($, path, 'dir'),
    files: (path: string) => listKind($, path, 'file'),
    exists: (path: string) => $.fs.exists(path) as Promise<boolean>,
    stamps: async (path: string) => {
      try {
        const entries = await $.fs.list(path)
        return entries
          .filter((e: { kind: string }) => e.kind === 'file')
          .map((e: { mtimeMs: number }) => e.mtimeMs)
      } catch {
        return []
      }
    },
  }
  const next = await loadSnapshot(files, wanted)
  await update($, snapshot, () => next)
}

let isTicking = false

// Re-reads the files every few seconds, so a review written by a reader agent
// shows up without anyone pressing anything.
function keepFresh($: Engine) {
  if (isTicking) return
  isTicking = true
  $.clock.every(REFRESH_MS, () => {
    void refresh($)
  })
}

async function choose($: Engine, name: string) {
  await update($, work, () => name)
  await $.store.set('reader-crabs.work', name)
  await refresh($)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'crabs',
      description: 'Show the reader crabs panel (optionally: /crabs <book folder>)',
      argumentHint: '[book]',
    })
    const saved = await $.store.get('reader-crabs.work')
    const saved2 = await $.store.get('reader-crabs.hidden')
    if (typeof saved === 'string') await update($, work, () => saved)
    if (Array.isArray(saved2)) await update($, hidden, () => saved2 as string[])
    keepFresh($)
    await refresh($)

    return next(e)
  })

  on('command.run', { command: 'crabs' }, async ($, e) => {
    const wanted = e.args.trim()
    if (wanted) await update($, work, () => wanted)
    keepFresh($)
    await refresh($)
    await $.ui.open({ id: PANE, title: 'Reader crabs' })

    return { text: 'Reader crabs panel opened. Use ◀ ▶ in the panel to change book.' }
  })

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    void refresh($)

    return ran
  })

  on('turn.complete', async ($, e, next) => {
    void refresh($)

    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const snap = await read($, snapshot)
    const gone = await read($, hidden)
    const picking = await read($, isPicking)

    if (snap === null) return <Text dimColor>Looking for your books…</Text>
    if (snap.book === null) {
      return <Text color="warning">{snap.problem ?? 'Nothing to show yet.'}</Text>
    }

    const book = snap.book
    const index = snap.works.findIndex(w => w.work === book.work)
    const step = (d: number) => {
      const target = snap.works[(index + d + snap.works.length) % snap.works.length]
      return choose($, target.work)
    }
    const toggle = (name: string) => {
      const id = `${book.work}/${name}`
      return update($, hidden, list => {
        const next = list.includes(id) ? list.filter(x => x !== id) : [...list, id]
        void $.store.set('reader-crabs.hidden', next)
        return next
      })
    }
    const shown = book.readers.filter(r => !gone.includes(`${book.work}/${r.name}`))

    return (
      <Box flexDirection="column">
        <Box>
          {snap.works.length > 1 && <Button key="prev" label="◀" onPress={() => step(-1)} />}
          <Text bold> {book.title} </Text>
          {snap.works.length > 1 && <Button key="next" label="▶" onPress={() => step(1)} />}
        </Box>
        <Text dimColor>
          {book.chapters} chapter{book.chapters === 1 ? '' : 's'} · {shown.length} of{' '}
          {book.readers.length} readers
        </Text>
        <Box>
          <Button key="pick" plain label={picking ? '▾ Choose readers' : '▸ Choose readers'} onPress={() => update($, isPicking, v => !v)} />
          <Text> </Text>
          <Button key="refresh" plain label="↻ Refresh" onPress={() => refresh($)} />
        </Box>
        {picking && (
          <Box flexDirection="column">
            {book.readers.map(r => (
              <Button
                key={`pick-${r.name}`}
                plain
                label={`${gone.includes(`${book.work}/${r.name}`) ? '[ ]' : '[x]'} ${r.title}`}
                onPress={() => toggle(r.name)}
              />
            ))}
          </Box>
        )}
        <Text> </Text>
        {book.readers.length === 0 && (
          <Text dimColor>No reader has reviewed this book yet. Run /review on a chapter.</Text>
        )}
        {shown.map(r => {
          const art = drawCrab(r.look, r.latestRating ?? r.overallRating)
          const color = bodyColor(r.look)
          return (
            <Box key={r.name} flexDirection="column" marginBottom={1}>
              <Box>
                <Box flexDirection="column" marginRight={1}>
                  {art.map((row, i) => (
                    <Text key={`${r.name}-${i}`}>
                      {row.map((cell, j) => (
                        <Text key={j} color={cell.color} backgroundColor={cell.backgroundColor}>
                          {cell.text}
                        </Text>
                      ))}
                    </Text>
                  ))}
                </Box>
                <Box flexDirection="column">
                  <Text bold color={color}>
                    {r.title}
                  </Text>
                  <Text dimColor wrap="truncate-end">
                    {r.tagline}
                  </Text>
                  {(
                    <Box flexDirection="column">
                      <Text>
                        <Text dimColor>Latest </Text>
                        <Text color={ratingColor(r.latestRating)}>{bar(r.latestRating, 8)}</Text>
                        <Text> {fmt(r.latestRating)}</Text>
                        <Text color={r.trend > 0 ? 'success' : 'error'}>{arrow(r.trend)}</Text>
                      </Text>
                      <Text>
                        <Text dimColor>Overall </Text>
                        <Text color={ratingColor(r.overallRating)}>{bar(r.overallRating, 8)}</Text>
                        <Text> {fmt(r.overallRating)}</Text>
                        <Text dimColor> ({r.rated} ch.)</Text>
                      </Text>
                    </Box>
                  )}
                </Box>
              </Box>
            </Box>
          )
        })}
      </Box>
    )
  })
}
