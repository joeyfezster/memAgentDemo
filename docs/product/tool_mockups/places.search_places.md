# Tool: places.search_places

## Purpose

Discover places (POIs/properties) given geography and filters:

- By category (e.g., "golf course", "regional mall")
- By chain/brand
- By ownership or user-defined portfolio tags (where available)

This is the “catalog discovery” tool that feeds place_ids into all other tools.

## Primary Personas

- Everyone – it’s foundational:
  - Sarah: find candidate sites and comps in a metro
  - Mike: enumerate centers in a region or owned portfolio
  - Jasmine: lists of stores for RMN design
  - Daniel: golf courses and nearby outlets

## Inputs (Conceptual)

- `geo_filter: {
  type: "point_radius" | "bounding_box" | "polygon" | "metro";
  config: {...};
}`
- `category_ids?: string[]` (NAICS-like or internal taxonomy)
- `chain_ids?: string[]`
- `text_query?: string` (name search, e.g., "Chick-fil-A", "Garden State Plaza")
- `portfolio_tags?: string[]` (e.g., "our_stores", "our_centers")
- `min_visits?: number`
- `limit?: number` (for result cap)

## Outputs (Conceptual)

- `places: {
  id: string;
  name: string;
  address: string;
  lat: number;
  lon: number;
  category_id: string;
  chain_id?: string;
  tags?: string[];
}[]`

## Example Usage

1. **Sarah – find comps**

Natural query:

> Find top-performing fast-casual locations similar to our brand within 15 miles of [address].

Agent behavior:

- `places.search_places` with:
  - geo_filter = point_radius,
  - category_ids = fast-casual category,
  - maybe `min_visits` and `limit`.
- Then pass results to `place_insights.get_place_summary` and `performance.compare_locations`.

2. **Mike – portfolio in a region**

Natural query:

> Show me all of our centers in the Southeast region and how they’re trending.

Agent behavior:

- `places.search_places` with `portfolio_tags = ["our_centers"]` + regional geo_filter.
- Use result ids in `performance.compare_locations`.

3. **Daniel – golf course list**

Natural query:

> Identify the top 20 golf courses by visits in [Metro Name].

Agent behavior:

- `places.search_places` with `category_ids = ["golf_course"]` + metro filter + `limit = 20`, optionally sort by visits using heuristics or a follow-up `place_insights` call.

Expected output use:

- Agent feeds these `place_ids` into `journeys.get_visit_flows`, `trade_area.get_trade_area_profile`, etc., to design the launch plan.
