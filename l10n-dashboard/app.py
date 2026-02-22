#!/usr/bin/env python3
"""L10n Suite Dashboard — local webapp for tracking apps, versions, and translations."""

import json
import os
import subprocess
import time
import urllib.request
import urllib.parse
import base64
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, render_template_string, redirect

app = Flask(__name__)
CACHE_FILE = Path(__file__).parent / "cache.json"
CACHE_TTL = 3600

TX_TOKEN = None
TX_ORG = "danielnylander"

# Language flag mapping
LANG_FLAGS = {
    "sv": "🇸🇪", "de": "🇩🇪", "fr": "🇫🇷", "es": "🇪🇸", "it": "🇮🇹",
    "pt_BR": "🇧🇷", "ja": "🇯🇵", "zh_CN": "🇨🇳", "ko": "🇰🇷", "nl": "🇳🇱",
    "da": "🇩🇰", "fi": "🇫🇮", "nb": "🇳🇴", "no": "🇳🇴", "pl": "🇵🇱",
    "ru": "🇷🇺", "uk": "🇺🇦", "cs": "🇨🇿", "hu": "🇭🇺", "ro": "🇷🇴",
    "tr": "🇹🇷", "ar": "🇸🇦", "he": "🇮🇱", "th": "🇹🇭", "vi": "🇻🇳",
    "id": "🇮🇩", "ms": "🇲🇾", "el": "🇬🇷", "bg": "🇧🇬", "hr": "🇭🇷",
    "sk": "🇸🇰", "sl": "🇸🇮", "et": "🇪🇪", "lv": "🇱🇻", "lt": "🇱🇹",
    "ca": "🏴", "eu": "🏴", "gl": "🏴",
}

APPS = [
    ("bildschema", "bildschema", "GUI/PO"), ("bildordbok", "bildordbok", "GUI/PO"),
    ("bildstod", "bildstod", "GUI/PO"), ("cert-watch", "cert-watch", "GUI/PO"),
    ("cldr-viewer", "cldr-viewer", "GUI/PO"), ("commonvoice-status", "commonvoice-status", "GUI/PO"),
    ("cve-monitor", "cve-monitor", "GUI/PO"), ("ddtp-translate", "ddtp-translate", "GUI/PO"),
    ("desktop-editor", "desktop-editor", "GUI/PO"), ("elementary-l10n", "elementary-l10n", "GUI/PO"),
    ("fedora-l10n", "fedora-l10n", "GUI/PO"), ("firewall-manager", "firewall-manager", "GUI/PO"),
    ("font-preview", "font-preview", "GUI/PO"), ("github-l10n", "github-l10n", "GUI/PO"),
    ("ha-l10n", "ha-l10n", "GUI/PO"), ("l10n-glossary", "l10n-glossary", "GUI/PO"),
    ("l10n-preview", "l10n-preview", "GUI/PO"), ("langpack-inspector", "langpack-inspector", "GUI/PO"),
    ("libretranslate-gui", "libretranslate-gui", "GUI/PO"), ("locale-tester", "locale-tester", "GUI/PO"),
    ("log-viewer", "log-viewer", "GUI/PO"), ("mqtt-dashboard", "mqtt-dashboard", "GUI/PO"),
    ("mqtt-inspector", "mqtt-inspector", "GUI/PO"), ("obd2-viewer", "obd2-viewer", "GUI/PO"),
    ("ordbyggaren", "ordbyggaren", "GUI/PO"), ("packetlens", "pcap-viewer", "GUI/PO"),
    ("pecsbrada", "pecsbrada", "GUI/PO"), ("process-explorer", "process-explorer", "GUI/PO"),
    ("regex-tester", "regex-tester", "GUI/PO"), ("rutinkompis", "rutinkompis", "GUI/PO"),
    ("snap-l10n", "snap-l10n", "GUI/PO"), ("tidskollen", "tidskollen", "GUI/PO"),
    ("tm-manager", "tm-manager", "GUI/PO"), ("tts-tester", "tts-tester", "GUI/PO"),
    ("ubuntu-l10n", "ubuntu-l10n", "GUI/PO"), ("vsdview", "vsdview", "GUI/PO"),
    ("wifi-analyzer", "wifi-analyzer", "GUI/PO"), ("zigbee-manager", "zigbee-manager", "GUI/PO"),
    ("fokuskompis", "fokuskompis", "GUI/PO"), ("lugnarummet", "lugnarummet", "GUI/PO"),
    ("gnome-l10n", "gnome-l10n", "GUI/PO"), ("scummvm-gtk", "scummvm-gtk", "GUI/PO"),
    ("kanslokartan", "kanslokartan", "GUI/PO"), ("minnet", "minnet", "GUI/PO"),
    ("beloningskartan", "beloningskartan", "GUI/PO"), ("socialaberattelser", "socialaberattelser", "GUI/PO"),
    ("ljudladan", "ljudladan", "GUI/PO"), ("mittschema", "mittschema", "GUI/PO"),
    ("linguaedit", "linguaedit", "GUI/TS"), ("kodi-subtitle-translator", "kodi-subtitle-translator", "GUI/TS"),
    ("l10n-conv", "l10n-conv", "CLI/PO"), ("l10n-lint", "l10n-lint", "CLI/PO"),
    ("po-diff", "po-diff", "CLI/PO"), ("po-translate", "po-translate", "CLI/PO"),
    ("svlang", "svlang", "CLI/PO"), ("tp-lint", "tp-lint", "CLI/PO"),
    ("makebread", "makebread", "GUI/PO"),
    ("tp-status", "tp-status", "GUI/PO"),
]

# Package name overrides for deb/rpm
PKG_NAME_MAP = {}
# Transifex project name overrides (when TX slug differs from app_name)
TX_NAME_MAP = {"po-translate": "po-translate-ai"}
# GitHub repo name overrides (when GH repo differs from app_name)
REPO_NAME_MAP = {"packetlens": "pcap-viewer"}
# RPM-only (no deb)
RPM_ONLY = {"fedora-l10n"}
# No RPM package (Debian/Ubuntu-specific or no RPM build)
NO_RPM = {"ddtp-translate", "ubuntu-l10n", "elementary-l10n", "langpack-inspector"}


def get_tx_token():
    global TX_TOKEN
    if TX_TOKEN:
        return TX_TOKEN
    rc = Path.home() / ".transifexrc"
    if rc.exists():
        in_www_section = False
        for line in rc.read_text().splitlines():
            if "www.transifex.com" in line:
                in_www_section = True
            elif line.startswith("["):
                in_www_section = False
            elif in_www_section and line.strip().startswith("token"):
                t = line.split("=", 1)[1].strip()
                if len(t) > 5:  # skip bogus short tokens
                    TX_TOKEN = t
                    return TX_TOKEN
    return None


def tx_api(path):
    token = get_tx_token()
    if not token:
        return None
    url = f"https://rest.api.transifex.com/{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except:
        return None


def fetch_tx_stats(app_name):
    tx_name = TX_NAME_MAP.get(app_name, app_name)
    data = tx_api(f"resource_language_stats?filter%5Bproject%5D=o%3A{TX_ORG}%3Ap%3A{tx_name}")
    if not data:
        return {"total": 0, "languages": {}}
    # Filter to main resource only (exclude man-page resources like *-man)
    # Main resource slugs: <app>-pot, pot, <app>
    main_slugs = {f"{app_name}-pot", "pot", app_name, f"{app_name.replace('-', '_')}-pot"}
    result = {"total": 0, "languages": {}}
    for item in data.get("data", []):
        # Extract resource slug from ID like "o:...:p:...:r:SLUG:l:LANG"
        parts = item["id"].split(":")
        # Find resource slug (between :r: and :l:)
        try:
            r_idx = parts.index("r")
            l_idx = parts.index("l")
            resource_slug = ":".join(parts[r_idx+1:l_idx])
        except (ValueError, IndexError):
            resource_slug = ""
        # Skip man-page resources — only use the main app pot
        if resource_slug.endswith("-man"):
            continue
        # For apps with multiple pot resources (e.g. l10n-lint + l10n-lint-gtk),
        # only use the primary one matching <app>-pot
        primary_slug = f"{app_name}-pot"
        if resource_slug and resource_slug != primary_slug and resource_slug not in {"pot", app_name}:
            continue
        lang = item["id"].split(":l:")[-1]
        attrs = item["attributes"]
        if attrs["total_strings"] > result["total"]:
            result["total"] = attrs["total_strings"]
        if attrs["translated_strings"] > 0 and lang != "en":
            result["languages"][lang] = {
                "translated": attrs["translated_strings"],
                "total": attrs["total_strings"],
                "pct": round(100 * attrs["translated_strings"] / attrs["total_strings"]) if attrs["total_strings"] else 0,
            }
    return result


_gh_version_cache = {}
_gh_cache_loaded_at = 0  # timestamp of last load
_GH_CACHE_TTL = 300  # reload from disk every 5 minutes
REPO_VERSIONS_CACHE = Path.home() / ".openclaw/workspace/local-services/cache/repo_versions.json"

def _load_gh_versions():
    """Load GH versions from local-services cache (refreshed every 2h by cron)."""
    global _gh_version_cache, _gh_cache_loaded_at
    import time
    now = time.time()
    if _gh_cache_loaded_at and (now - _gh_cache_loaded_at) < _GH_CACHE_TTL:
        return
    _gh_cache_loaded_at = now
    try:
        if REPO_VERSIONS_CACHE.exists():
            data = json.loads(REPO_VERSIONS_CACHE.read_text())
            repos = data.get("repos", data)  # handle both formats
            for name, info in repos.items():
                if isinstance(info, str):
                    # Simple format: {"app": "1.0.0"}
                    tag = info
                elif isinstance(info, dict):
                    tag = info.get("latest_tag", "")
                else:
                    continue
                if tag and not tag.startswith("{"):
                    _gh_version_cache[name] = tag.lstrip("v")
            print(f"Loaded {len(_gh_version_cache)} GH versions from cache", flush=True)
    except Exception as e:
        print(f"Failed to load GH version cache: {e}", flush=True)

def fetch_github_version(repo):
    _load_gh_versions()
    return _gh_version_cache.get(repo, "?")


def fetch_deb_version(pkg_name):
    pf = Path.home() / "debian-repo" / "Packages"
    if not pf.exists():
        return "-"
    cur_pkg = None
    for line in pf.read_text().splitlines():
        if line.startswith("Package:"):
            cur_pkg = line.split(":", 1)[1].strip()
        elif line.startswith("Version:") and cur_pkg == pkg_name:
            return line.split(":", 1)[1].strip()
    return "-"


def fetch_rpm_versions():
    """Parse rpm-repo repodata for all package versions."""
    versions = {}
    try:
        rpm_repo = Path.home() / "rpm-repo"
        if not rpm_repo.exists():
            return versions
        repodata = rpm_repo / "packages" / "repodata"
        if not repodata.exists():
            repodata = rpm_repo / "repodata"
        if not repodata.exists():
            return versions

        import xml.etree.ElementTree as ET
        rpm_primary = None

        # Try .zst first, then .gz
        for f in repodata.glob("*primary.xml.zst"):
            rpm_primary = f
            break
        if not rpm_primary:
            for f in repodata.glob("*primary.xml.gz"):
                rpm_primary = f
                break
        if not rpm_primary:
            return versions

        if str(rpm_primary).endswith(".zst"):
            import zstandard
            with open(rpm_primary, "rb") as fh:
                dctx = zstandard.ZstdDecompressor()
                xml_data = dctx.stream_reader(fh).read()
            tree = ET.ElementTree(ET.fromstring(xml_data))
        else:
            import gzip
            with gzip.open(rpm_primary) as gz:
                tree = ET.parse(gz)

        ns = {"c": "http://linux.duke.edu/metadata/common", "rpm": "http://linux.duke.edu/metadata/rpm"}
        for pkg in tree.findall(".//c:package", ns):
            name_el = pkg.find("c:name", ns)
            ver_el = pkg.find("c:version", ns)
            if name_el is not None and ver_el is not None:
                name = name_el.text
                ver = ver_el.get("ver", "?")
                # Keep the latest version if duplicates exist
                if name not in versions or ver > versions[name]:
                    versions[name] = ver
    except Exception as e:
        print(f"RPM parse error: {e}")
    return versions


def _count_msgids_in_content(content):
    """Count msgid entries in PO/POT content (excluding header empty msgid).

    Handles multiline: msgid ""\n"actual string" counts as non-empty.
    Only the very first msgid "" (PO header) is excluded.
    """
    lines = content.splitlines()
    count = 0
    i = 0
    first = True
    while i < len(lines):
        if lines[i].startswith("msgid "):
            val = lines[i][6:].strip().strip('"')
            if not val:
                # Check if next line continues the string
                j = i + 1
                while j < len(lines) and lines[j].startswith('"'):
                    val += lines[j].strip().strip('"')
                    j += 1
            if first and not val:
                first = False  # skip PO header
            else:
                count += 1
            i += 1
        else:
            i += 1
    return count


def _fetch_gh_file(repo, path):
    """Fetch a file from GitHub and return decoded content, or None."""
    try:
        r = subprocess.run(["gh", "api", f"repos/yeager/{repo}/contents/{path}", "--jq", ".content"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return base64.b64decode(r.stdout.strip()).decode()
    except:
        pass
    return None


def _count_ts_strings(content):
    """Count <source> elements in a Qt .ts XML file."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(content)
        return len(root.findall(".//message/source"))
    except:
        return 0


def _count_kodi_strings(content):
    """Count msgid entries in Kodi strings.po format."""
    return max(0, content.count("msgid ") - 1)


def fetch_github_pot_strings(repo):
    # 1. Standard: po/<name>.pot — prefer <repo>.pot over other .pot files
    try:
        r = subprocess.run(["gh", "api", f"repos/yeager/{repo}/contents/po", "--jq", ".[].name"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            pot_files = [n for n in r.stdout.strip().splitlines() if n.endswith(".pot")]
            # Sort: exact match first (repo.pot), then others
            primary = f"{repo}.pot"
            pot_files.sort(key=lambda n: (0 if n == primary else 1, n))
            for name in pot_files:
                content = _fetch_gh_file(repo, f"po/{name}")
                if content:
                    count = _count_msgids_in_content(content)
                    if count > 0:
                        return count
    except:
        pass

    # 2. makebread-style: <repo>/resources/locale/<name>.pot
    for locale_path in [f"{repo}/resources/locale", "resources/locale"]:
        try:
            r = subprocess.run(["gh", "api", f"repos/yeager/{repo}/contents/{locale_path}", "--jq", ".[].name"],
                               capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                for name in r.stdout.strip().splitlines():
                    if name.endswith(".pot"):
                        content = _fetch_gh_file(repo, f"{locale_path}/{name}")
                        if content:
                            count = _count_msgids_in_content(content)
                            if count > 0:
                                return count
        except:
            pass

    # 3. Kodi-format: resources/language/resource.language.en_gb/strings.po
    content = _fetch_gh_file(repo, "resources/language/resource.language.en_gb/strings.po")
    if content:
        count = _count_kodi_strings(content)
        if count > 0:
            return count

    # 4. Qt .ts format: src/*/translations/*_template.ts or src/*/translations/<name>.ts
    try:
        r = subprocess.run(["gh", "api", f"repos/yeager/{repo}/git/trees/main?recursive=1", "--jq",
                            '.tree[].path | select(test("src/.*/translations/.*\\\\.ts$"))'],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            ts_files = r.stdout.strip().splitlines()
            # Prefer template file, then base (no language suffix)
            for ts in ts_files:
                basename = ts.rsplit("/", 1)[-1]
                if "_template" in basename or "_" not in basename.replace(".ts", ""):
                    content = _fetch_gh_file(repo, ts)
                    if content:
                        count = _count_ts_strings(content)
                        if count > 0:
                            return count
    except:
        pass

    return 0


def fetch_last_push(repo):
    """Get the last push timestamp for a repo."""
    try:
        r = subprocess.run(["gh", "api", f"repos/yeager/{repo}", "--jq", ".pushed_at"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except:
        pass
    return None


def refresh_cache():
    print("Refreshing cache...", flush=True)
    data = {"updated": datetime.now(timezone.utc).isoformat(), "apps": []}

    # Clone rpm-repo if not present
    rpm_repo = Path.home() / "rpm-repo"
    if not rpm_repo.exists():
        subprocess.run(["git", "clone", "https://github.com/yeager/rpm-repo.git", str(rpm_repo)],
                       capture_output=True, timeout=30)
    else:
        subprocess.run(["git", "-C", str(rpm_repo), "pull"], capture_output=True, timeout=15)

    rpm_versions = fetch_rpm_versions()

    for app_name, repo, app_type in APPS:
        print(f"  {app_name}...", flush=True)
        tx = fetch_tx_stats(app_name)
        pkg = PKG_NAME_MAP.get(app_name, app_name)
        deb_ver = "-" if app_name in RPM_ONLY else fetch_deb_version(pkg)
        rpm_ver = "-" if app_name in NO_RPM else rpm_versions.get(pkg, rpm_versions.get(app_name, "-"))

        data["apps"].append({
            "name": app_name,
            "repo": repo,
            "type": app_type,
            "github_version": fetch_github_version(repo),
            "deb_version": deb_ver,
            "rpm_version": rpm_ver,
            "tx_strings": tx.get("total", 0),
            "github_strings": fetch_github_pot_strings(repo),
            "languages": tx.get("languages", {}),
            "pushed_at": fetch_last_push(repo),
        })

    CACHE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return data


def load_data():
    if CACHE_FILE.exists():
        if time.time() - CACHE_FILE.stat().st_mtime < CACHE_TTL:
            return json.loads(CACHE_FILE.read_text())
    return refresh_cache()


TEMPLATE = """<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="300">
<title>L10n Suite Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0f0f1a; color: #ccc; padding: 12px 16px; font-size: 13px; }
  h1 { color: #00d4ff; font-size: 20px; display: inline; }
  .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
  .subtitle { color: #666; font-size: 11px; }
  .stats { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
  .stat { background: #151528; border-radius: 8px; padding: 8px 16px; border: 1px solid #1a1a3a; text-align: center; }
  .stat .v { font-size: 22px; font-weight: bold; color: #00d4ff; }
  .stat .l { font-size: 10px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
  table { width: 100%; border-collapse: collapse; background: #151528; border-radius: 8px; overflow: hidden; font-size: 12px; }
  th { background: #0f1e3d; color: #00d4ff; padding: 6px 8px; text-align: left;
       font-size: 11px; text-transform: uppercase; letter-spacing: 0.3px;
       cursor: pointer; user-select: none; white-space: nowrap; }
  th:hover { background: #152850; }
  td { padding: 4px 8px; border-bottom: 1px solid #1a1a2e; white-space: nowrap; }
  tr:hover td { background: #1a2240; }
  .g { color: #4ade80; } .r { color: #f87171; } .y { color: #fbbf24; } .d { color: #555; }
  a { color: #60a5fa; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .flag { font-size: 14px; cursor: default; }
  .flag.partial { opacity: 0.5; }
  .btn { background: #0f1e3d; color: #00d4ff; border: 1px solid #00d4ff;
         padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; text-decoration: none; }
  .btn:hover { background: #152850; }
  .ver-match { color: #4ade80; }
  .ver-mismatch { color: #f87171; }
  .ver-none { color: #555; }
  .type { font-size: 10px; padding: 1px 6px; border-radius: 3px; }
  .type-gui { background: #0a2e1a; color: #4ade80; }
  .type-cli { background: #2e2a0a; color: #fbbf24; }
</style>
</head>
<body>
<div class="header">
  <div><h1>🌍 L10n Suite</h1> <span class="subtitle">{{ updated }}</span></div>
  <a href="/refresh" class="btn">🔄 Uppdatera</a>
</div>

<div class="stats">
  <div class="stat"><div class="v">{{ total_apps }}</div><div class="l">Appar</div></div>
  <div class="stat"><div class="v">{{ gui_apps }}</div><div class="l">GUI</div></div>
  <div class="stat"><div class="v">{{ cli_apps }}</div><div class="l">CLI</div></div>
  <div class="stat"><div class="v">{{ total_tx_strings }}</div><div class="l">TX strängar</div></div>
  <div class="stat"><div class="v">{{ total_gh_strings }}</div><div class="l">GH strängar</div></div>
  <div class="stat"><div class="v">{{ lang_count }}</div><div class="l">Språk</div></div>
</div>

{% if recent_apps %}
<h2 style="color:#fbbf24;font-size:14px;margin:12px 0 6px;">🔥 Ändrade senaste 1h</h2>
<table id="r">
<thead>
<tr>
  <th onclick="S2(0)">App</th>
  <th onclick="S2(1)">Typ</th>
  <th onclick="S2(2)">GitHub</th>
  <th onclick="S2(3)">.deb</th>
  <th onclick="S2(4)">.rpm</th>
  <th onclick="S2(5)">TX</th>
  <th onclick="S2(6)">GH</th>
  <th onclick="S2(7)">Ändrad</th>
  <th>Språk</th>
</tr>
</thead>
<tbody>
{% for a in recent_apps %}
<tr>
  <td><a href="https://github.com/yeager/{{ a.repo }}" target="_blank">{{ a.name }}</a></td>
  <td><span class="type type-{{ a.type|lower }}">{{ a.type }}</span></td>
  <td>{{ a.github_version }}</td>
  <td class="{% if a.deb_version == a.github_version or a.deb_version == a.github_version ~ '-1' %}ver-match{% elif a.deb_version == '-' %}ver-none{% else %}ver-mismatch{% endif %}">{{ a.deb_version }}</td>
  <td class="{% if a.rpm_version == a.github_version or a.rpm_version == a.github_version ~ '-1' %}ver-match{% elif a.rpm_version == '-' %}ver-none{% else %}ver-mismatch{% endif %}">{{ a.rpm_version }}</td>
  <td>{{ a.tx_strings }}</td>
  <td class="{% if a.tx_strings == a.github_strings or (a.tx_strings > 0 and a.github_strings > 0 and (a.tx_strings - a.github_strings)|abs <= 1) %}g{% elif a.github_strings == 0 %}d{% else %}r{% endif %}">{{ a.github_strings }}{% if a.tx_strings == a.github_strings and a.tx_strings > 0 %} ✓{% elif a.github_strings > 0 and a.tx_strings != a.github_strings %} ✗{% endif %}</td>
  <td style="color:#fbbf24">{{ a.pushed_ago }}</td>
  <td>
    {% for lang, info in a.languages.items() %}
    <span class="flag {% if info.pct < 100 %}partial{% endif %}" title="{{ lang }}: {{ info.translated }}/{{ info.total }} ({{ info.pct }}%)">{{ flags.get(lang, lang) }}</span>
    {% endfor %}
    {% if not a.languages %}<span class="d">—</span>{% endif %}
  </td>
</tr>
{% endfor %}
</tbody>
</table>
{% endif %}

<h2 style="color:#00d4ff;font-size:14px;margin:16px 0 6px;">📦 Alla appar</h2>
<table id="t">
<thead>
<tr>
  <th onclick="S(0)">App</th>
  <th onclick="S(1)">Typ</th>
  <th onclick="S(2)">GitHub</th>
  <th onclick="S(3)">.deb</th>
  <th onclick="S(4)">.rpm</th>
  <th onclick="S(5)">TX</th>
  <th onclick="S(6)">GH</th>
  <th>Språk</th>
</tr>
</thead>
<tbody>
{% for a in apps %}
<tr>
  <td><a href="https://github.com/yeager/{{ a.repo }}" target="_blank">{{ a.name }}</a></td>
  <td><span class="type type-{{ a.type|lower }}">{{ a.type }}</span></td>
  <td>{{ a.github_version }}</td>
  <td class="{% if a.deb_version == a.github_version or a.deb_version == a.github_version ~ '-1' %}ver-match{% elif a.deb_version == '-' %}ver-none{% else %}ver-mismatch{% endif %}">{{ a.deb_version }}</td>
  <td class="{% if a.rpm_version == a.github_version or a.rpm_version == a.github_version ~ '-1' %}ver-match{% elif a.rpm_version == '-' %}ver-none{% else %}ver-mismatch{% endif %}">{{ a.rpm_version }}</td>
  <td>{{ a.tx_strings }}</td>
  <td class="{% if a.tx_strings == a.github_strings or (a.tx_strings > 0 and a.github_strings > 0 and (a.tx_strings - a.github_strings)|abs <= 1) %}g{% elif a.github_strings == 0 %}d{% else %}r{% endif %}">{{ a.github_strings }}{% if a.tx_strings == a.github_strings and a.tx_strings > 0 %} ✓{% elif a.github_strings > 0 and a.tx_strings != a.github_strings %} ✗{% endif %}</td>
  <td>
    {% for lang, info in a.languages.items() %}
    <span class="flag {% if info.pct < 100 %}partial{% endif %}" title="{{ lang }}: {{ info.translated }}/{{ info.total }} ({{ info.pct }}%)">{{ flags.get(lang, lang) }}</span>
    {% endfor %}
    {% if not a.languages %}<span class="d">—</span>{% endif %}
  </td>
</tr>
{% endfor %}
</tbody>
</table>

<script>
let D={},D2={};
function _sort(tid,st,c){const t=document.getElementById(tid),r=Array.from(t.tBodies[0].rows),d=st[c]=!st[c];
r.sort((a,b)=>{let x=a.cells[c].textContent.trim(),y=b.cells[c].textContent.trim(),
nx=parseFloat(x),ny=parseFloat(y);if(!isNaN(nx)&&!isNaN(ny))return d?nx-ny:ny-nx;
return d?x.localeCompare(y):y.localeCompare(x)});r.forEach(r=>t.tBodies[0].appendChild(r))}
function S(c){_sort("t",D,c)} function S2(c){_sort("r",D2,c)}
</script>
</body>
</html>"""


@app.route("/")
def index():
    data = load_data()
    apps = data.get("apps", [])
    all_langs = set()
    total_tx = 0
    total_gh = 0
    gui = sum(1 for a in apps if a["type"].startswith("GUI"))
    cli = sum(1 for a in apps if a["type"].startswith("CLI"))
    for a in apps:
        total_tx += a.get("tx_strings", 0) or 0
        total_gh += a.get("github_strings", 0) or 0
        for lang in a.get("languages", {}):
            all_langs.add(lang)
    # Split into recent (1h) and rest
    now = datetime.now(timezone.utc)
    recent_apps = []
    older_apps = []
    for a in apps:
        pushed = a.get("pushed_at")
        if pushed:
            try:
                pt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
                diff = now - pt
                if diff.total_seconds() < 3600:
                    hours = int(diff.total_seconds() / 3600)
                    mins = int((diff.total_seconds() % 3600) / 60)
                    a["pushed_ago"] = f"{hours}h {mins}m sedan" if hours > 0 else f"{mins}m sedan"
                    recent_apps.append(a)
                    continue
            except:
                pass
        older_apps.append(a)
    # Sort recent by most recently pushed first
    recent_apps.sort(key=lambda a: a.get("pushed_at", ""), reverse=True)

    return render_template_string(TEMPLATE, apps=older_apps, recent_apps=recent_apps,
        flags=LANG_FLAGS,
        updated=data.get("updated", "?")[:16].replace("T", " ") + " UTC",
        total_apps=len(apps), gui_apps=gui, cli_apps=cli,
        total_tx_strings=total_tx, total_gh_strings=total_gh,
        lang_count=len(all_langs))


@app.route("/refresh")
def refresh():
    refresh_cache()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5111, debug=False)
