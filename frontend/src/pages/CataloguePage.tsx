import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ApiError,
  getCategories,
  getManufacturers,
  getMarketTags,
  listItems,
} from '../api/client'
import { CatalogueCard } from '../components/CatalogueCard'
import { CatalogueFilters } from '../components/CatalogueFilters'
import { navigate } from '../platform/browser/router'
import type {
  CategoryDetail,
  ItemSummary,
  ManufacturerSummary,
  MarketTagDetail,
} from '../types/api'
import {
  buildCataloguePath,
  EMPTY_CATALOGUE_FILTERS,
  parseCatalogueSearch,
  type CatalogueFilters as FilterState,
} from '../utils/catalogueUrl'

interface Props {
  locationSearch: string
}

const PAGE_SIZE = 24

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : 'The catalogue API could not be reached.'
}

export function CataloguePage({ locationSearch }: Props) {
  const parsed = useMemo(() => parseCatalogueSearch(locationSearch), [locationSearch])
  const [draft, setDraft] = useState<FilterState>(parsed)
  const [items, setItems] = useState<ItemSummary[]>([])
  const [total, setTotal] = useState(0)
  const [categories, setCategories] = useState<CategoryDetail[]>([])
  const [tags, setTags] = useState<MarketTagDetail[]>([])
  const [manufacturers, setManufacturers] = useState<ManufacturerSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingOptions, setLoadingOptions] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const requestSerial = useRef(0)

  useEffect(() => {
    setDraft(parsed)
  }, [parsed])

  useEffect(() => {
    let active = true
    setLoadingOptions(true)

    Promise.all([getCategories(), getMarketTags(), getManufacturers()])
      .then(([categoryRows, tagRows, manufacturerRows]) => {
        if (!active) return
        setCategories(categoryRows)
        setTags(
          tagRows.filter(
            (tag) =>
              (tag.item_count ?? 0) > 0 &&
              tag.tag_group !== 'core_raw' &&
              tag.tag_group !== 'market',
          ),
        )
        setManufacturers(manufacturerRows)
      })
      .catch((err: unknown) => {
        if (active) setError(errorMessage(err))
      })
      .finally(() => {
        if (active) setLoadingOptions(false)
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    const serial = ++requestSerial.current
    setLoading(true)
    setError(null)

    const min = parsed.minCost ? Number(parsed.minCost) : undefined
    const max = parsed.maxCost ? Number(parsed.maxCost) : undefined

    if (min !== undefined && max !== undefined && min > max) {
      setItems([])
      setTotal(0)
      setError('Minimum price cannot be greater than maximum price.')
      setLoading(false)
      return
    }

    listItems({
      q: parsed.q || undefined,
      category: parsed.category || undefined,
      tag: parsed.tag || undefined,
      manufacturer: parsed.manufacturer || undefined,
      minCostEb: min,
      maxCostEb: max,
      limit: PAGE_SIZE,
      offset: (parsed.page - 1) * PAGE_SIZE,
    })
      .then((result) => {
        if (serial !== requestSerial.current) return
        setItems(result.items)
        setTotal(result.total)
      })
      .catch((err: unknown) => {
        if (serial !== requestSerial.current) return
        setItems([])
        setTotal(0)
        setError(errorMessage(err))
      })
      .finally(() => {
        if (serial === requestSerial.current) setLoading(false)
      })
  }, [parsed])

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const page = Math.min(parsed.page, pageCount)

  useEffect(() => {
    if (!loading && total > 0 && parsed.page > pageCount) {
      navigate(buildCataloguePath({ ...parsed, page: pageCount }), { replace: true })
    }
  }, [loading, pageCount, parsed, total])
  const resultStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1
  const resultEnd = Math.min(page * PAGE_SIZE, total)

  function applyFilters() {
    navigate(buildCataloguePath({ ...draft, page: 1 }))
  }

  function resetFilters() {
    setDraft(EMPTY_CATALOGUE_FILTERS)
    navigate('/catalogue')
  }

  function changePage(nextPage: number) {
    if (nextPage < 1 || nextPage > pageCount || nextPage === page) return
    navigate(buildCataloguePath({ ...parsed, page: nextPage }))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <main className="page-shell catalogue-page">
      <header className="catalogue-hero">
        <span className="eyebrow">CANON 2045 DATABASE</span>
        <h1>Street Catalogue</h1>
        <p>
          Browse all 1,150 canonical records behind the Night Market generator. Search by name,
          source taxonomy, generator semantics, manufacturer, or actual eurobuck price.
        </p>
      </header>

      <CatalogueFilters
        value={draft}
        categories={categories}
        tags={tags}
        manufacturers={manufacturers}
        loadingOptions={loadingOptions}
        onChange={setDraft}
        onSubmit={applyFilters}
        onReset={resetFilters}
      />

      {error && (
        <div className="error-banner catalogue-error" role="alert">
          <strong>Catalogue query failed.</strong>
          <span>{error}</span>
        </div>
      )}

      <section className="catalogue-results" aria-live="polite">
        <header className="catalogue-results-header">
          <div>
            <span className="eyebrow">SEARCH RESULTS</span>
            <h2>{loading ? 'Querying the market…' : `${total.toLocaleString()} item${total === 1 ? '' : 's'} found`}</h2>
          </div>
          {!loading && total > 0 && (
            <div className="catalogue-range">
              Showing <strong>{resultStart}–{resultEnd}</strong> of <strong>{total}</strong>
            </div>
          )}
        </header>

        {loading && (
          <div className="catalogue-loading-grid" aria-hidden="true">
            {Array.from({ length: 8 }, (_, index) => (
              <div className="catalogue-skeleton" key={index} />
            ))}
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="catalogue-empty">
            <div className="empty-crosshair">∅</div>
            <h3>Nothing in this shipment.</h3>
            <p>Try widening the filters or clearing the current query.</p>
            <button className="text-button" type="button" onClick={resetFilters}>
              Reset catalogue
            </button>
          </div>
        )}

        {!loading && items.length > 0 && (
          <div className="catalogue-grid">
            {items.map((item) => (
              <CatalogueCard key={item.item_id} item={item} />
            ))}
          </div>
        )}

        {!loading && total > PAGE_SIZE && (
          <nav className="catalogue-pagination" aria-label="Catalogue pagination">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => changePage(page - 1)}
            >
              ← Previous
            </button>
            <span>
              Page <strong>{page}</strong> / {pageCount}
            </span>
            <button
              type="button"
              disabled={page >= pageCount}
              onClick={() => changePage(page + 1)}
            >
              Next →
            </button>
          </nav>
        )}
      </section>
    </main>
  )
}
