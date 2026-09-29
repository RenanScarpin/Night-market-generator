import { titleCase } from '../utils/format'

// Extraction provenance is kept in the database but hidden from the player-facing mechanics view.
// The compact citation is rendered separately by ItemDetails.
const HIDDEN_MECHANICS_SECTIONS = new Set(['source'])

interface Props {
  value: unknown
  depth?: number
}

function Primitive({ value }: { value: unknown }) {
  if (typeof value === 'boolean') {
    return <span>{value ? 'Yes' : 'No'}</span>
  }
  if (value === null || value === undefined) {
    return <span className="muted">—</span>
  }
  return <span>{String(value)}</span>
}

export function MechanicsView({ value, depth = 0 }: Props) {
  if (Array.isArray(value)) {
    return (
      <ul className={`mechanics-list depth-${Math.min(depth, 3)}`}>
        {value.map((entry, index) => (
          <li key={index}>
            {typeof entry === 'object' && entry !== null ? (
              <MechanicsView value={entry} depth={depth + 1} />
            ) : (
              <Primitive value={entry} />
            )}
          </li>
        ))}
      </ul>
    )
  }

  if (typeof value === 'object' && value !== null) {
    const entries = Object.entries(value as Record<string, unknown>)
      .filter(([key]) => !HIDDEN_MECHANICS_SECTIONS.has(key.toLowerCase()))
    if (!entries.length) return <span className="muted">No structured mechanics.</span>

    return (
      <dl className={`mechanics-grid depth-${Math.min(depth, 3)}`}>
        {entries.map(([key, entry]) => (
          <div className="mechanics-row" key={key}>
            <dt>{titleCase(key)}</dt>
            <dd>
              {typeof entry === 'object' && entry !== null ? (
                <MechanicsView value={entry} depth={depth + 1} />
              ) : (
                <Primitive value={entry} />
              )}
            </dd>
          </div>
        ))}
      </dl>
    )
  }

  return <Primitive value={value} />
}
