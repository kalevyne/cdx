import Papa from 'papaparse'
import { useMemo } from 'react'

// Rendering is the slow part, not parsing: show the top of big tables only.
const MAX_ROWS = 1000

/** A CSV/TSV file as a table, first row as the header. */
export default function TablePreview({ text }: { text: string }) {
  const rows = useMemo(
    () => Papa.parse<string[]>(text, { skipEmptyLines: true }).data,
    [text],
  )
  const [header = [], ...body] = rows
  const shown = body.slice(0, MAX_ROWS)

  return (
    <>
      <table className="w-max min-w-full border-separate border-spacing-0 text-xs">
        <thead>
          <tr>
            {header.map((cell, i) => (
              <th
                key={i}
                className="sticky top-0 border-b bg-muted px-3 py-2 text-left font-medium whitespace-nowrap"
              >
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="font-mono">
          {shown.map((row, r) => (
            <tr key={r} className="even:bg-muted/40">
              {row.map((cell, c) => (
                <td key={c} className="max-w-96 truncate border-b px-3 py-1.5" title={cell}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {body.length > MAX_ROWS && (
        <p className="sticky bottom-0 left-0 border-t bg-background px-3 py-2 text-xs text-muted-foreground">
          Showing the first {MAX_ROWS.toLocaleString()} of {body.length.toLocaleString()} rows.
          Download the file to see the rest.
        </p>
      )}
    </>
  )
}
