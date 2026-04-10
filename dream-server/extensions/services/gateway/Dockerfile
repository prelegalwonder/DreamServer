# Build context: dream-server repository root
FROM nginx:alpine

RUN apk add --no-cache python3 py3-yaml

COPY scripts/nginx/00-ws-map.conf /etc/nginx/conf.d/00-ws-map.conf
COPY extensions/services/gateway/nginx.conf /etc/nginx/conf.d/default.conf
COPY scripts/render_service_proxy_conf.py /usr/local/lib/dream/render_service_proxy_conf.py
COPY extensions/services/gateway/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 3080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:3080/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
