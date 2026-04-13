"""
strip.py — strips Docling JSON to minimal content for clipboard containers
Usage: python3 strip.py
Reads from SOURCE_DIR, writes stripped JSONs to STRIPPED_DIR
"""

import json
import os

SOURCE_DIR = "/mnt/c/Users/User/Downloads/cache_batch1"
STRIPPED_DIR = "/home/darwin/PRES/data/finance/source_docs"

# Finance agent — best 25 documents from the corpus
FINANCE_DOCS = [
    "2025_budget_policy_statement.json",
    "2026_budget_policy_statement.json",
    "2024_economic_survey.json",
    "2025_economic_survey.json",
    "cbk_2024_annual_report.json",
    "cbk_2025_annual_report.json",
    "annual_public_debt_report_2024_2025.json",
    "annual_public_debt_report_2023_2024.json",
    "tax_expenditure_report_ter_2024.json",
    "2023_tax_expenditure_report_final.json",
    "annual_revenue_performance_fy_2024_25_kr.json",
    "annual_revenue_performance_fy_2023_2024_.json",
    "imf_2023.json",
    "imf_2021.json",
    "world_bank_2024.json",
    "the_finance_act_2023.json",
    "thefinancebill_2024.json",
    "the_finance_bill_2025.json",
    "cbk_fsr_2024_sept_final_2025.json",
    "cbk_fsr_2023_published.json",
    "2024_medium_term_debt_management_strateg.json",
    "2021_medium_term_debt_manadement_strateg.json",
    "2025_budget_review_and_outlook_paper_1.json",
    "2024_budget_review_and_outlook_paper.json",
    "2022_post_election_economic_and_fiscal_r.json",
]


def strip_doc(data: dict) -> dict:
    """Strip Docling JSON to content-only fields."""
    content = []
    last_heading = None

    for b in data.get("blocks", []):
        hp = " > ".join(b["heading_path"]) if b.get("heading_path") else ""
        if hp != last_heading:
            content.append({"section": hp})
            last_heading = hp
        content.append({"p": b["page_number"], "t": b["text"]})

    for t in data.get("tables", []):
        content.append({
            "table_page": t["page_number"],
            "section": " > ".join(t["heading_path"]) if t.get("heading_path") else "",
            "markdown": t["markdown"]
        })

    return {
        "source_file": data["source_file"],
        "doc_slug": data["doc_slug"],
        "content": content
    }


def main():
    os.makedirs(STRIPPED_DIR, exist_ok=True)
    success, failed = [], []

    for filename in FINANCE_DOCS:
        src = os.path.join(SOURCE_DIR, filename)
        dst = os.path.join(STRIPPED_DIR, filename)

        if not os.path.exists(src):
            print(f"  MISSING: {filename}")
            failed.append(filename)
            continue

        with open(src, encoding="utf-8") as f:
            data = json.load(f)

        stripped = strip_doc(data)
        stripped_json = json.dumps(stripped, separators=(",", ":"), ensure_ascii=False)

        with open(dst, "w", encoding="utf-8") as f:
            f.write(stripped_json)

        orig_kb = os.path.getsize(src) / 1024
        new_kb = len(stripped_json) / 1024
        print(f"  OK  {filename:<55} {orig_kb:>7.1f} KB → {new_kb:>7.1f} KB  ({(1-new_kb/orig_kb)*100:.0f}% reduction)")
        success.append(filename)

    print(f"\nDone: {len(success)} stripped, {len(failed)} missing")
    print(f"Stripped docs saved to: {STRIPPED_DIR}")


if __name__ == "__main__":
    main()