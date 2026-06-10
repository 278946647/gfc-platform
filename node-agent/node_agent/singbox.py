from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

SINGBOX_CONFIG = Path(os.environ.get("GFC_ETC", "/etc/gfc-node")) / "sing-box.json"
DNS_DIRECT_TAG = "dns-direct"
DNS_INTL_DEFAULT = "1.1.1.1"
DNS_DOH_PATH = "/dns-query"


def _intl_dns_server(dataplane: dict[str, Any]) -> str:
    """International DNS (DoH) address — same for SOCKS path and node-direct path."""
    return (
        dataplane.get("dnsIntlServer")
        or dataplane.get("dnsFallbackServer")
        or os.environ.get("GFC_DNS_INTL_SERVER")
        or os.environ.get("GFC_DNS_FALLBACK_SERVER")
        or DNS_INTL_DEFAULT
    ).strip()


def _dns_fallback_enabled(dataplane: dict[str, Any]) -> bool:
    if "dnsFallbackEnabled" in dataplane:
        return bool(dataplane.get("dnsFallbackEnabled"))
    return os.environ.get("GFC_DNS_FALLBACK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _intl_doh_server(tag: str, server: str, *, detour: str | None = None) -> dict[str, Any]:
    """DoH on 443. No detour => forward node uses its own WAN (direct outbound)."""
    ob: dict[str, Any] = {
        "type": "https",
        "tag": tag,
        "server": server,
        "server_port": 443,
        "path": DNS_DOH_PATH,
    }
    if detour:
        ob["detour"] = detour
    return ob


def singbox_config_ok(path: Path | None = None) -> tuple[bool, str]:
    cfg = path or SINGBOX_CONFIG
    if not cfg.is_file():
        return False, "missing config"
    env = os.environ.copy()
    r = subprocess.run(
        ["sing-box", "check", "-c", str(cfg)],
        capture_output=True,
        text=True,
        env=env,
    )
    if r.returncode == 0:
        return True, ""
    return False, (r.stderr or r.stdout or "check failed").strip()


def render_singbox_config(
    dataplane: dict[str, Any],
    *,
    socks_dns_ok: dict[str, bool] | None = None,
) -> dict[str, Any]:
    rules_cfg = dataplane.get("rules") or []
    tproxy_port = int(dataplane.get("tproxyPort") or 12345)
    fallback_enabled = _dns_fallback_enabled(dataplane)
    intl_dns = _intl_dns_server(dataplane)
    socks_dns_ok = socks_dns_ok or {}

    outbounds: list[dict[str, Any]] = [{"type": "direct", "tag": "direct"}]
    # sing-box 1.13+: sniff must be a route rule action, not an inbound field.
    route_rules: list[dict[str, Any]] = [
        {"inbound": "tproxy-in", "action": "sniff"},
    ]
    dns_servers: list[dict[str, Any]] = []
    dns_rules: list[dict[str, Any]] = []

    for idx, rule in enumerate(rules_cfg):
        tag = f"socks-{rule.get('lineId', idx)}"
        socks = rule["socks"]
        ob: dict[str, Any] = {
            "type": "socks",
            "tag": tag,
            "server": socks["host"],
            "server_port": int(socks["port"]),
            "version": "5",
            # Many SOCKS5 providers reject UDP ASSOCIATE (code=7); tunnel UDP in TCP.
            "udp_over_tcp": {"enabled": True},
        }
        user = (socks.get("username") or "").strip()
        pw = (socks.get("password") or "").strip()
        if user:
            ob["username"] = user
            ob["password"] = pw
        ob["domain_resolver"] = "local-dns"
        outbounds.append(ob)

        dns_tag = f"dns-{tag}"
        proxy_dns_ok = socks_dns_ok.get(tag, True)
        if proxy_dns_ok:
            # International DoH via SOCKS (443; avoids blocked :53 on many SOCKS providers).
            dns_servers.append(_intl_doh_server(dns_tag, intl_dns, detour=tag))
        for cidr in rule.get("sourceCidrs") or []:
            route_rules.append(
                {
                    "source_ip_cidr": [cidr],
                    "action": "route",
                    "outbound": tag,
                }
            )
            if proxy_dns_ok:
                primary_dns = dns_tag
            elif fallback_enabled:
                # SOCKS down: intl DoH via forward-node WAN (direct outbound, no detour).
                primary_dns = DNS_DIRECT_TAG
            else:
                primary_dns = "local-dns"
            dns_rules.append(
                {
                    "source_ip_cidr": [cidr],
                    "action": "route",
                    "server": primary_dns,
                }
            )

    socks_rules = [r for r in route_rules if r.get("action") == "route"]
    final = "direct"
    if dataplane.get("defaultAction") == "drop":
        if socks_rules:
            final = socks_rules[-1]["outbound"]
        else:
            route_rules.append({"action": "reject"})

    # sing-box 1.12+ requires default_domain_resolver when auto_detect_interface is set.
    all_dns_servers: list[dict[str, Any]] = [{"type": "local", "tag": "local-dns"}]
    if fallback_enabled and rules_cfg:
        all_dns_servers.append(_intl_doh_server(DNS_DIRECT_TAG, intl_dns))
    all_dns_servers.extend(dns_servers)
    if rules_cfg:
        # Hijack DNS from TPROXY instead of SOCKS UDP ASSOCIATE (often unsupported).
        route_rules.insert(1, {"protocol": "dns", "action": "hijack-dns"})

    route_block: dict[str, Any] = {
        "rules": route_rules,
        "final": final,
        "auto_detect_interface": True,
        "default_domain_resolver": "local-dns",
    }

    cfg: dict[str, Any] = {
        "log": {"level": "info"},
        "inbounds": [
            {
                "type": "tproxy",
                "tag": "tproxy-in",
                "listen": "0.0.0.0",
                "listen_port": tproxy_port,
            }
        ],
        "outbounds": outbounds,
        "route": route_block,
        "dns": {
            "servers": all_dns_servers,
            "rules": dns_rules,
            "final": DNS_DIRECT_TAG
            if (fallback_enabled and rules_cfg)
            else (all_dns_servers[-1]["tag"] if len(all_dns_servers) > 1 else "local-dns"),
            "strategy": "prefer_ipv4",
            "independent_cache": True,
        },
    }
    return cfg
