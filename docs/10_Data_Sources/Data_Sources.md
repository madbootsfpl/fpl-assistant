This file lists potential data sources, nothing agreed and there may be others to pull data from

> **Integrated so far:** Official FPL API (players, teams, fixtures) and **ClubElo**
> (team Elo, Sprint 009 — best-effort/graceful, powers `fdr --type elo`; see ADR-010).
> Next candidate: FBref/SoccerData for player xG/xA (harder — player-name matching).

The best assistants combine **Fantasy data + Football data + Context + AI-generated insights**.

## Tier 1 - Must Have (Sprint 1)

### Official FPL API ⭐⭐⭐⭐⭐

This is your primary data source.

It gives you:

* Players
* Teams
* Fixtures
* Prices
* Price changes
* Ownership
* Transfers in/out
* Chip usage
* Live scores
* Bonus points
* Expected minutes (indirectly)
* Manager picks (your own team)

This should power about **80% of the application**.

---

### Fixture Difficulty

Rather than relying solely on FPL's own difficulty ratings, calculate your own.

Store:

* Home/Away
* Rest days
* Congested fixtures
* Double Gameweeks
* Blank Gameweeks
* Rolling fixture strength

Your own fixture model will quickly become one of your biggest advantages.

---

### Historical FPL Seasons

There are excellent community archives containing previous FPL seasons.

These allow you to analyse:

* price movements
* player consistency
* points by fixture
* captain success
* chip strategies

Perfect for machine learning later.

---

## Tier 2 - Football Data ⭐⭐⭐⭐

### [football-data.org](https://www.football-data.org/?utm_source=chatgpt.com)

Free tier includes:

* Fixtures
* Results
* League tables
* Team information
* Squads
* Match statistics

Useful for validating FPL fixture information and adding context. ([Football Data][1])

---

### OpenFootball

The [OpenFootball GitHub project](https://github.com/openfootball?utm_source=chatgpt.com) provides public-domain historical football data in structured formats, including Premier League fixtures and results. It's excellent for historical analysis without API limits. ([GitHub][2])

---

## Tier 3 - Player Context

These don't necessarily need APIs.

Build scrapers (carefully respecting each site's terms of use) or manually ingest:

* Injury news
* Suspension news
* Press conferences
* Predicted lineups
* Expected minutes
* European fixtures
* Cup fixtures

Examples include club news pages and official Premier League announcements.

---

## Tier 4 - Weather

Free weather APIs can provide:

* Rain
* Wind
* Temperature

It sounds gimmicky until you notice:

* high wind affects crosses
* heavy rain changes match tempo
* snow postpones games

---

## Tier 5 - Betting Odds

Several providers offer limited free access.

Useful data:

* Match winner probability
* Clean sheet probability
* Anytime scorer odds
* Over/Under goals

Odds are surprisingly strong predictive features because they aggregate market expectations.

---

## Tier 6 - Community Signals

These are gold for an assistant.

Track:

* Reddit trends
* YouTube creators
* X discussions
* Effective Ownership (EO)
* Template teams
* Differential picks

Your assistant could answer:

> "Everyone is buying Wirtz this week, but statistically Gordon is the better pick."

That kind of insight feels much more intelligent than simply listing points.

---

## Tier 7 - Build Your Own Data

This is where your project becomes unique.

Create tables like:

### Player Form

* Last 3
* Last 5
* Last 10

---

### Home/Away Splits

* Goals
* Assists
* Bonus
* xPoints

---

### Team Form

Rolling metrics:

* Goals scored
* Goals conceded
* Clean sheets
* xG trend
* xGA trend

---

### Manager Behaviour

Track yourself:

* Favourite captains
* Hit frequency
* Chip timing
* Transfer habits

Your assistant can then say:

> "Historically you outperform when you avoid taking hits before international breaks."

That's a genuinely personal insight.

---

## Tier 8 - AI-Enriched Data

Instead of storing raw facts, generate higher-level observations, for example:

```
Player Trend:
"Palmer has returned in 8 of his last 10 home matches."

Fixture Summary:
"Arsenal have the easiest defensive run over the next six gameweeks."

Transfer Insight:
"This looks like a sideways move with only a 0.6 expected points gain."

Risk Score:
8.7 / 10
```

These become reusable "knowledge objects" that make the assistant feel much smarter.

## My recommended roadmap

If I were designing your project, I'd build the data layer in this order:

1. ✅ Official FPL API
2. ✅ Local SQLite/PostgreSQL database
3. ✅ Historical FPL archive
4. ✅ Fixture difficulty engine
5. ✅ Team & player form engine
6. ✅ Injury/news ingestion
7. ✅ Weather integration
8. ✅ Betting odds
9. ✅ AI insights
10. ✅ Learning from your own decisions

Given everything we've discussed about your architecture, I also think there's an exciting longer-term goal: **don't build just an FPL assistant—build a football intelligence platform**. If you separate the data ingestion, analytics, and AI layers cleanly from the start, FPL becomes simply one application on top of a general football analytics engine. That makes the project far more extensible while still letting Sprint 1 stay focused on proving a single vertical slice.

[1]: https://www.football-data.org/?utm_source=chatgpt.com "football-data.org - ur src for machine readable football data"
[2]: https://github.com/openfootball?utm_source=chatgpt.com "football.db · GitHub"
