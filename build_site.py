"""
build_site.py — generates index.html + containers/ for Finance agent data collection
Usage: python3 build_site.py
Reads stripped JSONs from STRIPPED_DIR, writes index.html + containers/*.txt to SITE_DIR

Architecture: each container is a separate .txt file fetched on demand on button click.
Page load is instant — no massive JS blob embedded in HTML.
"""

import json
import os

STRIPPED_DIR = "/home/darwin/PRES/data/finance/source_docs"
SITE_DIR     = "/home/darwin/PRES/data/finance"
CONT_DIR     = "/home/darwin/PRES/data/finance/containers"

SYSTEM_PROMPT = "You are Kenya's Cabinet Secretary for the National Treasury and Economic Planning. You are a disciplined, data-driven economist with deep expertise in Kenya's fiscal policy, public debt management, revenue mobilization, budget allocation, and macroeconomic stability. You speak with authority grounded in Kenya's own government data. You cite specific figures, budget lines, and economic indicators. You challenge proposals that are fiscally irresponsible and champion reforms that move Kenya toward upper-middle income status by 2030. You are not a politician — you are a technocrat who follows the numbers. When presented with quantitative scenarios, you close the accounting loop explicitly: Debt_t = Debt_{t-1} + Deficit_t and GDP_t = GDP_{t-1} x (1 + nominal growth rate). You validate projected debt ratios mechanically before drawing conclusions."

EXAMPLE = '{"messages":[{"role":"system","content":"' + SYSTEM_PROMPT.replace('"', '\\"') + '"},{"role":"user","content":"The 2024 BPS Third Basis Formula for horizontal allocation of county equitable share uses eight parameters: Population (18%), Health Index (17%), Agriculture Index (10%), Urban Index (5%), Poverty Index (14%), Land Area (8%), Roads Index (8%), and Basic Share (20%). Why is the Basic Share parameter in the formula, what problem does it solve, and what problem does it create? (Source: 2024 Budget Policy Statement, section 4.5)"},{"role":"assistant","content":"<think>\\nBasic Share: 20% of equitable share divided equally among 47 counties.\\n20% x Ksh 391.1 billion = Ksh 78.22 billion total\\nPer county: Ksh 78.22 billion / 47 = Ksh 1.664 billion\\nProblem solved: institutional viability floor for small counties.\\nProblem created: per capita inefficiency. Nairobi (4.4M) gets Ksh 378/capita vs Lamu (130K) gets Ksh 12,800/capita. That is 34x more per capita.\\n</think>\\n\\nThe Basic Share is a floor mechanism: 20 percent of the equitable share — Ksh 78.22 billion in FY 2024/25 — divided equally among all 47 counties, giving each Ksh 1.664 billion regardless of population or need. It solves institutional viability for small counties that could not sustain a governor office, county assembly, and basic service delivery on a purely population-weighted allocation. The problem it creates is severe per capita inefficiency: Nairobi at 4.4 million residents receives Ksh 378 per capita from the Basic Share while Lamu at 130,000 residents receives Ksh 12,800 per capita — 34 times more. The Urban Index at 5 percent is far too small to counterbalance this. The CRA next basis review should reduce the Basic Share to 10-12 percent and reallocate the released weight to Population and Poverty Indices."}]}'

INSTRUCTION = """=== TASK ===
You have been given a Kenyan government source document below. Generate exactly 15 high-quality JSONL training examples for an AI model that plays Kenya's Cabinet Secretary for the National Treasury.

=== STRICT RULES ===
1. Every question and every answer MUST be grounded ONLY in figures, tables, and facts found in the document below. Do not invent any numbers.
2. Each question must cite its exact source: document name and section or page number.
3. Each answer must open with a <think> block showing step-by-step arithmetic or logical reasoning before the final response.
4. Questions must be analytically demanding — contradictions, implications, fiscal sensitivities, tradeoffs, multi-step debt or GDP calculations. No simple lookups.
5. Answers must cite specific KSh figures, percentages, and policy references found in the document.
6. No two questions may cover the same section, table, or topic.
7. Voice: disciplined technocrat, not a politician. Numbers first.

=== OUTPUT FORMAT ===
Output exactly 15 JSONL lines. Each line must be a single valid JSON object:
{"messages":[{"role":"system","content":"SYSTEM_PROMPT"},{"role":"user","content":"QUESTION (Source: DOCUMENT_NAME, Section/Page X)"},{"role":"assistant","content":"<think>\\nSTEP BY STEP REASONING\\n</think>\\n\\nFULL ANSWER"}]}

Use this exact system prompt in every entry:
""" + SYSTEM_PROMPT + """

After all 15 lines, create a downloadable .jsonl file with all entries ready to send.

=== QUALITY EXAMPLE (match this standard) ===
""" + EXAMPLE


def build_container(slug: str, doc_json_str: str) -> str:
    return f"{INSTRUCTION}\n\n=== SOURCE DOCUMENT: {slug} ===\n{doc_json_str}"


def to_label(slug: str) -> str:
    return slug.replace("_", " ").title()


def main():
    if not os.path.exists(STRIPPED_DIR):
        print(f"ERROR: {STRIPPED_DIR} not found — run strip.py first.")
        return

    docs = sorted(f for f in os.listdir(STRIPPED_DIR) if f.endswith(".json"))
    if not docs:
        print("ERROR: no .json files found in source_docs/")
        return

    os.makedirs(CONT_DIR, exist_ok=True)
    os.makedirs(SITE_DIR, exist_ok=True)

    meta = []
    for filename in docs:
        with open(os.path.join(STRIPPED_DIR, filename), encoding="utf-8") as f:
            raw = f.read()
        doc  = json.loads(raw)
        slug = doc.get("doc_slug", filename.replace(".json", ""))
        src  = doc.get("source_file", slug)
        container = build_container(slug, raw)

        with open(os.path.join(CONT_DIR, slug + ".txt"), "w", encoding="utf-8") as f:
            f.write(container)

        size_kb = round(len(container) / 1024, 1)
        meta.append({"slug": slug, "label": to_label(slug), "source": src, "size_kb": size_kb})
        print(f"  {slug:<55}  {size_kb:>7.1f} KB")

    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_html(meta))

    print(f"\n  {len(meta)} containers -> {CONT_DIR}")
    print(f"  Site -> {SITE_DIR}/index.html")
    print(f"  Target training pairs: {len(meta) * 15}")
    print(f"\n  Serve the entire finance/ folder — index.html needs containers/ next to it.")


def render_html(meta: list) -> str:
    cards = ""
    for i, m in enumerate(meta):
        cards += f"""
      <div class="card">
        <div class="card-num">#{i+1:02d}</div>
        <div class="card-title">{m['label']}</div>
        <div class="card-source">{m['source']}</div>
        <div class="card-footer">
          <span class="size">{m['size_kb']} KB</span>
          <button class="copy-btn" data-slug="{m['slug']}" data-idx="{i}">Copy prompt</button>
        </div>
        <div class="status" id="s{i}"></div>
      </div>"""

    slugs_js = json.dumps([m["slug"] for m in meta])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PRES · Finance Training Data</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#F5F2ED;
  --surface:#FFFFFF;
  --border:#D8D3CB;
  --text:#1A1814;
  --muted:#6B6560;
  --dim:#9B9590;
  --accent:#1B4332;
  --accent-light:#D8F3DC;
  --mono:'IBM Plex Mono',monospace;
  --sans:'IBM Plex Sans',sans-serif;
}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh}}
.header{{padding:2.5rem 2.5rem 2rem;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;flex-wrap:wrap}}
.eyebrow{{font-family:var(--mono);font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:var(--muted);margin-bottom:0.6rem}}
h1{{font-size:2rem;font-weight:600;letter-spacing:-0.02em;line-height:1.1}}
h1 em{{font-style:normal;color:var(--muted);font-weight:400}}
.hright{{text-align:right}}
.big{{font-family:var(--mono);font-size:2.2rem;font-weight:500;color:var(--accent);line-height:1}}
.big-sub{{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:var(--dim);margin-top:3px}}
.steps{{display:flex;border-bottom:1px solid var(--border);overflow-x:auto}}
.step{{flex:1;min-width:150px;padding:1rem 1.25rem;border-right:1px solid var(--border);display:flex;gap:10px;align-items:flex-start}}
.step:last-child{{border-right:none}}
.sn{{font-family:var(--mono);font-size:10px;font-weight:500;color:var(--accent);background:var(--accent-light);border-radius:3px;padding:2px 6px;flex-shrink:0;margin-top:1px}}
.st{{font-size:12px;color:var(--muted);line-height:1.5}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1px;background:var(--border);margin:2rem 2.5rem;border:1px solid var(--border);border-radius:8px;overflow:hidden}}
.card{{background:var(--surface);padding:1.25rem;display:flex;flex-direction:column;gap:7px;transition:background .1s}}
.card:hover{{background:#FAFAF8}}
.card-num{{font-family:var(--mono);font-size:10px;color:var(--dim)}}
.card-title{{font-size:13px;font-weight:600;line-height:1.3;flex:1}}
.card-source{{font-family:var(--mono);font-size:10px;color:var(--dim);line-height:1.4}}
.card-footer{{display:flex;align-items:center;justify-content:space-between;margin-top:4px}}
.size{{font-family:var(--mono);font-size:10px;color:var(--dim)}}
.copy-btn{{font-family:var(--sans);font-size:12px;font-weight:500;padding:6px 14px;background:var(--accent);color:#fff;border:none;border-radius:4px;cursor:pointer;transition:opacity .15s}}
.copy-btn:hover{{opacity:.85}}
.copy-btn.loading{{background:var(--dim);cursor:wait}}
.copy-btn.done{{background:#2D6A4F}}
.copy-btn.err{{background:#C0392B}}
.status{{font-family:var(--mono);font-size:10px;color:var(--accent);min-height:14px}}
footer{{padding:1.5rem 2.5rem;border-top:1px solid var(--border);display:flex;justify-content:space-between;font-family:var(--mono);font-size:10px;color:var(--dim);flex-wrap:wrap;gap:8px}}
@media(max-width:600px){{
  .header,.grid,footer{{margin-left:1rem;margin-right:1rem;padding-left:1rem;padding-right:1rem}}
  .header{{padding-top:1.5rem;flex-direction:column;align-items:flex-start}}
  .hright{{text-align:left}}
  h1{{font-size:1.5rem}}
  .grid{{margin:1rem}}
  .steps{{flex-direction:column}}
  .step{{border-right:none;border-bottom:1px solid var(--border)}}
}}
</style>
</head>
<body>
<div class="header">
  <div>
    <div class="eyebrow">PRES · Policy Reasoning &amp; Expert Simulation</div>
    <h1>Finance Agent <em>Training Data</em></h1>
  </div>
  <div class="hright">
    <div class="big">{len(meta) * 15}</div>
    <div class="big-sub">Target training pairs</div>
  </div>
</div>
<div class="steps">
  <div class="step"><span class="sn">01</span><span class="st">Click <strong>Copy prompt</strong> on any document card</span></div>
  <div class="step"><span class="sn">02</span><span class="st">Open <strong>claude.ai</strong> and paste the full text</span></div>
  <div class="step"><span class="sn">03</span><span class="st">Claude generates 15 examples and a <strong>.jsonl</strong> file</span></div>
  <div class="step"><span class="sn">04</span><span class="st">Download the <strong>.jsonl</strong> and send it back on WhatsApp</span></div>
</div>
<div class="grid">
{cards}
</div>
<footer>
  <span>PRES · Finance Agent · {len(meta)} source documents</span>
  <span>Each document produces 15 grounded training pairs · DeepSeek R1 fine-tuning</span>
</footer>
<script>
const slugs = {slugs_js};
async function copy(btn, slug, idx) {{
  const status = document.getElementById('s' + idx);
  btn.textContent = 'Loading...';
  btn.className = 'copy-btn loading';
  try {{
    const res = await fetch('containers/' + slug + '.txt');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const text = await res.text();
    await navigator.clipboard.writeText(text);
    btn.textContent = 'Copied!';
    btn.className = 'copy-btn done';
    status.textContent = (text.length / 1024).toFixed(0) + ' KB on clipboard — paste into Claude';
    setTimeout(() => {{ btn.textContent = 'Copy prompt'; btn.className = 'copy-btn'; status.textContent = ''; }}, 4000);
  }} catch(e) {{
    btn.textContent = 'Failed';
    btn.className = 'copy-btn err';
    status.textContent = e.message;
    setTimeout(() => {{ btn.textContent = 'Copy prompt'; btn.className = 'copy-btn'; status.textContent = ''; }}, 3000);
  }}
}}
document.querySelectorAll('.copy-btn').forEach(btn => {{
  btn.addEventListener('click', () => copy(btn, btn.dataset.slug, btn.dataset.idx));
}});
</script>
</body>
</html>"""


if __name__ == "__main__":
    main()