// Unified proxy path mapping for Dream Server services
export const PROXY_PATHS = {
  'open-webui': '/chat',
  'n8n': '/n8n',
  'llama-server': '/llm',
  'llm': '/llm',
  'dashboard-api': '/api',
  'comfyui': '/comfy',
  'searxng': '/searx',
  'perplexica': '/search',
  'dreamforge': '/forge',
  'openclaw': '/claw',
  'token-spy': '/spy',
  'whisper': '/whisper',
  'qdrant': '/qdrant',
  'litellm': '/gateway',
  'embeddings': '/embeddings',
  'tts': '/tts',
  'privacy-shield': '/shield',
  'opencode': '/code',
  'ape': '/ape'
};

/**
 * Generates an external URL for a service, using Nginx proxy paths if available.
 * @param {number} port - Fallback port for the service.
 * @param {string} id - The service ID (used to match against PROXY_PATHS).
 * @param {string} uiPath - Optional subpath for the service UI (prepended to the final URL).
 * @returns {string} The fully qualified URL.
 */
export const getExternalUrl = (port, id, uiPath = '/') => {
  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost';
  const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';

  // 1. Check for explicit proxy path mapping
  if (id && PROXY_PATHS[id]) {
    const baseUrl = origin + PROXY_PATHS[id];
    // Append uiPath if it's not the root path
    const suffix = (uiPath && uiPath !== '/') ? (uiPath.startsWith('/') ? uiPath : '/' + uiPath) : '';
    return baseUrl + suffix;
  }

  // 2. Fallback to IP:Port if no proxy mapping exists
  return `http://${hostname}:${port}${uiPath && uiPath !== '/' ? uiPath : ''}`;
};
