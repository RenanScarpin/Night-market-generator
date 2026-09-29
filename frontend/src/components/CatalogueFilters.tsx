import type { FormEvent } from 'react'
import type { CategoryDetail, ManufacturerSummary, MarketTagDetail } from '../types/api'
import type { CatalogueFilters as Filters } from '../utils/catalogueUrl'

interface Props {
  value: Filters
  categories: CategoryDetail[]
  tags: MarketTagDetail[]
  manufacturers: ManufacturerSummary[]
  loadingOptions: boolean
  onChange: (value: Filters) => void
  onSubmit: () => void
  onReset: () => void
}

export function CatalogueFilters({
  value,
  categories,
  tags,
  manufacturers,
  loadingOptions,
  onChange,
  onSubmit,
  onReset,
}: Props) {
  function patch(patchValue: Partial<Filters>) {
    onChange({ ...value, ...patchValue })
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    onSubmit()
  }

  const categoryById = new Map(categories.map((category) => [category.category_id, category]))
  const tagGroups = new Map<string, MarketTagDetail[]>()
  for (const tag of tags) {
    const group = tagGroups.get(tag.tag_group) ?? []
    group.push(tag)
    tagGroups.set(tag.tag_group, group)
  }

  return (
    <form className="catalogue-filter-panel" onSubmit={submit}>
      <div className="catalogue-filter-header">
        <div>
          <span className="eyebrow">DATABASE QUERY</span>
          <h2>Find something on the Street.</h2>
          <p>Search the complete canon-2045 equipment catalogue and narrow it by market semantics.</p>
        </div>
        <button className="text-button" type="button" onClick={onReset}>
          Reset filters
        </button>
      </div>

      <div className="catalogue-filter-grid">
        <label className="field catalogue-search-field">
          <span>Search</span>
          <input
            type="search"
            value={value.q}
            onChange={(event) => patch({ q: event.target.value, page: 1 })}
            placeholder="Militech, cyberarm, shotgun…"
          />
          <small>Name or known alias.</small>
        </label>

        <label className="field">
          <span>Category</span>
          <select
            value={value.category}
            disabled={loadingOptions}
            onChange={(event) => patch({ category: event.target.value, page: 1 })}
          >
            <option value="">All categories</option>
            {categories.filter((category) => (category.item_count ?? 0) > 0).map((category) => {
              const parent = category.parent_category_id
                ? categoryById.get(category.parent_category_id)
                : null
              return (
                <option key={category.category_id} value={category.slug}>
                  {parent ? `${parent.name} › ` : ''}{category.name} ({category.item_count ?? 0})
                </option>
              )
            })}
          </select>
          <small>Official/index taxonomy.</small>
        </label>

        <label className="field">
          <span>Market tag</span>
          <select
            value={value.tag}
            disabled={loadingOptions}
            onChange={(event) => patch({ tag: event.target.value, page: 1 })}
          >
            <option value="">All market tags</option>
            {[...tagGroups.entries()].map(([group, entries]) => (
              <optgroup key={group} label={group.replaceAll('_', ' ').toUpperCase()}>
                {entries.map((tag) => (
                  <option key={tag.tag_id} value={tag.code}>
                    {tag.name} ({tag.item_count ?? 0})
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
          <small>Generator-facing semantic classification.</small>
        </label>

        <label className="field">
          <span>Manufacturer</span>
          <select
            value={value.manufacturer}
            disabled={loadingOptions}
            onChange={(event) => patch({ manufacturer: event.target.value, page: 1 })}
          >
            <option value="">All manufacturers</option>
            {manufacturers.map((manufacturer) => (
              <option key={manufacturer.company_id} value={manufacturer.name}>
                {manufacturer.name} ({manufacturer.item_count})
              </option>
            ))}
          </select>
          <small>Only explicit manufacturer assignments.</small>
        </label>

        <label className="field">
          <span>Minimum price</span>
          <input
            inputMode="numeric"
            value={value.minCost}
            onChange={(event) => patch({ minCost: event.target.value.replace(/[^0-9]/g, ''), page: 1 })}
            placeholder="0"
          />
          <small>Eurobucks; fixed-price variants.</small>
        </label>

        <label className="field">
          <span>Maximum price</span>
          <input
            inputMode="numeric"
            value={value.maxCost}
            onChange={(event) => patch({ maxCost: event.target.value.replace(/[^0-9]/g, ''), page: 1 })}
            placeholder="5000"
          />
          <small>Eurobucks; fixed-price variants.</small>
        </label>
      </div>

      <button className="catalogue-search-button" type="submit">
        <span>Search catalogue</span>
        <span aria-hidden="true">→</span>
      </button>
    </form>
  )
}
