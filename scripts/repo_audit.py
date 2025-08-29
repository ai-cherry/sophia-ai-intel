#!/usr/bin/env python3
"""
Sophia Supreme – Repository Integration Auditor
Outputs:
  reports/audit/<timestamp>/
    - audit_report.json
    - issues.csv
    - short_notes.md  (≤ 30 lines)
"""

import argparse, os, re, sys, json, csv, time, subprocess, pathlib, socket
from datetime import datetime
from urllib.parse import urljoin, urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# --------- util ---------
ROOT = pathlib.Path(__file__).resolve().parents[1]  # repo root by default

def nowstamp():
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")

def write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def write_csv(p, rows, header):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def write_short_md(p, lines):
    # enforce ≤ 30 lines
    lines = lines[:30]
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def http_get(url, timeout=6, headers=None):
    req = Request(url, headers=headers or {})
    try:
        with urlopen(req, timeout=timeout) as r:
            return r.getcode(), r.read()
    except Exception as e:
        return None, str(e)

def http_post_json(url, payload, timeout=8, headers=None):
    data = json.dumps(payload).encode("utf-8")
    h = {"Content-Type": "application/json"}
    if headers: h.update(headers)
    try:
        req = Request(url, data=data, headers=h, method="POST")
        with urlopen(req, timeout=timeout) as r:
            return r.getcode(), r.read()
    except Exception as e:
        return None, str(e)

def cmd_ok(args, cwd=None, timeout=120):
    try:
        r = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout, text=True)
        return r.returncode == 0, r.stdout
    except Exception as e:
        return False, str(e)

def port_open(host, port, timeout=2.0):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False

# --------- checks ---------
REQUIRED_UI = [
    "apps/sophia-dashboard/src/lib/config.ts",
    "apps/sophia-dashboard/src/app/api/chat/route.ts",
    "apps/sophia-dashboard/src/app/layout.tsx",
    "apps/sophia-dashboard/src/components/ChatRenderer.tsx",
    "apps/sophia-dashboard/src/components/ActivityFeed.tsx",
    "apps/sophia-dashboard/src/components/DebateScorecards.tsx",
    "apps/sophia-dashboard/src/app/api-health/page.tsx",
    "apps/sophia-dashboard/src/app/api/health/route.ts",
    "apps/sophia-dashboard/src/app/agent-factory/page.tsx",
    "apps/sophia-dashboard/src/app/swarm-monitor/page.tsx",
    "apps/sophia-dashboard/src/app/metrics/page.tsx",
]
DELETED_FILES = [
    "apps/sophia-dashboard/src/components/AgentSwarmPanel.tsx",  # mock panel must be gone
]

MOCK_PAT = re.compile(r"\b(mock|fake|placeholder|todo)\b", re.IGNORECASE)

EXCLUDE_DIRS = {".git", ".next", "node_modules", "dist", "build", ".turbo", ".vercel"}

def scan_mocks(base: pathlib.Path):
    issues = []
    for p in base.rglob("*"):
        if not p.is_file(): continue
        # skip vendor/build
        parts = set(p.relative_to(base).parts)
        if parts & EXCLUDE_DIRS: continue
        if p.suffix.lower() in {".png",".jpg",".jpeg",".gif",".webp",".ico",".lock",".map",".svg",".woff",".woff2",".ttf"}:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if MOCK_PAT.search(txt):
            issues.append((str(p.relative_to(ROOT)), "mock/fake/placeholder/TODO found", "high", "Replace with live endpoint or delete"))
    return issues

def files_exist(paths):
    missing = []
    for rel in paths:
        if not (ROOT / rel).exists():
            missing.append(rel)
    return missing

def files_absent(paths):
    present = []
    for rel in paths:
        if (ROOT / rel).exists():
            present.append(rel)
    return present

# --------- audit runner ---------
def run_audit(args):
    ts = nowstamp()
    outdir = ROOT / f"reports/audit/{ts}"
    issues = []
    report = {
        "ts": ts,
        "integration": {},
        "testing": {},
        "deployment": {},
        "monitoring": {},
        "no_mocks": None,
    }

    # 1) Integration: files present/absent
    missing = files_exist(REQUIRED_UI)
    if missing:
        for m in missing:
            issues.append((m, "required file missing", "high", "Commit patch pack; ensure path matches"))
    stale = files_absent(DELETED_FILES)
    if stale:
        for s in stale:
            issues.append((s, "legacy/mock file still present", "high", "Delete file"))
    report["integration"]["required_present"] = (len(missing) == 0)
    report["integration"]["legacy_removed"] = (len(stale) == 0)
    report["integration"]["missing_count"] = len(missing)
    report["integration"]["legacy_count"] = len(stale)

    # 2) Mock scan (apps/sophia-dashboard only)
    mock_issues = scan_mocks(ROOT / "apps" / "sophia-dashboard")
    for mi in mock_issues: issues.append(mi)
    report["no_mocks"] = (len(mock_issues) == 0)

    # 3) Typecheck (optional)
    tsc_ok, tsc_out = cmd_ok(["pnpm","tsc","--noEmit"], cwd=str(ROOT / "apps" / "sophia-dashboard"))
    report["testing"]["tsc_ok"] = tsc_ok
    if not tsc_ok:
        issues.append(("apps/sophia-dashboard", "TypeScript compile failed", "high", "Fix imports/types; run pnpm tsc --noEmit"))

    # 4) Unit tests (optional)
    if args.run_tests:
        test_ok, test_out = cmd_ok(["pnpm","test","--","-u"], cwd=str(ROOT / "apps" / "sophia-dashboard"))
        report["testing"]["unit_ok"] = test_ok
        if not test_ok:
            issues.append(("apps/sophia-dashboard", "Unit tests failed", "high", "Fix failing tests"))
    else:
        report["testing"]["unit_ok"] = "skipped"

    # 5) Dashboard base URL & probes
    base_url = args.base_url.rstrip("/") if args.base_url else ""
    # 5a) /api/health (dashboard proxy)
    if base_url:
        code, body = http_get(urljoin(base_url + "/", "api/health"), timeout=6)
        report["monitoring"]["api_health_ok"] = (code == 200)
        if code != 200:
            issues.append(("apps/sophia-dashboard/api/health", f"GET failed: {code} {body}", "medium", "Ensure HEALTH_TARGETS and services are reachable"))
        # 5b) /api/metrics?query=up
        q = urlencode({"query":"up","range":"30m","step":"30s"})
        code_m, body_m = http_get(urljoin(base_url + "/", f"api/metrics?{q}"), timeout=8)
        report["monitoring"]["metrics_proxy_ok"] = (code_m == 200)
        if code_m != 200:
            issues.append(("apps/sophia-dashboard/api/metrics", f"GET failed: {code_m} {body_m}", "low", "Set PROM_URL or ensure Prometheus reachable"))

        # 5c) /api/chat smoke – research + health
        for prompt in ["research quantum computing", "status health"]:
            code_c, body_c = http_post_json(urljoin(base_url + "/", "api/chat"),
                                            {"messages":[{"role":"user","content":prompt}]}, timeout=10)
            ok = (code_c == 200 and isinstance(body_c, (bytes, bytearray)))
            try:
                parsed = json.loads(body_c if isinstance(body_c, (bytes, bytearray)) else "{}")
                ok = ok and "sections" in parsed
            except Exception:
                ok = False
            report["integration"][f"chat_probe_{prompt.split()[0]}"] = bool(ok)
            if not ok:
                issues.append(("apps/sophia-dashboard/api/chat", f"POST failed for '{prompt}'", "medium", "Fix orchestrator / MCP routes; ensure services up"))
    else:
        report["monitoring"]["api_health_ok"] = "skipped"
        report["monitoring"]["metrics_proxy_ok"] = "skipped"
        report["integration"]["chat_probe_research"] = "skipped"

    # 6) Swarm service & WS (optional)
    swarm_http = args.swarm_http.rstrip("/") if args.swarm_http else ""
    swarm_ws = args.swarm_ws.rstrip("/") if args.swarm_ws else ""
    ws_ok = None
    if swarm_http:
        # create swarm
        payload = {"swarm_type":"analysis","task":"integration-audit swarm creation","context":{"source":"repo_audit"}}
        code_s, body_s = http_post_json(swarm_http + "/swarms/create", payload, timeout=10)
        created = False
        swarm_id = None
        if code_s == 200:
            try:
                j = json.loads(body_s)
                swarm_id = j.get("swarm_id")
                created = bool(swarm_id)
            except Exception:
                pass
        report["deployment"]["swarm_create_ok"] = created
        if not created:
            issues.append(("services/swarm", f"create failed: {code_s} {body_s}", "medium", "Ensure /swarms/create reachable"))

        # WS check if created and ws provided
        if created and swarm_ws:
            try:
                import asyncio, websockets  # optional dep
                async def ws_probe():
                    uri = f"{swarm_ws}/ws/swarm/{swarm_id}"
                    async with websockets.connect(uri, ping_timeout=5, close_timeout=5) as ws:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=8)
                            return True, msg
                        except Exception:
                            return False, None
                ok, msg = asyncio.get_event_loop().run_until_complete(ws_probe())
                ws_ok = ok
                if not ok:
                    issues.append(("services/swarm/ws", f"no message received for swarm {swarm_id}", "low", "Verify WS hub fanout"))
            except Exception as e:
                ws_ok = False
                issues.append(("services/swarm/ws", f"ws probe failed: {e}", "low", "pip install websockets; ensure WS path correct"))
        report["deployment"]["swarm_ws_ok"] = ws_ok if ws_ok is not None else "skipped"
    else:
        report["deployment"]["swarm_create_ok"] = "skipped"
        report["deployment"]["swarm_ws_ok"] = "skipped"

    # 7) Prometheus direct (optional)
    if args.prom_url:
        code_p, body_p = http_get(args.prom_url.rstrip("/") + "/api/v1/query?query=up", timeout=8)
        report["monitoring"]["prom_ok"] = (code_p == 200)
        if code_p != 200:
            issues.append(("prometheus", f"query up failed: {code_p} {body_p}", "low", "Check PROM_URL and network"))
    else:
        report["monitoring"]["prom_ok"] = "skipped"

    # 8) Grafana (optional presence check)
    report["monitoring"]["grafana_set"] = bool(args.grafana_url)

    # 9) Portkey – env presence sanity (no secrets content parsed)
    vk_envs = [k for k in os.environ.keys() if k.startswith("PORTKEY_VK_")]
    report["integration"]["portkey_virtual_keys_present"] = (len(vk_envs) > 0)

    # 10) write outputs
    out_json = outdir / "audit_report.json"
    out_csv  = outdir / "issues.csv"
    out_md   = outdir / "short_notes.md"

    write_json(out_json, report)
    write_csv(out_csv, issues, header=["path","error","severity","fix"])

    # short notes (≤30 lines)
    notes = [
        "# Sophia Supreme – Integration Audit (summary)",
        f"- timestamp: {ts}",
        f"- required UI present: {report['integration']['required_present']}",
        f"- legacy removed: {report['integration']['legacy_removed']}",
        f"- mocks remaining: {not report['no_mocks']}",
        f"- tsc_ok: {report['testing']['tsc_ok']}",
        f"- unit_ok: {report['testing']['unit_ok']}",
        f"- chat_probe_research: {report['integration'].get('chat_probe_research')}",
        f"- api_health_ok: {report['monitoring']['api_health_ok']}",
        f"- metrics_proxy_ok: {report['monitoring']['metrics_proxy_ok']}",
        f"- swarm_create_ok: {report['deployment']['swarm_create_ok']}",
        f"- swarm_ws_ok: {report['deployment']['swarm_ws_ok']}",
        f"- prom_ok: {report['monitoring']['prom_ok']}",
        f"- grafana_set: {report['monitoring']['grafana_set']}",
        f"- portkey_virtual_keys_present: {report['integration']['portkey_virtual_keys_present']}",
        f"- total_issues: {len(issues)}",
        "",
        "## Next Steps",
        "- Fix any missing files or mock references",
        "- Ensure services in HEALTH_TARGETS are reachable",
        "- Verify WS hub forwards swarm messages",
        "- Optional: run E2E and raise PR"
    ]
    write_short_md(out_md, notes)

    # console summary
    print(f"\n✅ Audit written to: {outdir}")
    print(f" - {out_json.name}")
    print(f" - {out_csv.name} (issues: {len(issues)})")
    print(f" - {out_md.name}")
    if issues:
        print("\nIssues (top 10):")
        for r in issues[:10]:
            print(" •", " | ".join(r))

def main():
    ap = argparse.ArgumentParser(description="Sophia Supreme Repo Auditor")
    ap.add_argument("--base-url", default=os.getenv("DASH_BASE_URL", "http://localhost:3000"),
                    help="Dashboard base URL (for /api/* probes)")
    ap.add_argument("--swarm-http", default=os.getenv("SWARM_HTTP_BASE", "http://localhost:8100"),
                    help="Swarm HTTP base (for /swarms/*)")
    ap.add_argument("--swarm-ws", default=os.getenv("SWARM_WS_BASE", "ws://localhost:8100"),
                    help="Swarm WS base (for /ws/swarm/{id})")
    ap.add_argument("--prom-url", default=os.getenv("PROM_URL", ""),
                    help="Prometheus base URL (optional; direct query)")
    ap.add_argument("--grafana-url", default=os.getenv("GRAFANA_URL", ""),
                    help="Grafana URL for embed (presence check only)")
    ap.add_argument("--run-tests", action="store_true", help="Run unit tests (pnpm test) and tsc check")
    args = ap.parse_args()
    run_audit(args)

if __name__ == "__main__":
    main()
