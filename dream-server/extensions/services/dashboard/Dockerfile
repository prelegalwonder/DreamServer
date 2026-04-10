# Dream Server Dashboard
# Build context: dream-server repository root (see docker-compose.base.yml)
# Stage 1: Build React SPA
FROM node:20-alpine AS builder

WORKDIR /app
COPY extensions/services/dashboard/package*.json ./
RUN npm ci
COPY extensions/services/dashboard/ ./
RUN npm run build

# Stage 2: Serve with nginx + generated service proxy routes
FROM nginx:alpine

RUN apk add --no-cache python3 py3-yaml

COPY --from=builder /app/dist /usr/share/nginx/html
COPY scripts/nginx/00-ws-map.conf /etc/nginx/conf.d/00-ws-map.conf
COPY extensions/services/dashboard/nginx.conf /etc/nginx/conf.d/default.conf
COPY scripts/render_service_proxy_conf.py /usr/local/lib/dream/render_service_proxy_conf.py
COPY extensions/services/dashboard/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:3001/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
