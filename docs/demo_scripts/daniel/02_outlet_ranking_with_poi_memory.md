# Demo Script 2: Outlet Ranking with POI Memory

## Objective

Showcase **ManageUserMemoryTool** storing and retrieving POIs (Places of Interest) with notes for key locations Daniel tracks.

## Prerequisites

- User: daniel.insights@goldtobacco.com logged in
- **Seeded conversation** from 3 days ago: "Topgolf Scottsdale Outlet Prioritization"
- **Agent should have stored POI** for Topgolf Scottsdale in user memory

## Memory Tools Showcased

1. **manage_user_memory (operation: add_poi)** - Store place of interest with notes
2. **manage_user_memory (operation: get_memory)** - Retrieve stored POIs and facts
3. **search_past_conversations** - Retrieve context about stored POI

---

## Required Seed Conversation

**Title:** "Topgolf Scottsdale Outlet Prioritization"
**Created:** 3 days ago
**User ID:** daniel.insights@goldtobacco.com

### Message 1 (User)

```
I want to analyze Topgolf Scottsdale as a potential anchor location for our golf line. Find nearby convenience stores within a 10-minute drive and rank them by overlap with Topgolf visitors.
```

### Message 2 (Agent)

```
I'll analyze Topgolf Scottsdale and identify high-overlap convenience stores in the surrounding area.
```

### Tool Call 1: search_places

```json
{
  "geo_filter": {
    "type": "point_radius",
    "config": { "lat": 33.4673, "lon": -111.9564, "radius_km": 8 }
  },
  "text_query": "Topgolf Scottsdale",
  "limit": 1
}
```

### Tool Result 1:

```json
{
  "places": [
    {
      "id": "topgolf_scottsdale_001",
      "name": "Topgolf Scottsdale",
      "lat": 33.4673,
      "lon": -111.9564
    }
  ]
}
```

### Tool Call 2: get_place_summary

```json
{
  "place_ids": ["topgolf_scottsdale_001"],
  "time_range": { "start": "2024-01-01", "end": "2024-12-31" },
  "granularity": "monthly",
  "include_benchmark": true
}
```

### Tool Result 2:

```json
{
  "summaries": [
    {
      "place_id": "topgolf_scottsdale_001",
      "metrics": {
        "monthly_visits": 28500,
        "unique_visitors": 19200,
        "visit_frequency": 1.48
      }
    }
  ]
}
```

### Tool Call 3: search_places (nearby convenience stores)

```json
{
  "geo_filter": {
    "type": "point_radius",
    "config": { "lat": 33.4673, "lon": -111.9564, "radius_km": 8 }
  },
  "category_ids": ["convenience_store"],
  "limit": 10
}
```

### Tool Result 3:

```json
{
  "places": [
    {
      "id": "cvs_001",
      "name": "7-Eleven - Scottsdale Rd",
      "lat": 33.4692,
      "lon": -111.9501
    },
    {
      "id": "cvs_002",
      "name": "Circle K - Greenway Pkwy",
      "lat": 33.471,
      "lon": -111.9488
    },
    {
      "id": "cvs_003",
      "name": "QuikTrip - Loop 101",
      "lat": 33.4621,
      "lon": -111.9612
    }
  ]
}
```

### Tool Call 4: get_profile_and_overlap

```json
{
  "base_entities": [{ "type": "place", "id": "topgolf_scottsdale_001" }],
  "comparison_entities": [
    { "type": "place", "id": "cvs_001" },
    { "type": "place", "id": "cvs_002" },
    { "type": "place", "id": "cvs_003" }
  ],
  "time_range": { "start": "2024-01-01", "end": "2024-12-31" },
  "dimensions": ["age", "income"]
}
```

### Tool Result 4:

```json
{
  "overlaps": [
    {
      "entity": { "type": "place", "id": "cvs_001" },
      "overlap_index": 78.4,
      "shared_visitors": 15040
    },
    {
      "entity": { "type": "place", "id": "cvs_002" },
      "overlap_index": 71.2,
      "shared_visitors": 13664
    },
    {
      "entity": { "type": "place", "id": "cvs_003" },
      "overlap_index": 65.8,
      "shared_visitors": 12636
    }
  ]
}
```

### Message 3 (Agent)

```
Here's the Topgolf Scottsdale outlet analysis:

**Topgolf Scottsdale Performance:**
- Monthly visits: 28,500
- Unique visitors: 19,200
- Visit frequency: 1.48x per month

**Top 3 Convenience Stores by Visitor Overlap:**

1. **7-Eleven - Scottsdale Rd**
   - Overlap index: 78.4%
   - Shared visitors: 15,040 monthly
   - Distance: 0.8 miles northeast

2. **Circle K - Greenway Pkwy**
   - Overlap index: 71.2%
   - Shared visitors: 13,664 monthly
   - Distance: 1.1 miles north

3. **QuikTrip - Loop 101**
   - Overlap index: 65.8%
   - Shared visitors: 12,636 monthly
   - Distance: 1.4 miles south

**Recommendation:** The 7-Eleven on Scottsdale Rd should be your #1 priority outlet - it captures 78% overlap with Topgolf visitors and sees 15K shared visitors per month. This is an ideal first-wave placement location.
```

### Tool Call 5: manage_user_memory (add_poi - AGENT'S AUTONOMOUS DECISION)

```json
{
  "operation": "add_poi",
  "place_id": "topgolf_scottsdale_001",
  "place_name": "Topgolf Scottsdale",
  "notes": "Key anchor location for golf line launch. 28.5K monthly visits, 19.2K unique visitors. 7-Eleven Scottsdale Rd (78% overlap) is top priority outlet."
}
```

### Tool Result 5:

```json
{
  "success": true,
  "operation": "add_poi",
  "place_id": "topgolf_scottsdale_001",
  "message": "Stored place: Topgolf Scottsdale"
}
```

### Message 4 (User)

```
Excellent. This 7-Eleven location should definitely be in our first wave. Let's track this as a priority.
```

### Message 5 (Agent)

```
I've stored Topgolf Scottsdale in your memory with the key metrics and the top outlet priority. This will help us track performance post-launch.
```

---

## Demo Script Execution

### User Message 1 (Type slowly)

```
What locations have I been tracking for the golf line launch?
```

**Expected Agent Behavior:**

1. Recognize request for stored memory
2. Call `manage_user_memory` with operation: `get_memory`
3. Retrieve POIs from user's memory document
4. Present stored places with notes

**UI Should Show:**

- Tool interaction block with tool name: "manage_user_memory"
- Tool parameters: `{"operation": "get_memory"}`
- Tool result showing facts and POIs arrays with metadata
- Agent response synthesizing the memory contents

### Expected Agent Response

```
You've been tracking the following location for your golf line launch:

**Topgolf Scottsdale** (Place ID: topgolf_scottsdale_001)
- Notes: Key anchor location for golf line launch. 28.5K monthly visits, 19.2K unique visitors. 7-Eleven Scottsdale Rd (78% overlap) is top priority outlet.
- Added: 3 days ago

This location has strong visitor volumes and a high-overlap convenience store nearby that you identified as a first-wave placement priority.
```

### User Message 2 (Type slowly)

```
Remind me about the analysis we did for that Topgolf location - what were the exact overlap numbers for the top 3 stores?
```

**Expected Agent Behavior:**

1. Recognize reference to past discussion
2. Call `search_past_conversations` with keywords: `["Topgolf", "Scottsdale", "overlap", "convenience"]`
3. Retrieve seeded conversation from 3 days ago
4. Extract exact overlap percentages and store names

**UI Should Show:**

- Tool interaction for search_past_conversations
- Matched conversation snippet with **[MATCH]** marker
- Agent synthesizing the specific metrics requested

### Expected Agent Response

```
From our Topgolf Scottsdale analysis 3 days ago, here were the exact overlap numbers for the top 3 convenience stores:

1. **7-Eleven - Scottsdale Rd**: 78.4% overlap, 15,040 shared visitors monthly
2. **Circle K - Greenway Pkwy**: 71.2% overlap, 13,664 shared visitors monthly
3. **QuikTrip - Loop 101**: 65.8% overlap, 12,636 shared visitors monthly

The 7-Eleven location had nearly 80% overlap with Topgolf visitors, making it your highest-priority outlet for first-wave product placement.
```

### User Message 3 (Type slowly)

```
Perfect. I want to add a note that we launched product at that 7-Eleven last week.
```

**Expected Agent Behavior:**

1. Recognize request to update memory
2. Call `manage_user_memory` with operation: `add_fact`
3. Store launch information as a fact

**UI Should Show:**

- Tool interaction for manage_user_memory (add_fact)
- Tool parameters showing content field
- Success response with fact_id

### Expected Agent Response

```
I've recorded that you launched product at the 7-Eleven on Scottsdale Rd last week. This fact is now stored in your memory and I'll remember it for future conversations about the launch performance.
```

### User Message 4 (Type slowly)

```
Show me everything you remember about my golf launch project.
```

**Expected Agent Behavior:**

1. Call `manage_user_memory` with operation: `get_memory`
2. Retrieve all facts and POIs
3. Present organized summary

### Expected Agent Response

```
Here's everything I have stored about your golf launch project:

**Tracked Locations (POIs):**
- Topgolf Scottsdale: Key anchor location, 28.5K monthly visits, 7-Eleven Scottsdale Rd (78% overlap) is top priority outlet

**Launch Facts:**
- Product launched at 7-Eleven on Scottsdale Rd last week

**Memory Stats:**
- Total facts: 1 active
- Total POIs: 1
- Token count: ~120 tokens

This memory will persist across all your future conversations, so I can always reference these details when discussing launch performance or expansion planning.
```

---

## Success Criteria

✅ Agent autonomously stored POI during seeded conversation (showed in seed)
✅ Agent retrieves memory on request showing POIs with notes
✅ Agent combines memory retrieval (POI) with conversation search (analysis details)
✅ Agent stores new fact when user provides launch update
✅ Agent presents comprehensive memory view with both POIs and facts
✅ All tool interactions visible in UI with parameters and results

---

## Technical Notes

- The agent should have called `add_poi` autonomously during the seed conversation when the user showed strong interest ("Let's track this as a priority")
- POI notes field stores the key context so agent doesn't need to search conversations for basic info
- Facts vs POIs distinction: Facts are statements/preferences, POIs are specific places with Placer IDs
