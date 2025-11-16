# Tool: audience.get_profile_and_overlap

## Purpose

Describe who visits a place/chain and how that audience overlaps or differs from others:

- Demographics, income, households, lifestyle
- Audience similarity and overlap indices

This underpins “fit” questions between assets, brands, and campaigns.

## Primary Personas

- Sarah: tenant / site audience fit
- Mike: asset repositioning and target mix validation
- Jasmine: audience-based store bundling and campaign targeting
- Daniel: whether golf visitors match target segment for a product

## Inputs (Conceptual)

- `base_entities: { type: "place" | "chain"; id: string }[]`
- `comparison_entities?: { type: "place" | "chain"; id: string }[]`
- `baseline?: { type: "region" | "country" | "custom"; id: string }`
- `time_range: { start: date; end: date }`
- `dimensions: ("age" | "income" | "household_size" | "kids" | "lifestyle" | "visit_frequency")[]`

## Outputs (Conceptual)

For each base entity:

- `profile: {
  age_distribution: {...};
  income_distribution: {...};
  household_size_distribution: {...};
  presence_of_kids_pct?: number;
  lifestyle_segments?: { name: string; share_of_visitors: number }[];
  visit_frequency_profile?: {...};
}`
- `vs_baseline?: {
  age_index?: {...};
  income_index?: {...};
}`
- `overlaps?: {
  comparison_entity: { type: "place" | "chain"; id: string; name: string };
  audience_similarity_index: number;  // e.g. 0–100
  shared_visitor_pct?: number;
}[]`

## Example Usage

1. **Jasmine – audience-based store bundle**

Natural query:

> Build a list of stores where the trade-area audience most closely matches [target audience definition] for a premium campaign.

Agent behavior:

- Use external mapping from “target audience definition” → desired distributions.
- Call `audience.get_profile_and_overlap` for candidate stores.
- Compute similarity to target.

Expected output use:

- Agent recommends a store bundle ranked by fit.

2. **Sarah – tenant fit**

Natural query:

> Does the audience at [Center Name] look like the core customer for [Prospective Tenant Chain]?

Agent behavior:

- Call `audience.get_profile_and_overlap` with base = center, comparison = chain.

Expected output use:

- Agent reports similarity index and highlights where they differ (age, income, kids, etc.).

3. **Daniel – golf audience validation**

Natural query:

> Confirm whether visitors to the top 10 golf courses in [Metro Name] match our target profile for the new product.

Agent behavior:

- Call `audience.get_profile_and_overlap` on those golf-course places.

Expected output use:

- Agent shows if they skew toward the desired age/income/lifestyle; if not, suggests alternative venues or segments.
