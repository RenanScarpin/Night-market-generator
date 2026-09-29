import { titleCase } from '../utils/format'

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
