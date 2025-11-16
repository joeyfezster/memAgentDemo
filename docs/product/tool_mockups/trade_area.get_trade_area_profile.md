# Tool: trade_area.get_trade_area_profile

## Purpose

Describe the "True Trade Area" of one or more places:

- Where visitors come from
- How important each geography is
- Who those visitors are (demographics, income, household profile)

Used whenever the question is “where do my visitors live/work and what are they like?”.

## Primary Personas

- Sarah: cannibalization risk and white space / infill
- Mike: catchment quality and repositioning
- Jasmine: geo/audience fit for campaigns
- Daniel: trade areas around golf courses and nearby outlets

## Inputs (Conceptual)

- `place_ids: string[]`
- `time_range: { start: date; end: date }`
- `output_geography: "block_group" | "census_tract" | "zip" | "cbg"`
- `include_demographics?: boolean`
- `include_psychographics?: boolean`
- `max_radius_km?: number` (optional clip)

## Outputs (Conceptual)

For each `place_id`:

- `trade_area_polygon: GeoJSON` (or list of polygons)
- `geo_units: {
  id: string;
  visits: number;
  share_of_visits: number;
  avg_distance_km?: number;
  demographics?: {...};
  psychographics?: {...};
}[]`
- `summary: {
  median_distance_km: number;
  top_n_geo_units: string[];
  diversity_index?: number;
}`

## Example Usage

1. **Sarah – cannibalization**

Natural query:

> Estimate cannibalization if we open a new store at [candidate address] relative to stores A and B.

Agent behavior:

- Use `places.search_places` to resolve `place_ids`.
- Call `trade_area.get_trade_area_profile` on `[candidate, A, B]`.
- Compute overlap of geo_units for candidate vs A/B.

Expected output use:

- Agent quantifies % of candidate trade area already served by A/B and highlights incremental coverage.

2. **Mike – catchment assessment**

Natural query:

> Does [Center Name] pull from the higher-income households we’re targeting for this repositioning?

Agent behavior:

- Call `trade_area.get_trade_area_profile` with `include_demographics = true`.
- Filter geo_units for income bands and share of visits.

Expected output use:

- Agent summarizes share of visits from target income brackets and compares with plan.

3. **Daniel – golf course trade areas**

Natural query:

> For the top 10 golf courses in [Metro Name], where do visitors predominantly come from?

Agent behavior:

- Get golf-course `place_ids` via `places.search_places`.
- Call `trade_area.get_trade_area_profile` for each.

Expected output use:

- Agent identifies overlapping geos, potential regional clusters, and high-value segments for target marketing.
