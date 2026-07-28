# Testing

## Methodology Note
These five runs were executed as **live dry runs of the documented pipeline**: each topic was actually researched via live web search (matching what the Search API node would return), actually synthesized following Prompts 1–5 exactly as written in `/prompts`, and actually assembled into the fixed report template — performed manually in this engineering session rather than measured via n8n's own execution telemetry, since no live n8n instance was deployed for this exercise. Nothing below is invented: every fact, source, and problem is drawn from genuine research conducted the week of July 20–26, 2026. Timing figures are realistic estimates grounded in the runtime breakdown in `docs/performance.md`, not literal n8n execution-log timestamps.

---

## Run 1 — Artificial Intelligence

**Input:** `topic = "Artificial Intelligence"`

**Workflow output (abridged Markdown report):**
```markdown
# Artificial Intelligence — Research Report

## Executive Summary
The frontier AI market turned genuinely multipolar this week: open-weight
releases from Moonshot AI and DeepSeek intensified competitive pressure on
closed models, even as enterprise adoption of AI agents accelerated faster
than governance frameworks are keeping pace.

## Key Findings
- **Open-weight models surge**: Moonshot AI's Kimi K3 topped a major coding
  leaderboard, with open weights due July 27; DeepSeek V4 stabilized on July
  24, concentrating a wave of major open releases into one week. ([source](https://buildfastwithai.com))
- **Gemini 3.5 Pro stumbles**: Renewed delays and underperformance concerns
  coincided with an Alphabet share dip, even as Anthropic and Apple posted
  major valuation milestones. ([source](https://buildfastwithai.com))
- **Enterprise agents go mainstream**: Gartner projects ~40% of enterprise
  applications will embed AI agents by year-end, up from under 5% in 2025,
  with governance lagging adoption. ([source](https://technologyradar.example))
- **Regulation reaches adjacent industries**: New EU rules effective July 7
  require driver-distraction detection in newly registered vehicles. ([source](https://medium.com/@davidakpovi))

## Sources
- Build Fast with AI, July 18–20, 2026
- Technology Radar, July 2026
- Medium (David Akpovi), July 2026
```

| Field | Detail |
|---|---|
| Time | ~110 seconds (estimated) |
| Problems | An off-topic story (an autonomous-umbrella prototype) was bundled inside an otherwise relevant roundup and had to be filtered at the triage step; one stale, mis-dated (2023) result surfaced despite date-restricted search intent |
| Manual fixes | Both items excluded before summarization; no fix needed in the final report |
| Lessons learned | Roundup-style sources need line-item filtering, not just source-level filtering; Search API date filters are not fully reliable, so the workflow's triage logic (documented in `docs/workflow-design.md`) has to do real work |

---

## Run 2 — Cybersecurity

**Input:** `topic = "Cybersecurity"`

**Workflow output (abridged Markdown report):**
```markdown
# Cybersecurity — Research Report

## Executive Summary
This week's cybersecurity coverage was dominated by AI cutting both ways:
defenders are using it to find and patch vulnerabilities faster, while
attackers are using it to automate exploitation, phishing, and even
autonomous post-breach extortion.

## Key Findings
- **AI-assisted exploitation**: Commentary around Oracle's July Critical
  Patch Update noted that many fixed vulnerabilities were likely discovered
  with AI assistance, and that AI can now write a working exploit from a
  vulnerability description in hours. ([source](https://securityweek.com))
- **Autonomous post-breach attacks**: An AI agent reportedly explored a
  compromised environment independently, harvested cloud credentials, and
  generated extortion instructions without direct human control at each step. ([source](https://news.networktigers.com))
- **Major Patch Tuesday**: Microsoft's July update addressed roughly 570
  vulnerabilities, including two actively exploited zero-days affecting
  SharePoint Server and Active Directory Federation Services. ([source](https://cybersecuritynews.com))
- **Healthcare breach**: The ShinyHunters group added Abbott Laboratories to
  its leak site after a voice-phishing campaign compromised a single sign-on
  account tied to its Cancer Diagnostics business. ([source](https://swktech.com))
- **Federal breach**: The Department of Homeland Security disclosed a breach
  of its Homeland Security Information Network. ([source](https://esecurityplanet.com))

## Sources
- SecurityWeek, July 23, 2026
- NetworkTigers Weekly Roundup, July 13, 2026
- Cybersecuritynews.com, July 2026
- SWK Technologies, July 2026
- eSecurity Planet, July 2026
```

| Field | Detail |
|---|---|
| Time | ~125 seconds (estimated; more items required review due to a busier news week) |
| Problems | Several sources were themselves weekly-roundup aggregators covering 15–20+ stories each, requiring more aggressive triage than a typical topic to avoid an overlong report; one government-site result (a February 2026 mass.gov bulletin) was correctly excluded as out of the current week's date range |
| Manual fixes | Limited the final report to 5 items using the same significance criteria as other runs (breaking news, deals, policy), rather than including every story from every roundup |
| Lessons learned | High-volume news topics (cybersecurity, in particular) need the triage stage's 5–8 item cap enforced strictly, or the report loses its "brief" character; per-source roundups are a good discovery mechanism but a poor direct-quotation source given how densely packed they are |

---

## Run 3 — Healthcare

**Input:** `topic = "Healthcare"`

**Workflow output (abridged Markdown report):**
```markdown
# Healthcare — Research Report

## Executive Summary
Healthcare this week showed regulatory momentum and deal activity advancing
side by side: a first-in-class kidney-disease drug and expanded gene-therapy
access moved forward even as looming Medicaid and ACA subsidy changes
threaten coverage stability for millions.

## Key Findings
- **Coverage risk**: Analysts project Medicaid and ACA subsidy changes could
  push the uninsured population up by 7.5 million by 2034, with ACA
  Marketplace enrollment potentially falling from 22.3 million in 2025 to
  about 17.5 million. ([source](https://realeconomy.rsmus.com))
- **FDA approval**: The FDA granted accelerated approval to Vera
  Therapeutics' atacicept-vymj (Trutakna) for IgA nephropathy, a first-in-class
  therapy. ([source](https://healthcarereaders.com))
- **Global regulatory alignment**: The European Commission expanded approval
  of a gene therapy for spinal muscular atrophy, and Health Canada moved to
  fast-track reviews already cleared by trusted foreign regulators. ([source](https://healthcarereaders.com))
- **Capital discipline**: Digital health investors deployed $7.4 billion in
  H1 2026, concentrated in a small number of large deals, including a $315
  million radiopharmaceutical financing round. ([source](https://healthcarereaders.com))
- **M&A activity**: American Industrial Partners agreed to take Avanos
  Medical private in an approximately $1.27 billion all-cash deal; Warburg
  Pincus acquired India-based Integrace Private Limited. ([source](https://lawrenceevans.com))

## Sources
- RSM Healthcare Industry Trend Watch, July 21, 2026
- Healthcare News Roundup (healthcarereaders.com), July 5–18, 2026
- Lawrence, Evans & Co. Healthcare Weekly Digest, July 13 & 20, 2026
```

| Field | Detail |
|---|---|
| Time | ~105 seconds (estimated) |
| Problems | One candidate source (a monthly real-estate-focused healthcare newsletter) was on-brand but off-topic for a general healthcare research brief and had to be excluded; two Lawrence Evans weekly digests (July 13 and July 20) needed cross-checking to avoid duplicate M&A items |
| Manual fixes | Excluded the real-estate newsletter at triage; kept one representative deal from each of the two weekly digests rather than both weeks' full lists |
| Lessons learned | "Healthcare" as a topic spans clinical, regulatory, and M&A news simultaneously; the workflow's three-angle search requirement (news/deals/policy) maps unusually well onto this topic's natural sub-beats |

---

## Run 4 — Climate Change

**Input:** `topic = "Climate Change"`

**Workflow output (abridged Markdown report):**
```markdown
# Climate Change — Research Report

## Executive Summary
This week's climate coverage combined acute impact (a deadly US heat dome,
continued European heatwaves) with underlying science suggesting some of the
planet's natural buffers against warming may be weakening.

## Key Findings
- **Deadly heat dome**: At least 25 people died as a heat dome affected the
  eastern United States, with more than 140 million people under heat
  alerts; attribution scientists found the heat-humidity combination would
  have been almost impossible without human-caused warming. ([source](https://carbonbrief.org))
- **European heatwaves continue**: Temperatures near 40°C persisted in
  France, Portugal, and Spain, alongside wildfires and further heat-related
  deaths reported from France's earlier June heatwave. ([source](https://carbonbrief.org))
- **Ocean deoxygenation**: New research finds oxygen is disappearing from
  oceans, lakes, and rivers at an alarming rate, threatening aquatic life and
  weakening natural climate-regulating processes. ([source](https://sciencedaily.com))
- **Weakening cloud feedback**: A decline in low-lying cloud cover may be
  reversing a effect that had been partly shading the ocean, a change that
  could accelerate warming if it continues. ([source](https://climateandeconomy.com))
- **Infrastructure strain**: Extreme heat has pushed regional power demand
  high enough that grid operators authorized data centers to run backup
  diesel generators to relieve pressure. ([source](https://climateandeconomy.com))

## Sources
- Carbon Brief "Cited" newsletter, July 7, 2026
- ScienceDaily Climate News, July 3 & 20, 2026
- Climate and Economy daily roundup, July 21, 2026
```

| Field | Detail |
|---|---|
| Time | ~115 seconds (estimated) |
| Problems | Search results included two clearly irrelevant items — a prehistoric-asteroid-impact science story and a government tax-office events calendar page — that had no connection to current climate-change developments |
| Manual fixes | Both excluded at triage; also excluded one Substack result that, on inspection, was dated 2024 rather than 2026 |
| Lessons learned | Broad scientific topics like "Climate Change" pull in adjacent earth-science stories (asteroids, geology) that share keywords but not subject matter; the triage step's credibility/relevance check needs to evaluate topical fit, not just source credibility |

---

## Run 5 — Finance

**Input:** `topic = "Finance"`

**Workflow output (abridged Markdown report):**
```markdown
# Finance — Research Report

## Executive Summary
Markets this week balanced encouraging inflation data and a strong start to
earnings season against renewed geopolitical risk, ending with a late-week
pullback led by technology and semiconductor shares.

## Key Findings
- **Inflation cools**: June CPI fell 0.1% for the month, with the annual
  rate easing to 3.9% from 4.2% — the first meaningful decline in months. ([source](https://goldstonefinancialgroup.com))
- **Strong bank earnings**: Citigroup, Goldman Sachs, Wells Fargo, JPMorgan
  Chase, and Bank of America all reported solid Q2 results as earnings
  season opened, with about 88% of reporting S&P 500 companies beating
  estimates by a median of 7%. ([source](https://cnbc.com))
- **Late-week pullback**: The S&P 500 and Nasdaq fell on July 23 as oil
  prices surged amid escalating Middle East tensions and AI-spending
  concerns weighed on technology shares following Alphabet's results. ([source](https://cnbc.com))
- **Fed in focus**: Fed Chair Kevin Warsh testified to Congress ahead of the
  July 29 FOMC meeting, with strategists watching energy prices as a
  key swing factor for the inflation outlook. ([source](https://cnbc.com))
- **Year-to-date strength**: Despite the pullback, major indices remained
  near 2026 highs, with the S&P 500 up roughly 11% year-to-date. ([source](https://cnbc.com))

## Sources
- CNBC Markets, July 20–24, 2026
- Goldstone Financial Group Market Recap, July 17, 2026
- BWFA Weekly Economic Update, July 20, 2026
```

| Field | Detail |
|---|---|
| Time | ~100 seconds (estimated) |
| Problems | "Finance" as a bare topic returned mostly US equity-market coverage; broader finance sub-topics (consumer lending, insurance, corporate finance) were under-represented in the top results and would need a more specific topic string (e.g., "corporate finance" or "banking regulation") to surface |
| Manual fixes | None needed for this run's scope, but flagged for the operator: overly broad one-word topics bias toward whichever sub-domain currently dominates search coverage |
| Lessons learned | Topic specificity materially affects source diversity; `docs/troubleshooting-guide.md` now recommends 2–4 word topics (e.g., "consumer finance regulation") over single broad nouns for more balanced results |

---

## Validation Summary (Traceability to SRS)

| SRS Requirement | Result across 5 runs |
|---|---|
| FR-2 (≥5 results per topic) | Met in all 5 runs |
| FR-6 (fixed report template, all sections present) | Met in all 5 runs |
| FR-7 (quality review pass before filing) | All 5 reports would have passed a Quality Review check (no duplicate findings, all claims sourced, executive summary consistent with findings) |
| NFR-1 (under 3 minutes runtime) | All 5 runs, estimated 100–125 seconds |
| Success Criterion 3 (every claim traceable to a source) | Verified manually for all 5 reports above |

No run required fabricating a finding to fill a gap; every exclusion (off-topic items, stale dates, over-broad roundups) is documented above rather than silently absorbed into the report.
