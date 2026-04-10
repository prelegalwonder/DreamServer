#!/usr/bin/env python3
"""Generate nginx location blocks for per-service reverse proxy paths.

Used at container startup by dashboard and dream-gateway images.
Reads the same manifest layout as resolve-compose-stack / dashboard-api config.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Iterator

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

SKIP_PROXY_IDS = frozenset({"dashboard", "dashboard-api"})
GPU_BACKEND = os.environ.get("GPU_BACKEND", "nvidia").lower()
EXTENSIONS_SERVICES = Path(
    os.environ.get("DREAM_EXTENSIONS_SERVICES", "/dream-server/extensions/services")
)
USER_EXTENSIONS = Path(os.environ.get("DREAM_USER_EXTENSIONS_DIR", "/data/user-extensions"))
OUT_PATH = Path(os.environ.get("NGINX_SERVICES_CONF", "/etc/nginx/dream-services.conf"))


def _normalize_gateway_path(service_id: str, raw: Any) -> str:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        seg = service_id.strip("/").replace("//", "/") or service_id
        return f"/{seg}"
    path = str(raw).strip()
    if not path.startswith("/"):
        path = "/" + path
    inner = path.strip("/")
    if not inner:
        seg = service_id.strip("/") or service_id
        return f"/{seg}"
    return "/" + inner


def _read_manifest(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    elif yaml is not None:
        data = yaml.safe_load(text)
    else:
        return None
    return data if isinstance(data, dict) else None


def _manifest_paths(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    for item in sorted(root.iterdir()):
        if not item.is_dir():
            continue
        if (item / "compose.yaml.disabled").exists() or (item / "compose.yml.disabled").exists():
            continue
        for name in ("manifest.yaml", "manifest.yml", "manifest.json"):
            candidate = item / name
            if candidate.exists():
                out.append(candidate)
                break
    return out


def _user_ext_manifest_paths(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    for item in sorted(root.iterdir()):
        if not item.is_dir():
            continue
        if not (item / "compose.yaml").exists():
            continue
        for name in ("manifest.yaml", "manifest.yml", "manifest.json"):
            candidate = item / name
            if candidate.exists():
                out.append(candidate)
                break
    return out


def _service_from_manifest(manifest: dict[str, Any]) -> dict[str, Any] | None:
    if manifest.get("schema_version") != "dream.services.v1":
        return None
    service = manifest.get("service")
    if not isinstance(service, dict):
        return None
    service_id = service.get("id")
    if not service_id:
        return None
    supported = service.get("gpu_backends", ["amd", "nvidia", "apple"])
    if GPU_BACKEND == "apple":
        if service.get("type") == "host-systemd":
            return None
    elif GPU_BACKEND not in supported and "all" not in supported and "none" not in supported:
        return None
    default_host = service.get("default_host", "localhost")
    port = int(service.get("port", 0))
    gateway_path = _normalize_gateway_path(service_id, service.get("gateway_path"))
    return {
        "id": service_id,
        "host": default_host,
        "port": port,
        "gateway_path": gateway_path,
    }


def iter_proxy_services() -> Iterator[dict[str, Any]]:
    seen_paths: dict[str, str] = {}
    for mp in _manifest_paths(EXTENSIONS_SERVICES) + _user_ext_manifest_paths(USER_EXTENSIONS):
        manifest = _read_manifest(mp)
        if not manifest:
            continue
        row = _service_from_manifest(manifest)
        if not row or row["id"] in SKIP_PROXY_IDS:
            continue
        if row["port"] <= 0:
            continue
        path = row["gateway_path"]
        prev = seen_paths.get(path)
        if prev and prev != row["id"]:
            print(
                f"WARNING: duplicate gateway_path {path!r} for {row['id']!r} and {prev!r} — skipping {row['id']!r}",
                file=sys.stderr,
            )
            continue
        seen_paths[path] = row["id"]
        yield row


LOCATION_TEMPLATE = """
    location = {path} {{
        return 308 {path}/;
    }}
    location ^~ {path}/ {{
        proxy_pass http://{upstream_host}:{upstream_port}/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }}
"""


def render_conf() -> str:
    parts: list[str] = [
        "# Generated by render_service_proxy_conf.py — do not edit\n",
    ]
    for row in sorted(iter_proxy_services(), key=lambda r: r["gateway_path"]):
        parts.append(
            LOCATION_TEMPLATE.format(
                path=row["gateway_path"],
                upstream_host=row["host"],
                upstream_port=row["port"],
            )
        )
    return "".join(parts).strip() + "\n"


def main() -> int:
    if yaml is None:
        print("ERROR: PyYAML is required to render service proxy config", file=sys.stderr)
        return 1
    body = render_conf()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(body, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(body)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
