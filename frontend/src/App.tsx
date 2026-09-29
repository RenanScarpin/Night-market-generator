import { useEffect } from 'react'
import { GeneratorPage } from './pages/GeneratorPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { BrowserLink, navigate, useBrowserLocation } from './platform/browser/router'

export default function App() {
  const location = useBrowserLocation()
  const pathname = location.pathname === '/' ? '/market' : location.pathname

  useEffect(() => {
    if (location.pathname === '/') {
      navigate(`/market${location.search}`, { replace: true })
    }
  }, [location.pathname, location.search])

  return (
    <div className="app-frame">
      <header className="site-header">
        <BrowserLink className="brand" to="/market" aria-label="Night Market home">
          <span className="brand-mark">NM</span>
          <span>
            <strong>NIGHT MARKET</strong>
            <small>CANON 2045 CATALOGUE</small>
          </span>
        </BrowserLink>
        <nav className="site-nav" aria-label="Primary navigation">
          <BrowserLink
            className={pathname === '/market' ? 'nav-link nav-active' : 'nav-link'}
            to="/market"
          >
            Generator
          </BrowserLink>
          <span className="nav-coming" title="Coming in the next milestone">Catalogue</span>
        </nav>
      </header>

      {pathname === '/market' ? (
        <GeneratorPage locationSearch={location.search} />
      ) : (
        <NotFoundPage />
      )}

      <footer className="site-footer">
        <span>Cyberpunk RED Night Market tooling</span>
        <span>RAW + canon-2045 expanded generation</span>
      </footer>
    </div>
  )
}
