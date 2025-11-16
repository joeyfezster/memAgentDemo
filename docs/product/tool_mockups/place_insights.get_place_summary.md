# Tool: place_insights.get_place_summary

## Purpose

Return a concise health and context snapshot for one or more places:

- Who visits
- How often
- How the place is trending
- Basic competitive positioning in its local market

This is usually the first tool an agent calls once it knows which place(s) it cares about.

## Primary Personas

- Sarah (QSR Real Estate): candidate vs comp store performance
- Mike (REIT Asset Manager): center health and trends
- Jasmine (Retail Media): base understanding of stores used in campaigns
- Daniel (Golf/Tobacco): outlet-level context around courses

## Inputs (Conceptual)

- `place_ids: string[]`
- `time_range: { start: date; end: date }`
- `granularity?: "daily" | "weekly" | "monthly"`
- `include_benchmark?: boolean` (compare vs category/region)
- `include_rollup?: boolean` (aggregate stats for all places)

## Outputs (Conceptual)

For each `place_id`:

- `place: { id, name, address, lat, lon, category, chain_id? }`
- `visits: { total: number, by_period: { period: date; visits: number }[] }`
- `unique_visitors: number`
- `visit_frequency: number` (avg visits per visitor)
- `dwell_time: { median_minutes: number }`
- `trend: { yoy_change_pct?: number; mom_change_pct?: number; classification: "growing" | "stable" | "declining" }`
- `benchmark?`: normalized index vs local/category baseline

## Example Usage

1. **Sarah – candidate vs comps**

Natural query:

> Compare weekly and monthly visit trends and dwell times for this proposed location and our top 10 stores in the same metro.

Agent behavior:

- Use `places.search_places` (category + chain + metro) to find top-10 comps.
- Call `place_insights.get_place_summary` with `[candidate, ...comps]`.

Expected output use:

- Agent builds a table comparing visits, trends, and dwell for candidate vs comps, flags risks.

2. **Mike – center performance check**

Natural query:

> Show me how [Center Name] has performed vs the rest of the submarket over the last 24 months.

Agent behavior:

- Resolve center `place_id`.
- Call `place_insights.get_place_summary` with `include_benchmark = true`.

Expected output use:

- Agent highlights whether center is under/over performing and how trend evolved.

3. **Jasmine – RMN store sanity check**

Natural query:

> Before I add these 50 stores to a premium media package, sanity-check that they’re not structurally declining.

Agent behavior:

- Call `place_insights.get_place_summary` on the 50 stores, inspect trend classifications.

Expected output use:

- Agent marks any “declining” stores and suggests replacements or caveats.
