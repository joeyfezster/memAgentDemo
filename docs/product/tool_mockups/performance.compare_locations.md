# Tool: performance.compare_locations

## Purpose

Compare time-series performance of multiple locations or chains:

- Rank and classify them
- Benchmark them against peers or a market baseline

This powers portfolio views and “who’s winning/losing” questions.

## Primary Personas

- Sarah: market or chain-wide ranking for stores
- Mike: portfolio health, top/bottom centers
- Jasmine: find fast-growing stores for RMN
- Daniel: post-launch outlet monitoring

## Inputs (Conceptual)

- `entities: { type: "place" | "chain"; id: string }[]`
- `time_range: { start: date; end: date }`
- `metric: "visits" | "visit_frequency" | "dwell_time"`
- `benchmark?: {
  type: "category_region" | "custom_set";
  config: {...}
}`
- `classification_thresholds?: { growing: number; declining: number }` (e.g. ±5% YoY)

## Outputs (Conceptual)

- `series: {
  entity: { type: "place" | "chain"; id: string };
  by_period: { period: date; value: number }[];
  yoy_change_pct?: number;
  mom_change_pct?: number;
  classification: "growing" | "stable" | "declining";
  benchmark_index?: number;
}[]`
- `rankings: {
  metric: string;
  ranked_entities: { id: string; value: number; rank: number }[];
}[]`

## Example Usage

1. **Mike – redevelopment impact**

Natural query:

> Compare visits to [Center Name] for 12 months before vs 12 months after the redevelopment, and benchmark vs similar centers.

Agent behavior:

- Define pre and post windows.
- Call `performance.compare_locations` twice or with segmented time_range and a peer set benchmark.

Expected output use:

- Agent shows change in classification, YoY uplift, and performance vs peers.

2. **Sarah – market ranking**

Natural query:

> Rank all our stores in [Metro Name] by 12-month visit trend and flag declining ones.

Agent behavior:

- Get list of stores in metro via external CRM or `places.search_places`.
- Call `performance.compare_locations` with metric = `visits`.

Expected output use:

- Agent surfaces top/bottom stores and suggests where to investigate closures/moves.

3. **Jasmine – RMN expansion**

Natural query:

> Identify stores with at least +10% YoY visit growth to consider for a new premium media product.

Agent behavior:

- Call `performance.compare_locations` for all candidate stores.
- Filter by `yoy_change_pct >= 10`.

Expected output use:

- Agent outputs a shortlist of growth stores to be added to the RMN tier.
