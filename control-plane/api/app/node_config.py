from __future__ import annotations

import hashlib
import json
from typing import Any

from .models import Line, Node, SocksProfile
from .platform_secrets import get_primary_bootstrap_token


def _collect_line_cidrs(lines: list[Line]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if not line.is_enabled or line.status != "active":
            continue
        for cidr in (line.source_cidrs or "").split(","):
            c = cidr.strip()
            if c and c not in seen:
                seen.add(c)
                out.append(c)
    return out


def _merge_static_routes(
    manual: list[dict[str, Any]],
    auto_prefixes: list[str],
    device: str,
) -> list[dict[str, Any]]:
    """OpenVPN auto return routes override manual entries for the same prefix."""
    auto_set = {p.strip() for p in auto_prefixes if (p or "").strip()}
    merged: list[dict[str, Any]] = []
    for r in manual:
        prefix = (r.get("prefix") or "").strip()
        if prefix and prefix in auto_set:
            continue
        merged.append(dict(r))
    existing = {(r.get("prefix") or "").strip() for r in merged}
    for prefix in auto_prefixes:
        p = prefix.strip()
        if not p:
            continue
        merged.append(
            {
                "prefix": p,
                "device": device,
                "comment": "auto: openvpn return path",
            }
        )
        existing.add(p)
    return merged


def build_node_payload(
    node: Node,
    lines: list[Line],
    socks_by_id: dict[int, SocksProfile],
) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    for line in lines:
        if not line.is_enabled or line.status != "active":
            continue
        sp = socks_by_id[line.socks_profile_id]
        cidrs = [c.strip() for c in line.source_cidrs.split(",") if c.strip()]
        rules.append(
            {
                "lineId": line.id,
                "tid": line.tid,
                "lineName": line.name,
                "sourceCidrs": cidrs,
                "socks": {
                    "host": (sp.host or "").strip(),
                    "port": sp.port,
                    "username": ((sp.username or "").strip() or None),
                    "password": ((sp.password or "").strip() or None),
                },
            }
        )

    connect_mode = node.connect_mode or "ethernet"
    vpn: dict[str, Any] | None = None
    if connect_mode == "openvpn" and node.vpn_config_json:
        try:
            vpn = json.loads(node.vpn_config_json)
        except json.JSONDecodeError:
            vpn = None

    static_routes: list[dict[str, Any]] = []
    if node.static_routes_json:
        try:
            raw = json.loads(node.static_routes_json)
            if isinstance(raw, list):
                static_routes = raw
        except json.JSONDecodeError:
            static_routes = []

    tproxy_iface: str | None = None
    if connect_mode == "openvpn" and vpn and vpn.get("enabled", True):
        tproxy_iface = (vpn.get("dev") or "tun0").strip() or "tun0"
        if vpn.get("auto_static_routes", True):
            auto_cidrs = list(vpn.get("remote_networks") or [])
            for c in _collect_line_cidrs(lines):
                if c not in auto_cidrs:
                    auto_cidrs.append(c)
            static_routes = _merge_static_routes(static_routes, auto_cidrs, tproxy_iface)

    return {
        "nodeId": node.id,
        "nodeName": node.name,
        "connectMode": connect_mode,
        "vpn": vpn,
        "tproxyIface": tproxy_iface,
        "bootstrapToken": get_primary_bootstrap_token(),
        "staticRoutes": static_routes,
        "dataplane": {
            "tproxyPort": 12345,
            "defaultAction": "drop",
            "rules": rules,
            "dnsFallbackEnabled": True,
            "dnsIntlServer": "1.1.1.1",
        },
    }


def payload_version(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
