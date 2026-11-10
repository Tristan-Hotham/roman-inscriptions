"""Step 7: index.html from code/page_template.html + page_essay.html, filled from data/results.json.
10.5281/zenodo.24114976, https://doi.org/10.5281/zenodo.24114976 and https://blog.tristanhotham.com/2026/10/31/roman-inscriptions/ are left for the publisher to fill."""
from common import *

R = jload(f"{DATA}/results.json")
S = jload(f"{DATA}/site.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("%%ESSAY%%", open(os.path.join(ROOT, "code", "page_essay.html"), encoding="utf-8").read())
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "2026a").replace("{{NBINS}}", str(len(S["bins"])))
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert t.rstrip().endswith("</html>") and 'site-nav.js" defer></script>\n</body>' in t
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
