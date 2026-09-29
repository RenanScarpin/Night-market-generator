import { BrowserLink } from '../platform/browser/router'

export function NotFoundPage() {
  return (
    <main className="page-shell">
      <section className="empty-market route-missing">
        <div className="empty-crosshair" aria-hidden="true">404</div>
        <h1>Wrong part of Night City.</h1>
        <p>That route does not exist yet.</p>
        <BrowserLink to="/market" className="route-home-link">
          Return to the Night Market →
        </BrowserLink>
      </section>
    </main>
  )
}
