import { useEffect, useState, type MouseEvent, type ReactNode } from 'react'

export interface BrowserLocation {
  pathname: string
  search: string
}

export interface NavigateOptions {
  replace?: boolean
}

function readLocation(): BrowserLocation {
  return {
    pathname: window.location.pathname,
    search: window.location.search,
  }
}

export function useBrowserLocation(): BrowserLocation {
  const [location, setLocation] = useState<BrowserLocation>(() => readLocation())

  useEffect(() => {
    function handleLocationChange() {
      setLocation(readLocation())
    }

    window.addEventListener('popstate', handleLocationChange)
    return () => window.removeEventListener('popstate', handleLocationChange)
  }, [])

  return location
}

export function navigate(to: string, options: NavigateOptions = {}) {
  if (options.replace) {
    window.history.replaceState(null, '', to)
  } else {
    window.history.pushState(null, '', to)
  }
  window.dispatchEvent(new PopStateEvent('popstate'))
}

interface BrowserLinkProps {
  to: string
  className?: string
  children: ReactNode
  replace?: boolean
  'aria-label'?: string
}

export function BrowserLink({
  to,
  className,
  children,
  replace = false,
  'aria-label': ariaLabel,
}: BrowserLinkProps) {
  function handleClick(event: MouseEvent<HTMLAnchorElement>) {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    ) {
      return
    }

    event.preventDefault()
    navigate(to, { replace })
  }

  return (
    <a href={to} className={className} aria-label={ariaLabel} onClick={handleClick}>
      {children}
    </a>
  )
}
