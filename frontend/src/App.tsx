import { useEffect } from 'react'
import { CataloguePage } from './pages/CataloguePage'
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

  let page
  if (pathname === '/market') {
    page = <GeneratorPage locationSearch={location.search} />
  } else if (pathname === '/catalogue') {
    page = <CataloguePage locationSearch={location.search} />
  } else {
    page = <NotFoundPage />
  }

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
          <BrowserLink
            className={pathname === '/catalogue' ? 'nav-link nav-active' : 'nav-link'}
            to="/catalogue"
          >
            Catalogue
          </BrowserLink>
        </nav>
      </header>

      {page}

      <footer className="site-footer">
        <span>Cyberpunk RED Night Market tooling</span>
        <span>RAW + canon-2045 expanded generation</span>
      </footer>
    </div>
  )
}
