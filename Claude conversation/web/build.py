"""Assemble daemon_city.html from template.html + data, encode the models, and write headless test pages."""
import base64
import io
import json
import re
import sys

PLAN = "F:/Weimar universit\u00e4t/1/Introduction Project/Daemon Project/Second Version/Claude conversation/daemon_city_people.json"
t = io.open("template.html", encoding="utf-8").read()
t = t.replace("__LABELS__", json.dumps(json.load(io.open("labels.json", encoding="utf-8")), ensure_ascii=False))
t = t.replace("__DESC__", json.dumps(json.load(io.open("descriptions.json", encoding="utf-8")), ensure_ascii=False))
t = t.replace("__PLAN__", json.dumps(json.load(io.open(PLAN, encoding="utf-8")), ensure_ascii=False, separators=(",", ":")))
io.open("daemon_city.html", "w", encoding="utf-8").write(t)

# the daemons' film: the drawing and music code of the Safar Bekheyr animation, drawing into an offscreen canvas
SAFAR = "F:/Weimar universit\u00e4t/1/Introduction Project/Sentient Thing/safar-bekheyr.html"
s = io.open(SAFAR, encoding="utf-8").read()
body = s.split("<script>", 1)[1].split("// ---------- playback & recording")[0]
body = body.replace("const cv = document.getElementById('c');", "const cv = document.createElement('canvas'); cv.width = 1280; cv.height = 720;")
assert "getElementById" not in body
io.open("safar.js", "w", encoding="utf-8").write("// Safar Bekheyr, extracted from safar-bekheyr.html by build.py\n(function () {\n"
                                                 + body + "\nwindow.SAFAR = { cv, draw, DUR, makeMusic };\n})();\n")
for name in ("daemon_city", "daemon_houses"):
    open(name + "_glb.txt", "w").write(base64.b64encode(open(name + ".glb", "rb").read()).decode())
io.open("check.mjs", "w", encoding="utf-8").write(re.search(r'<script type="module">(.*)</script>', t, re.S).group(1))

# test pages: same page, opened at a given chapter and story time (the city itself still loads)
for ch in sys.argv[1:]:
    tt = '<meta charset="utf-8">' + t
    tt = tt.replace("  startStory(0);\n}", "  startStory(%s);\n}" % ch)
    tt = tt.replace("flyTo(frame(tgt, Math.max(42, top * 2.3), 30, 205), tgt, 1800);",
                    "camera.position.copy(frame(tgt, Math.max(42, top * 2.3), 30, 205)); controls.target.copy(tgt);")
    io.open("test_ch%s.html" % ch, "w", encoding="utf-8").write(tt)
print("built", len(t))

# GitHub Pages copy: <repo>/docs, a standalone page that loads the .glb files directly
import os
import shutil

DOCS = os.path.join("..", "..", "docs")
os.makedirs(os.path.join(DOCS, "draco"), exist_ok=True)
p = t
old = 'Promise.all([fetchB64("daemon_city_glb.txt", prog), fetchB64("daemon_houses_glb.txt", prog)])'
assert p.count(old) == 1
p = p.replace(old, 'Promise.all([fetchBin("daemon_city.glb", prog), fetchBin("daemon_houses.glb", prog)])')
old = "async function fetchB64(url, prog) {"
assert p.count(old) == 1
p = p.replace(old, """async function fetchBin(url, prog) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(url + ": HTTP " + res.status);
  const reader = res.body.getReader(), chunks = [];
  for (;;) { const { done, value } = await reader.read(); if (done) break; chunks.push(value); prog(value.length); }
  return await new Blob(chunks).arrayBuffer();
}
""" + old)
glb_total = sum(os.path.getsize(n + ".glb") for n in ("daemon_city", "daemon_houses"))
old = "const total = 12.25e6;"
assert p.count(old) == 1
p = p.replace(old, "const total = %d;" % glb_total)
p = p.replace("Loading the city (12 MB)", "Loading the city (%d MB)" % round(glb_total / 1e6))
p = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
     '<meta name="viewport" content="width=device-width, initial-scale=1">\n' + p + "\n</html>\n")
io.open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8").write(p)
for f in ("daemon_city.glb", "daemon_houses.glb", "safar.js", "draco/draco_decoder.js"):
    shutil.copyfile(f, os.path.join(DOCS, f))
open(os.path.join(DOCS, ".nojekyll"), "w").close()
print("pages copy written to", os.path.abspath(DOCS))
