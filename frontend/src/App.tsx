import { GeneratorPage } from './pages/GeneratorPage'

export default function App() {
  return (
    <div className="app-frame">
      <header className="site-header">
        <a className="brand" href="/" aria-label="Night Market home">
          <span className="brand-mark">NM</span>
          <span>
            <strong>NIGHT MARKET</strong>
            <small>CANON 2045 CATALOGUE</small>
          </span>
        </a>
        <nav className="site-nav" aria-label="Primary navigation">
          <span className="nav-active">Generator</span>
          <span className="nav-coming" title="Coming in the next milestone">Catalogue</span>
        </nav>
      </header>
      <GeneratorPage />
      <footer className="site-footer">
        <span>Cyberpunk RED Night Market tooling</span>
        <span>RAW + canon-2045 expanded generation</span>
      </footer>
    </div>
  )
}
