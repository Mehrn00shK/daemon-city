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
