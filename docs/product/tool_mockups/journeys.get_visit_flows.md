# Tool: journeys.get_visit_flows

## Purpose

Understand visit flows before and after a visit to a given origin:

- Cross-shopping behavior
- Path-to-purchase patterns
- Co-tenancy synergies

This powers all “where do they go before/after X?” questions.

## Primary Personas

- Daniel: golf → convenience/bar path for product placement
- Jasmine: spillover to partner brands / co-marketing
- Sarah & Mike: co-tenancy insights (what pairs well together)

## Inputs (Conceptual)

- `origin_place_ids: string[]`
- `time_range: { start: date; end: date }`
- `window_before_minutes?: number` (default e.g. 120)
- `window_after_minutes?: number` (default e.g. 240)
- `group_by: "destination_place" | "destination_chain" | "destination_category"`
- `min_shared_visitors?: number`

## Outputs (Conceptual)

For each `origin_place_id`:

- `flows_out: {
  destination: { type: "place" | "chain" | "category"; id: string; name: string };
  shared_visitors: number;
  visits: number;
  share_of_origin_visitors: number;
  median_time_offset_minutes: number;  // >0 after, <0 before
}[]`

Optionally:

- Aggregated flows across all origins when multiple are provided.

## Example Usage

1. **Daniel – golf path-to-purchase**

Natural query:

> Map where golfers in [Metro Name] go immediately before and after visiting the top 20 golf courses.

Agent behavior:

- Get top golf course `place_ids` via `places.search_places`.
- Call `journeys.get_visit_flows` with those as `origin_place_ids`.

Expected output use:

- Agent identifies the most common outlet types and specific venues to target for product placement.

2. **Jasmine – spillover to partner brand**

Natural query:

> For visitors to our flagship stores, how often do they also visit [Partner Brand] locations within 3 hours?

Agent behavior:

- Use `origin_place_ids` = flagship stores.
- Set `group_by = "destination_chain"` and filter for the partner chain.

Expected output use:

- Agent quantifies cross-visitation and strengthens the case for co-marketing.

3. **Mike – co-tenancy fit**

Natural query:

> For [Center Name], which categories benefit the most from traffic flows after visits to the anchor tenant?

Agent behavior:

- `origin_place_ids` = anchor.
- `group_by = "destination_category"` and inspect flows within a certain radius.

Expected output use:

- Agent shows which categories are natural followers, informing leasing strategy.
