#!/bin/sh
set -e

export DREAM_EXTENSIONS_SERVICES="${DREAM_EXTENSIONS_SERVICES:-/dream-server/extensions/services}"
export DREAM_USER_EXTENSIONS_DIR="${DREAM_USER_EXTENSIONS_DIR:-/data/user-extensions}"
export NGINX_SERVICES_CONF="${NGINX_SERVICES_CONF:-/etc/nginx/dream-services.conf}"
export GPU_BACKEND="${GPU_BACKEND:-nvidia}"

echo "[dream-gateway] Rendering service proxy routes -> $NGINX_SERVICES_CONF"
python3 /usr/local/lib/dream/render_service_proxy_conf.py || {
    echo "[dream-gateway] WARNING: render_service_proxy_conf failed; writing stub"
    printf '# dream-gateway proxy routes unavailable\n' > "$NGINX_SERVICES_CONF"
}

exec nginx -g 'daemon off;'
