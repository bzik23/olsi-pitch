# -*- coding: utf-8 -*-
"""
Deploy theme files to the LIVE olsi.co.il (no SFTP available). Uses the proven
Code-Snippets-over-REST method: install code-snippets, run a one-shot guarded
snippet that reads/writes files under the active theme dir, then clean up.

Safety:
  - reads live files first so we can diff before overwriting (catch live-only drift)
  - every written file is backed up to <file>.olsibak on the server (rollback)
  - all PHP is linted locally (php -l) before this runs
  - a random per-run token guards the trigger; the snippet is deleted after

Usage (import): read_theme(), write_theme(local_paths), restore_theme(), cleanup().
"""
import json, base64, urllib.request, urllib.error, io, os, hashlib

SITE = "https://www.olsi.co.il"
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp_auth import USER, APPPW  # local-only, gitignored (see _wp/wp_auth.py)
_AUTH = "Basic " + base64.b64encode(("%s:%s" % (USER, APPPW)).encode()).decode()
DIST = os.path.join(os.path.dirname(__file__), "dist", "olsi-systems")

# deterministic-ish token (no Math.random in this env is irrelevant; python is fine)
TOKEN = hashlib.sha1(os.urandom(16)).hexdigest()[:16]

def _req(method, path, data=None, raw=False):
    url = path if path.startswith("http") else SITE + path
    body = None
    if data is not None:
        body = data if raw else json.dumps(data).encode("utf-8")
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header("Authorization", _AUTH)
    if data is not None and not raw:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r) as resp:
            txt = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        return {"_http_error": e.code, "_body": txt}
    try:
        return json.loads(txt)
    except Exception:
        return {"_text": txt}

# ---- plugin management -----------------------------------------------------------
def plugin_status(slug="code-snippets"):
    d = _req("GET", "/wp-json/wp/v2/plugins?_fields=plugin,status")
    for p in d if isinstance(d, list) else []:
        if p.get("plugin", "").startswith(slug + "/") or p.get("plugin", "") == slug:
            return p.get("status")
    return None

def ensure_code_snippets():
    st = plugin_status()
    if st == "active":
        return "already-active"
    if st == "inactive":
        _req("POST", "/wp-json/wp/v2/plugins/code-snippets/code-snippets", {"status": "active"})
        return "activated"
    r = _req("POST", "/wp-json/wp/v2/plugins", {"slug": "code-snippets", "status": "active"})
    return "installed" if not r.get("_http_error") else ("install-error: %s" % r)

def cleanup_plugin(remove=True):
    if not remove:
        return "kept"
    _req("POST", "/wp-json/wp/v2/plugins/code-snippets/code-snippets", {"status": "inactive"})
    r = _req("DELETE", "/wp-json/wp/v2/plugins/code-snippets/code-snippets")
    return "removed" if not r.get("_http_error") else ("delete-error: %s" % r)

# ---- snippet run -----------------------------------------------------------------
def _create_snippet(code, name="olsi-ops-temp"):
    r = _req("POST", "/wp-json/code-snippets/v1/snippets",
             {"name": name, "code": code, "scope": "global", "active": True})
    return r

def _delete_snippet(sid):
    _req("POST", "/wp-json/code-snippets/v1/snippets/%s" % sid, {"active": False})
    return _req("DELETE", "/wp-json/code-snippets/v1/snippets/%s" % sid)

def _trigger():
    return _req("GET", "/?olsi_op=%s" % TOKEN)

# ---- read live theme files -------------------------------------------------------
READ_RELS = ["header.php", "footer.php", "functions.php", "assets/olsi.css",
             "page.php", "front-page.php", "single.php", "index.php", "style.css"]

def read_theme():
    rels_php = "array(" + ",".join("'%s'" % r for r in READ_RELS) + ")"
    code = ("add_action('init', function(){\n"
            "  if ((isset($_GET['olsi_op'])?$_GET['olsi_op']:'') !== '%s') return;\n"
            "  $dir = get_template_directory();\n"
            "  $rels = %s;\n"
            "  $out = array('dir'=>$dir,'files'=>array());\n"
            "  foreach($rels as $r){ $p=$dir.'/'.$r; $out['files'][$r] = is_file($p)?base64_encode(file_get_contents($p)):null; }\n"
            "  file_put_contents(WP_CONTENT_DIR.'/uploads/_olsi_read_%s.json', json_encode($out));\n"
            "  header('Content-Type: text/plain'); echo 'OLSI_READ_OK'; exit;\n"
            "});") % (TOKEN, rels_php, TOKEN)
    sn = _create_snippet(code, "olsi-read")
    sid = sn.get("id")
    trig = _trigger()
    data = _req("GET", "/wp-content/uploads/_olsi_read_%s.json" % TOKEN)
    if sid:
        _delete_snippet(sid)
    files = {}
    if isinstance(data, dict) and "files" in data:
        for r, b in data["files"].items():
            files[r] = base64.b64decode(b).decode("utf-8", "replace") if b else None
        return {"dir": data.get("dir"), "files": files, "trigger": trig}
    return {"error": data, "snippet": sn, "trigger": trig}

# ---- write live theme files ------------------------------------------------------
def write_theme(rels):
    """rels: list of theme-relative paths to push from DIST (e.g. ['functions.php',...])."""
    entries = []
    for r in rels:
        with io.open(os.path.join(DIST, r), "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        entries.append("'%s'=>'%s'" % (r, b64))
    files_php = "array(" + ",".join(entries) + ")"
    code = ("add_action('init', function(){\n"
            "  if ((isset($_GET['olsi_op'])?$_GET['olsi_op']:'') !== '%s') return;\n"
            "  $dir = get_template_directory();\n"
            "  $files = %s;\n"
            "  $log = array();\n"
            "  foreach($files as $rel=>$b64){\n"
            "    $t = $dir.'/'.$rel;\n"
            "    if (is_file($t) && !is_file($t.'.olsibak')) @copy($t, $t.'.olsibak');\n"
            "    $log[$rel] = file_put_contents($t, base64_decode($b64));\n"
            "  }\n"
            "  file_put_contents(WP_CONTENT_DIR.'/uploads/_olsi_write_%s.json', json_encode($log));\n"
            "  header('Content-Type: text/plain'); echo 'OLSI_WRITE_OK'; exit;\n"
            "});") % (TOKEN, files_php, TOKEN)
    sn = _create_snippet(code, "olsi-write")
    sid = sn.get("id")
    trig = _trigger()
    log = _req("GET", "/wp-content/uploads/_olsi_write_%s.json" % TOKEN)
    if sid:
        _delete_snippet(sid)
    return {"log": log, "snippet_id": sid, "trigger": trig, "token": TOKEN}

def restore_theme(rels):
    """rollback: copy each <rel>.olsibak back over <rel>."""
    files_php = "array(" + ",".join("'%s'" % r for r in rels) + ")"
    code = ("add_action('init', function(){\n"
            "  if ((isset($_GET['olsi_op'])?$_GET['olsi_op']:'') !== '%s') return;\n"
            "  $dir = get_template_directory(); $rels = %s; $log=array();\n"
            "  foreach($rels as $rel){ $t=$dir.'/'.$rel; $b=$t.'.olsibak';\n"
            "    $log[$rel] = is_file($b)? copy($b,$t) : 'no-backup'; }\n"
            "  file_put_contents(WP_CONTENT_DIR.'/uploads/_olsi_restore_%s.json', json_encode($log));\n"
            "  header('Content-Type: text/plain'); echo 'OLSI_RESTORE_OK'; exit;\n"
            "});") % (TOKEN, files_php, TOKEN)
    sn = _create_snippet(code, "olsi-restore")
    sid = sn.get("id")
    _trigger()
    log = _req("GET", "/wp-content/uploads/_olsi_restore_%s.json" % TOKEN)
    if sid:
        _delete_snippet(sid)
    return log

def cleanup_server(rels):
    """delete <rel>.olsibak backups in the theme dir + our temp uploads logs."""
    files_php = "array(" + ",".join("'%s'" % r for r in rels) + ")"
    code = ("add_action('init', function(){\n"
            "  if ((isset($_GET['olsi_op'])?$_GET['olsi_op']:'') !== '%s') return;\n"
            "  $dir = get_template_directory(); $rels = %s; $log=array();\n"
            "  foreach($rels as $rel){ $b=$dir.'/'.$rel.'.olsibak'; $log[$rel.'.olsibak'] = is_file($b)? (unlink($b)?'del':'fail') : 'none'; }\n"
            "  foreach(glob(WP_CONTENT_DIR.'/uploads/_olsi_*.json') as $g){ $log[basename($g)] = unlink($g)?'del':'fail'; }\n"
            "  file_put_contents(WP_CONTENT_DIR.'/uploads/_olsi_cleanup.json', json_encode($log));\n"
            "  header('Content-Type: text/plain'); echo 'OLSI_CLEANUP_OK'; exit;\n"
            "});") % (TOKEN, files_php)
    sn = _create_snippet(code, "olsi-cleanup")
    sid = sn.get("id")
    _trigger()
    log = _req("GET", "/wp-content/uploads/_olsi_cleanup.json")
    # remove the cleanup log itself + the snippet
    code2 = ("add_action('init', function(){ if ((isset($_GET['olsi_op'])?$_GET['olsi_op']:'') !== '%s') return;"
             " @unlink(WP_CONTENT_DIR.'/uploads/_olsi_cleanup.json'); echo 'x'; exit; });") % TOKEN
    if sid:
        _delete_snippet(sid)
    sn2 = _create_snippet(code2, "olsi-cleanup2"); sid2 = sn2.get("id")
    _trigger()
    if sid2:
        _delete_snippet(sid2)
    return log

if __name__ == "__main__":
    import sys
    print("token:", TOKEN)
    print("code-snippets status:", plugin_status())
