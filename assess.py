#!/usr/bin/env python3
"""
AI Readiness Research Tool
──────────────────────────
Automatically researches a company's AI readiness signals and produces
a sales prep brief with scores, insights, and key quotes.

SETUP (one time):
  pip install ddgs anthropic requests beautifulsoup4

  export ANTHROPIC_API_KEY="sk-ant-..."   # required for AI analysis
  # On Windows: set ANTHROPIC_API_KEY=sk-ant-...

USAGE:
  python assess.py "Acme Corp"
  python assess.py "Acme Corp" --domain acme.com
  python assess.py "Acme Corp" --domain acme.com --save-dir ./briefs

OUTPUT:
  - Printed to console
  - Saved as [company]_brief_[date].md in current folder (or --save-dir)
"""

import sys
import os
import time
import argparse
import textwrap
from datetime import datetime
from pathlib import Path


# ── Auto-install dependencies ─────────────────────────────────────────────────

def ensure_deps():
    deps = {
        "ddgs":      "ddgs",
        "anthropic": "anthropic",
        "requests":  "requests",
        "bs4":       "beautifulsoup4",
    }
    for module, package in deps.items():
        try:
            __import__(module)
        except ImportError:
            print(f"  Installing {package}...")
            os.system(f"pip install {package} -q")

ensure_deps()

from ddgs import DDGS   # noqa: E402
import anthropic                      # noqa: E402
import requests                       # noqa: E402
from bs4 import BeautifulSoup         # noqa: E402


# ── Config ────────────────────────────────────────────────────────────────────

SEARCH_DELAY  = 1.8   # seconds between searches (avoids DDG rate limits)
MAX_RESULTS   = 6
CLAUDE_MODEL  = "claude-haiku-4-5-20251001"   # fast + cheap; upgrade to sonnet for richer analysis
MAX_TOKENS    = 3000


# ── Search helpers ────────────────────────────────────────────────────────────

def _ddg_text(query, max_results=MAX_RESULTS):
    """DuckDuckGo web search. Returns list of {title, href, body}."""
    try:
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))
        time.sleep(SEARCH_DELAY)
        return results
    except Exception as e:
        print(f"    ⚠ Search error ({query[:45]}…): {e}")
        time.sleep(2)
        return []


def _ddg_news(query, max_results=MAX_RESULTS):
    """DuckDuckGo news search. Returns list of {title, url, excerpt, date}."""
    try:
        ddgs = DDGS()
        results = list(ddgs.news(query, max_results=max_results))
        time.sleep(SEARCH_DELAY)
        return results
    except Exception as e:
        print(f"    ⚠ News search error ({query[:45]}…): {e}")
        return []


def _builtwith(domain):
    """Scrape BuiltWith free page for tech stack summary."""
    if not domain:
        return ""
    try:
        r = requests.get(
            f"https://builtwith.com/{domain}",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                                   "Chrome/120.0.0.0 Safari/537.36"},
            timeout=10
        )
        soup = BeautifulSoup(r.text, "html.parser")
        # Grab category names and technology names from the page
        tags = soup.select("h6, .tech-item, [class*='technology']")
        items = list({t.get_text(strip=True) for t in tags if 3 < len(t.get_text(strip=True)) < 60})
        return " | ".join(items[:30]) if items else ""
    except Exception:
        return ""


# ── Signal gathering ──────────────────────────────────────────────────────────

def gather_signals(company: str, domain: str | None = None) -> dict:
    """
    Run all research searches. Returns a dict of raw search results.
    Covers all 5 assessment signals + 3 quote/insight searches.
    """
    c = company  # shorthand for query construction

    print(f"\n  Gathering signals for: {company}")
    print("  " + "─" * 44)

    signals = {}

    # ── Signal 1: AI/Data job postings (Talent & People dimension)
    print("  ○ AI & data job postings…")
    signals["jobs"] = _ddg_text(
        f'"{c}" "data engineer" OR "data scientist" OR "machine learning engineer" '
        f'OR "AI engineer" OR "head of data" jobs hiring 2024 OR 2025'
    )

    # ── Signal 2: Named AI/Data leadership (Leadership & Strategy dimension)
    print("  ○ AI leadership presence…")
    signals["leadership"] = _ddg_text(
        f'"{c}" "chief data officer" OR "chief AI officer" OR "head of AI" '
        f'OR "VP of data" OR "director of AI" OR "AI lead"'
    )

    # ── Signal 3: Culture & change signals (People & Culture dimension)
    print("  ○ Culture & innovation signals…")
    signals["culture"] = _ddg_text(
        f'"{c}" glassdoor employees technology innovation AI tools culture 2024 OR 2025'
    )

    # ── Signal 4: Technology stack (Data & Tech dimension)
    print("  ○ Technology stack…")
    signals["techstack"]     = _ddg_text(
        f'"{c}" technology stack cloud infrastructure AWS OR Azure OR GCP '
        f'data platform Snowflake OR BigQuery OR Databricks 2024 OR 2025'
    )
    signals["builtwith_raw"] = _builtwith(domain) if domain else ""

    # ── Signal 5: AI strategy & announcements (Leadership & Strategy dimension)
    print("  ○ AI strategy & announcements…")
    signals["ai_strategy"] = _ddg_text(
        f'"{c}" "AI strategy" OR "artificial intelligence strategy" OR "AI roadmap" '
        f'OR "AI investment" 2024 OR 2025',
        max_results=8
    )

    # ── NEW: Quotes — Executive statements on AI
    print("  ○ Executive quotes on AI…")
    signals["exec_quotes"] = _ddg_text(
        f'"{c}" CEO OR CTO OR CDO OR "chief executive" '
        f'"artificial intelligence" OR AI said OR announced OR interview 2024 OR 2025',
        max_results=8
    )

    # ── NEW: AI enablement, training & capability building
    print("  ○ AI enablement & training…")
    signals["ai_enablement"] = _ddg_text(
        f'"{c}" "AI training" OR "AI enablement" OR "AI upskilling" OR '
        f'"AI literacy" OR "capability building" OR "workforce AI" OR "reskilling"'
    )

    # ── NEW: Recent AI news
    print("  ○ Recent AI news…")
    signals["ai_news"] = _ddg_news(
        f'"{c}" artificial intelligence', max_results=8
    )

    print(f"  ✓ Research complete — {sum(len(v) for v in signals.values() if isinstance(v, list))} results gathered\n")
    return signals


# ── Format for Claude ─────────────────────────────────────────────────────────

def _format_result(r: dict) -> str:
    """Format a single search result as a readable text block."""
    title   = r.get("title",   r.get("url",     ""))
    body    = r.get("body",    r.get("excerpt",  r.get("summary", "")))
    url     = r.get("href",    r.get("url",      ""))
    date    = r.get("date",    "")
    date_str = f" [{date}]" if date else ""
    return f"  TITLE:  {title}{date_str}\n  BODY:   {(body or '')[:350]}\n  SOURCE: {url}"


def format_for_claude(signals: dict) -> str:
    """Convert raw signals dict into a clean text block for the Claude prompt."""
    labels = {
        "jobs":          "AI & DATA JOB POSTINGS",
        "leadership":    "AI LEADERSHIP PRESENCE",
        "culture":       "CULTURE & INNOVATION SIGNALS (GLASSDOOR ETC.)",
        "techstack":     "TECHNOLOGY STACK",
        "builtwith_raw": "BUILTWITH TECHNOLOGY DETECTED",
        "ai_strategy":   "AI STRATEGY & ANNOUNCEMENTS",
        "exec_quotes":   "EXECUTIVE QUOTES & STATEMENTS ON AI",
        "ai_enablement": "AI ENABLEMENT, TRAINING & CAPABILITY BUILDING",
        "ai_news":       "RECENT AI NEWS",
    }

    parts = []
    for key, label in labels.items():
        results = signals.get(key, [])
        if key == "builtwith_raw":
            if results:
                parts.append(f"=== {label} ===\n  {results}\n")
            continue
        if not results:
            parts.append(f"=== {label} ===\n  [No results found]\n")
            continue
        parts.append(f"=== {label} ===")
        for r in results:
            parts.append(_format_result(r))
        parts.append("")

    return "\n".join(parts)


# ── Claude analysis prompt ────────────────────────────────────────────────────

PROMPT_TEMPLATE = """\
You are a senior AI sales intelligence analyst. A salesperson sells AI enablement programmes \
to corporate clients. You are preparing their brief for an intro call with {company}.

Analyse the web research below and produce a structured sales prep brief. Be specific — \
cite actual findings. If evidence is thin for a signal, say so honestly rather than guessing.

{research}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Produce the brief in this EXACT format. Use these exact section headers:

## DIMENSION SCORES

Leadership & Strategy: [LOW / MEDIUM / HIGH]
Evidence: [One sentence — specific finding. "Insufficient data" if nothing found.]

Data & Tech: [LOW / MEDIUM / HIGH]
Evidence: [One sentence — specific finding. "Insufficient data" if nothing found.]

People & Culture: [LOW / MEDIUM / HIGH]
Evidence: [One sentence — specific finding. "Insufficient data" if nothing found.]

## READINESS TIER
[LAGGARD / AWARE / READY] — [One sentence rationale based on the three scores above.]

## OPPORTUNITY FLAG
[HOT / WARM / COLD] — [One sentence. HOT = named AI initiative + urgency evident. WARM = general interest signals. COLD = no clear AI motion visible.]

## TOP GAP
[2–3 sentences. What is the company's most significant AI readiness weakness? Why does it matter to their business specifically?]

## PITCH ANGLE
[2–3 sentences. How should the salesperson position an AI enablement or training programme for this specific company? Reference what you found.]

## KEY INSIGHTS & QUOTES
[3–5 of the most relevant, specific insights or direct quotes found in the research.
Prioritise: (1) verbatim executive quotes on AI, (2) specific AI investment/initiative announcements, \
(3) AI training or enablement statements, (4) notable data or culture signals.
DO NOT fabricate quotes. If a result contains a direct quote, use it verbatim.

Format each as:
▸ INSIGHT: [verbatim quote or specific data point — not a paraphrase of a headline]
  SOURCE: [publication or site name] — [URL]
  WHY IT MATTERS: [One sentence on why this is useful in the sales conversation]]

## SIGNAL EVIDENCE SUMMARY
Jobs: [What AI/data job postings indicate about hiring activity and maturity]
Leadership: [Is there a named AI/data leader? What title?]
Culture: [What Glassdoor or culture signals show about openness to change]
Tech Stack: [What infrastructure or tooling is visible]
Recent News: [Any significant AI announcements or investments in last 12 months]

## OPENING QUESTION
[One specific, non-generic question to open the call. It must reference a real finding \
from this research — a quote, a job posting trend, a news item, or a gap. \
Frame it around their business problem, not around AI.]
"""


# ── Claude API call ───────────────────────────────────────────────────────────

def analyze_with_claude(company: str, signals: dict, api_key: str) -> str:
    """Send research to Claude and return the structured brief."""
    client   = anthropic.Anthropic(api_key=api_key)
    research = format_for_claude(signals)
    prompt   = PROMPT_TEMPLATE.format(company=company, research=research)

    print("  Analysing with Claude…")
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


# ── Raw fallback (no API key) ─────────────────────────────────────────────────

def format_raw_output(company: str, signals: dict) -> str:
    """Produce a readable raw-findings report when no API key is available."""
    lines = [
        f"NOTE: Set ANTHROPIC_API_KEY environment variable for AI-powered scoring and analysis.",
        f"Showing raw research findings for manual review.",
        "",
        "═" * 60,
    ]

    section_map = {
        "jobs":          "AI & DATA JOB POSTINGS",
        "leadership":    "AI LEADERSHIP",
        "culture":       "CULTURE SIGNALS",
        "techstack":     "TECH STACK",
        "ai_strategy":   "AI STRATEGY",
        "exec_quotes":   "EXECUTIVE QUOTES ON AI",
        "ai_enablement": "AI ENABLEMENT & TRAINING",
        "ai_news":       "RECENT AI NEWS",
    }

    for key, label in section_map.items():
        results = signals.get(key, [])
        lines.append(f"\n── {label} ──")
        if not results:
            lines.append("  No results found.")
            continue
        for r in results[:4]:
            title  = r.get("title",  r.get("url",    ""))
            body   = r.get("body",   r.get("excerpt", ""))
            url    = r.get("href",   r.get("url",     ""))
            lines.append(f"  • {title}")
            lines.append(f"    {(body or '')[:220]}")
            lines.append(f"    {url}")

    if signals.get("builtwith_raw"):
        lines.append(f"\n── BUILTWITH TECH STACK ──")
        lines.append(f"  {signals['builtwith_raw']}")

    lines.append("\n" + "═" * 60)
    lines.append("\nManual scoring guide:")
    lines.append("  Leadership & Strategy:  Does a CDO/CAIO exist? Is AI named in strategy?")
    lines.append("  Data & Tech:            Is there a modern cloud stack? (AWS/Azure/GCP + data tools)")
    lines.append("  People & Culture:       AI/data hiring activity? Glassdoor culture signals?")
    lines.append("\nReadiness tiers: All-Low=Laggard | Mix=Aware | 2+High=Ready")
    lines.append("Opportunity flag: Named AI initiative=Hot | General interest=Warm | No signal=Cold")

    return "\n".join(lines)


# ── Save output ───────────────────────────────────────────────────────────────

def save_output(company: str, content: str, save_dir: str | None = None) -> Path:
    """Save the brief as a markdown file."""
    slug    = company.lower().replace(" ", "_").replace("/", "_")[:40]
    date    = datetime.now().strftime("%Y%m%d")
    fname   = f"{slug}_brief_{date}.md"

    if save_dir:
        out_dir = Path(save_dir)
    else:
        # Try Cowork outputs path, fall back to current directory
        cowork = Path("/sessions/blissful-fervent-ritchie/mnt/outputs")
        out_dir = cowork if cowork.exists() else Path(".")

    out_dir.mkdir(parents=True, exist_ok=True)
    filepath = out_dir / fname

    header = textwrap.dedent(f"""\
        # AI Readiness Brief: {company}
        *Generated: {datetime.now().strftime("%d %B %Y, %H:%M")}*

        > **Note:** Contact LinkedIn research should be done manually before the call.
        > Review the contact's background, tenure, and any AI-related content they have published
        > to determine whether to pitch as a Technical Buyer, Business Buyer, or find a champion.

        ---

    """)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + content)

    return filepath


# ── Console output formatting ─────────────────────────────────────────────────

def print_banner(company: str, domain: str | None, mode: str):
    width = 62
    print("\n" + "═" * width)
    print(f"  AI READINESS RESEARCH TOOL")
    print(f"  Company : {company}")
    if domain:
        print(f"  Domain  : {domain}")
    print(f"  Mode    : {mode}")
    print(f"  Time    : {datetime.now().strftime('%d %b %Y, %H:%M')}")
    print("═" * width)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AI Readiness Research Tool — automatically researches a company and produces a sales prep brief."
    )
    parser.add_argument("company",
                        help='Company name, e.g. "Acme Corp"')
    parser.add_argument("--domain",
                        help="Company domain for BuiltWith lookup, e.g. acme.com",
                        default=None)
    parser.add_argument("--save-dir",
                        help="Directory to save the brief (default: current folder)",
                        default=None)
    parser.add_argument("--no-save",
                        help="Don't save output to file",
                        action="store_true")
    parser.add_argument("--model",
                        help=f"Claude model to use (default: {CLAUDE_MODEL})",
                        default=None)
    args = parser.parse_args()

    company  = args.company
    api_key  = os.environ.get("ANTHROPIC_API_KEY")
    mode     = f"AI-powered ({CLAUDE_MODEL})" if api_key else "Raw findings (set ANTHROPIC_API_KEY for scoring)"

    if args.model:
        globals()["CLAUDE_MODEL"] = args.model

    print_banner(company, args.domain, mode)

    # Gather all signals
    signals = gather_signals(company, domain=args.domain)

    # Analyse
    if api_key:
        try:
            content = analyze_with_claude(company, signals, api_key)
        except Exception as e:
            print(f"  ⚠ Claude API error: {e}")
            print("  Falling back to raw output…")
            content = format_raw_output(company, signals)
    else:
        content = format_raw_output(company, signals)

    # Print
    width = 62
    print("\n" + "═" * width)
    print(f"  BRIEF: {company.upper()}")
    print("═" * width + "\n")
    print(content)
    print("\n" + "═" * width)

    # Save
    if not args.no_save:
        filepath = save_output(company, content, save_dir=args.save_dir)
        print(f"\n  ✓ Brief saved: {filepath}\n")


if __name__ == "__main__":
    main()
