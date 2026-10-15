import { Fragment, type ReactNode } from 'react'

// Tiny renderer for what the assistant actually emits: **bold**, "- " bullets and | tables |.
const inline = (t: string): ReactNode[] =>
  t.split(/(\*\*[^*]+\*\*)/g).map((p, i) => (p.startsWith('**') && p.endsWith('**') ? <strong key={i}>{p.slice(2, -2)}</strong> : <Fragment key={i}>{p}</Fragment>))

const cells = (row: string) => row.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim())
const isSep = (row: string) => /^\s*\|?[\s:|-]+\|?\s*$/.test(row) && row.includes('-')

export default function Markdown({ text }: { text: string }) {
  const lines = text.split('\n')
  const out: ReactNode[] = []
  for (let i = 0; i < lines.length; ) {
    const line = lines[i]
    if (line.trim().startsWith('|')) {
      const rows: string[] = []
      while (i < lines.length && lines[i].trim().startsWith('|')) rows.push(lines[i++])
      const body = rows.filter((r) => !isSep(r)).map(cells)
      const [head, ...rest] = body
      out.push(
        <div key={out.length} className="my-2 overflow-x-auto rounded-lg border border-white/10">
          <table className="w-full text-left text-xs">
            <thead className="bg-white/[0.06] text-slate-400"><tr>{head.map((h, k) => <th key={k} className="px-3 py-1.5 font-medium">{inline(h)}</th>)}</tr></thead>
            <tbody className="divide-y divide-white/10">{rest.map((r, k) => <tr key={k}>{r.map((c, j) => <td key={j} className="px-3 py-1.5">{inline(c)}</td>)}</tr>)}</tbody>
          </table>
        </div>,
      )
    } else if (/^\s*[-*] /.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\s*[-*] /.test(lines[i])) items.push(lines[i++].replace(/^\s*[-*] /, ''))
      out.push(<ul key={out.length} className="my-1 list-disc space-y-0.5 pl-5">{items.map((t, k) => <li key={k}>{inline(t)}</li>)}</ul>)
    } else {
      out.push(<Fragment key={out.length}>{line.trim() === '' ? <div className="h-2" /> : <div>{inline(line)}</div>}</Fragment>)
      i++
    }
  }
  return <>{out}</>
}
