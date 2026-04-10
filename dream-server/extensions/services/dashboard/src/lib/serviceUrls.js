/**
 * Build same-origin URLs for services exposed via dashboard / dream-gateway nginx.
 */

/** @param {string} gatewayPath e.g. /chat */
/** @param {string} [uiPath] manifest ui_path, default '/' */
export function gatewayServiceHref(gatewayPath, uiPath = '/') {
  const raw = (gatewayPath || '').toString().trim()
  let base = raw.startsWith('/') ? raw : `/${raw}`
  base = base.replace(/\/+$/, '') || '/'
  const prefix = base === '/' ? '/' : base
  if (uiPath && uiPath !== '/') {
    const tail = uiPath.startsWith('/') ? uiPath : `/${uiPath}`
    return `${prefix}${tail}`
  }
  return prefix === '/' ? '/' : `${prefix}/`
}

/** @param {number} port */
export function getExternalUrl(port) {
  if (port == null || port === '') return null
  return typeof window !== 'undefined'
    ? `http://${window.location.hostname}:${port}`
    : `http://localhost:${port}`
}

/**
 * Prefer reverse-proxy path; fall back to host:port + ui_path.
 * @param {{ gateway_path?: string, port?: number, ui_path?: string }} link
 */
export function serviceBrowserHref(link) {
  const ui = link?.ui_path
  if (link?.gateway_path) {
    return gatewayServiceHref(link.gateway_path, ui || '/')
  }
  const base = getExternalUrl(link?.port)
  if (!base) return null
  return base + (ui && ui !== '/' ? ui : '')
}
