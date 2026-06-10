from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

GFC_ETC = Path(os.environ.get("GFC_ETC", "/etc/gfc-node"))
ROUTES_STATE = GFC_ETC / "static-routes.json"


def _run(cmd: list[str]) -> tuple[bool, str]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        return True, (r.stdout or "").strip()
    return False, (r.stderr or r.stdout or "failed").strip()


def ensure_tproxy_policy(tproxy_port: int) -> list[str]:
    """Policy routing for TPROXY reply path (mark 0x1 -> local table)."""
    msgs: list[str] = []
    ok, _ = _run(["ip", "rule", "show", "fwmark", "0x1"])
    if not ok:
        ok, err = _run(["ip", "rule", "add", "fwmark", "0x1", "lookup", "100"])
        msgs.append("ip rule fwmark 1 -> table 100" if ok else f"ip rule warn: {err}")
    ok, _ = _run(["ip", "route", "show", "table", "100"])
    if "local" not in _:
        ok, err = _run(
            ["ip", "route", "add", "local", "0.0.0.0/0", "dev", "lo", "table", "100"]
        )
        msgs.append("ip route table 100 local" if ok else f"route local warn: {err}")
    return msgs


def apply_static_routes(routes: list[dict[str, Any]]) -> tuple[bool, str]:
    ROUTES_STATE.parent.mkdir(parents=True, exist_ok=True)
    previous: list[dict[str, Any]] = []
    if ROUTES_STATE.is_file():
        try:
            raw = json.loads(ROUTES_STATE.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                previous = raw
        except (OSError, json.JSONDecodeError):
            previous = []

    ROUTES_STATE.write_text(json.dumps(routes, ensure_ascii=False, indent=2), encoding="utf-8")

    messages: list[str] = []
    ok_all = True
    new_prefixes = {(r.get("prefix") or "").strip() for r in routes if (r.get("prefix") or "").strip()}

    for r in previous:
        prefix = (r.get("prefix") or "").strip()
        if not prefix or prefix in new_prefixes:
            continue
        ok, err = _run(["ip", "route", "del", prefix])
        if ok:
            messages.append(f"route {prefix} removed (stale)")
        else:
            messages.append(f"route {prefix} stale del warn: {err}")

    for r in routes:
        prefix = (r.get("prefix") or "").strip()
        if not prefix:
            continue
        next_hop = (r.get("nextHop") or r.get("next_hop") or "").strip() or None
        device = (r.get("device") or r.get("iface") or "").strip() or None
        if not device:
            device = os.environ.get("GFC_TPROXY_IFACE", "").strip() or None
        cmd = ["ip", "route", "replace", prefix]
        if next_hop:
            cmd += ["via", next_hop]
        if device:
            cmd += ["dev", device]
        elif next_hop:
            gr = subprocess.run(
                ["ip", "route", "get", next_hop],
                capture_output=True,
                text=True,
                check=False,
            )
            parts = (gr.stdout or "").split()
            if "dev" in parts:
                cmd += ["dev", parts[parts.index("dev") + 1]]
        ok, err = _run(cmd)
        if ok:
            messages.append(f"route {prefix} ok")
        else:
            ok_all = False
            messages.append(f"route {prefix} fail: {err}")

    if not routes:
        messages.append("no static routes configured")
    return ok_all, "; ".join(messages)
