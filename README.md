# AI Readiness Research Tool

A command-line tool that automatically researches a company's AI readiness signals and produces a structured sales prep brief — including dimension scores, key quotes from executives, and a recommended opening question for your call.

Built for sales professionals who sell AI enablement programmes and want to walk into intro calls prepared.

---

## What it does

You give it a company name. It does the rest.

In about 2–3 minutes it runs 8 targeted searches across job boards, news, Glassdoor, executive statements, and tech signals — then uses Claude AI to produce a ready-to-use brief covering:

- **Readiness scores** across 3 dimensions: Leadership & Strategy, Data & Tech, People & Culture
- **Readiness tier**: Laggard / Aware / Ready
- **Opportunity flag**: Hot / Warm / Cold
- **Top gap** — the biggest weakness and why it matters to their business
- **Pitch angle** — how to position your offer for this specific company
- **Key insights & quotes** — 3–5 verbatim executive quotes or data points with sources
- **Opening question** — one specific, non-generic question referencing real findings
- **Signal evidence** — what each search actually found

The brief is printed to your terminal and saved as a `.md` file you can paste into Notion or any note-taking tool.

---

## Requirements

- Python 3.9 or higher
- An [Anthropic API key](https://console.anthropic.com) (costs ~$0.002 per assessment)

---

## Setup

**1. Clone or download this repo**

```bash
git clone https://github.com/YOUR_USERNAME/ai-readiness-tool.git
cd ai-readiness-tool
```

**2. Install dependencies**

```bash
pip3 install -r requirements.txt
```

**3. Set your Anthropic API key**

Mac / Linux:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Windows:
```cmd
set ANTHROPIC_API_KEY=sk-ant-...
```

To make this permanent on Mac/Linux, add the export line to your `~/.zshrc` or `~/.bashrc` file.

Get your API key at [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key.

---

## Usage

**Basic — company name only:**
```bash
python3 assess.py "Acme Corp"
```

**With domain — adds BuiltWith tech stack lookup:**
```bash
python3 assess.py "Acme Corp" --domain acme.com
```

**Save to a specific folder:**
```bash
python3 assess.py "Acme Corp" --domain acme.com --save-dir ~/Documents/briefs
```

**Without saving to file:**
```bash
python3 assess.py "Acme Corp" --no-save
```

**Use a different Claude model** (default is Haiku — fast and cheap):
```bash
python3 assess.py "Acme Corp" --model claude-sonnet-4-5-20250929
```

---

## Example output

```
══════════════════════════════════════════════════════════════
  BRIEF: SIEMENS
══════════════════════════════════════════════════════════════

## DIMENSION SCORES

Leadership & Strategy: HIGH
Evidence: Siemens appointed Vasi Philomin as EVP and Head of Data & AI in 2025,
and CEO Roland Busch has publicly named industrial AI as the company's
"biggest technological lever."

Data & Tech: HIGH
Evidence: Modern cloud infrastructure confirmed via partnerships with AWS, Azure,
NVIDIA, and Databricks; Siemens Industrial Copilot is in active deployment.

People & Culture: MEDIUM
Evidence: Active AI/data hiring visible, but limited Glassdoor signal on
whether AI literacy programmes reach the broader workforce.

## READINESS TIER
READY — Strong leadership commitment, modern infrastructure, and active AI
deployment. Gaps are in workforce enablement, not strategy or infrastructure.

## OPPORTUNITY FLAG
HOT — Siemens has named AI as a strategic priority with specific investment
announcements; there is clear urgency to scale beyond early adopters internally.

## KEY INSIGHTS & QUOTES

▸ INSIGHT: "It's not just about adopting AI — it's about being the fastest to adopt it."
  SOURCE: Siemens Realize LIVE 2025 — https://www.engineering.com/...
  WHY IT MATTERS: Signals internal pressure to accelerate — an enablement programme
  that reduces time-to-adoption is a natural fit.

▸ INSIGHT: Siemens appointed a new EVP and Head of Data & AI (Vasi Philomin)
  effective July 2025, signalling a significant organisational investment in AI leadership.
  SOURCE: Siemens Press — https://press.siemens.com/...
  WHY IT MATTERS: New leader = new mandate, potential new budget, openness to
  external partners who can accelerate delivery.

...

## OPENING QUESTION
"You've moved fast on AI strategy and infrastructure — Roland Busch has been
very public about that. Where are you finding the biggest friction in getting
the broader organisation to actually work differently because of AI?"
```

---

## How to use the brief

1. Run the tool 20–30 minutes before your intro call
2. Review the brief — especially the top gap, pitch angle, and opening question
3. **Do one manual step:** spend 3 minutes on the contact's LinkedIn to understand their background. This tells you whether to pitch as a technical or business conversation — the tool can't know who you're talking to in advance.
4. Open with the suggested question (or your own variation). Reference something specific from the research.

---

## Signals researched

| Signal | What it looks for |
|--------|-------------------|
| Job postings | AI/data/ML roles posted in the last 90 days |
| AI leadership | CDO, CAIO, Head of AI, VP of Data presence |
| Culture | Glassdoor signals on technology and innovation culture |
| Tech stack | Cloud provider, data infrastructure (via BuiltWith if domain provided) |
| AI strategy | Named AI initiatives, roadmaps, investment announcements |
| Executive quotes | CEO/CTO/CDO statements on AI from interviews and press |
| AI enablement | AI training, upskilling, capability building programmes |
| Recent AI news | AI-related announcements and partnerships in the last 12 months |

---

## Without an API key

The tool still runs without `ANTHROPIC_API_KEY` — it will output the raw search findings instead of the analysed brief. Useful for a quick look at what's out there, but you'll need to score and interpret manually.

---

## Cost

Using the default Claude Haiku model: approximately **$0.001–0.003 per assessment** depending on how much is found. Assessing 20 companies costs less than $0.10.

To use a more powerful model (better analysis, slightly higher cost):
```bash
python3 assess.py "Acme Corp" --model claude-sonnet-4-5-20250929
```

---

## Output files

Briefs are saved as `[company]_brief_[date].md` in the current folder by default. These are plain markdown files — paste them directly into Notion, Obsidian, or any markdown-compatible tool.

---

## Notes

- The tool respects search rate limits with a delay between requests. Each run takes 2–3 minutes.
- Search results depend on what is publicly available. For smaller or less prominent companies, some signals may return limited results — the tool will say so clearly rather than fabricating data.
- This tool is for sales preparation only. Treat scores as directional, not definitive.

---

## License

MIT — use and adapt freely.
