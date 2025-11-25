# Demo Script 1: Golf Course Visitor Recall

## Objective

Showcase **SearchPastConversationsTool** retrieving prior Phoenix golf course analysis to inform Dallas strategy.

## Prerequisites

- User: daniel.insights@goldtobacco.com logged in
- **Seeded conversation** from 7 days ago: "Phoenix Golf Course Path-to-Purchase Analysis"

## Memory Tools Showcased

1. **search_past_conversations** - Keyword-based cross-conversation retrieval
2. Tool interaction visibility in UI (tool call, parameters, results streaming)

---

## Required Seed Conversation

**Title:** "Phoenix Golf Course Path-to-Purchase Analysis"
**Created:** 7 days ago
**User ID:** daniel.insights@goldtobacco.com

### Message 1 (User)

```
For the Phoenix metro area, identify the top 10 golf courses by visit volume over the last 12 months, then map where their visitors most frequently go immediately before and after a course visit. Break the results down by venue type - I need to understand the path-to-purchase behavior.
```

### Message 2 (Agent)

```
I'll analyze Phoenix golf courses and visitor journey patterns. Let me search for the top courses and map their before/after visit behaviors.
```

### Tool Call 1: search_places

```json
{
  "geo_filter": {
    "type": "metro",
    "config": { "metro_name": "Phoenix-Mesa-Scottsdale, AZ" }
  },
  "category_ids": ["golf_course", "golf_practice_facility"],
  "limit": 10
}
```

### Tool Result 1:

```json
{
  "places": [
    {
      "id": "phx_golf_001",
      "name": "TPC Scottsdale - Stadium Course",
      "monthly_visits": 18500
    },
    {
      "id": "phx_golf_002",
      "name": "Troon North Golf Club",
      "monthly_visits": 14200
    },
    {
      "id": "phx_golf_003",
      "name": "Grayhawk Golf Club",
      "monthly_visits": 12800
    },
    {
      "id": "phx_golf_004",
      "name": "We-Ko-Pa Golf Club",
      "monthly_visits": 11600
    },
    {
      "id": "phx_golf_005",
      "name": "Talking Stick Golf Club",
      "monthly_visits": 10900
    }
  ],
  "total": 10
}
```

### Tool Call 2: get_visit_flows

```json
{
  "origin_place_ids": [
    "phx_golf_001",
    "phx_golf_002",
    "phx_golf_003",
    "phx_golf_004",
    "phx_golf_005"
  ],
  "time_range": { "start": "2024-01-01", "end": "2024-12-31" },
  "window_before_minutes": 120,
  "window_after_minutes": 120,
  "group_by": "category",
  "min_shared_visitors": 100
}
```

### Tool Result 2:

```json
{
  "flows": [
    {
      "origin_id": "phx_golf_001",
      "before_visit": [
        {
          "category": "convenience_store",
          "visitor_count": 3450,
          "percentage": 42.3
        },
        {
          "category": "gas_station",
          "visitor_count": 2890,
          "percentage": 35.4
        },
        { "category": "coffee_shop", "visitor_count": 1820, "percentage": 22.3 }
      ],
      "after_visit": [
        {
          "category": "convenience_store",
          "visitor_count": 5320,
          "percentage": 65.2
        },
        {
          "category": "gas_station",
          "visitor_count": 3440,
          "percentage": 42.1
        },
        {
          "category": "bar_restaurant",
          "visitor_count": 2560,
          "percentage": 31.4
        },
        {
          "category": "grocery_store",
          "visitor_count": 1230,
          "percentage": 15.1
        }
      ]
    }
  ]
}
```

### Message 3 (Agent)

```
Based on the Phoenix golf course analysis, here are the key path-to-purchase patterns:

**Top Golf Courses (Monthly Visits):**
1. TPC Scottsdale - Stadium Course: 18,500 visits
2. Troon North Golf Club: 14,200 visits
3. Grayhawk Golf Club: 12,800 visits

**Before Golf Course Visits:**
- 42.3% stop at convenience stores
- 35.4% stop at gas stations
- 22.3% stop at coffee shops

**After Golf Course Visits (Higher capture rate):**
- 65.2% stop at convenience stores
- 42.1% stop at gas stations
- 31.4% stop at bars/restaurants
- 15.1% stop at grocery stores

**Key Insight:** Post-round convenience store visits are 54% higher than pre-round (65.2% vs 42.3%), indicating golfers are more receptive to purchases after playing. Gas stations show similar patterns. This suggests optimal product placement timing is for the post-golf journey.
```

### Message 4 (User)

```
Perfect, this is exactly the pattern I expected. The post-round spike at convenience stores is significant. Archive this analysis.
```

### Message 5 (Agent)

```
Analysis archived. These Phoenix patterns provide a strong baseline for your Dallas golf launch strategy.
```

---

## Demo Script Execution

### User Message 1 (Type slowly)

```
I'm planning the Dallas launch strategy for our new golf line. Can you remind me what we learned about golfer behavior in Phoenix? Specifically the before and after visit patterns to convenience stores and gas stations?
```

**Expected Agent Behavior:**

1. Recognize reference to past discussion: "remind me", "we learned", "Phoenix"
2. Call `search_past_conversations` with keywords: `["golf", "Phoenix", "before", "after", "convenience", "gas"]`
3. Retrieve seeded conversation from 7 days ago
4. Extract and present the specific metrics requested

**UI Should Show:**

- Tool interaction block with tool name: "search_past_conversations"
- Tool parameters visible: keywords array, context settings
- Tool result with matched conversation snippet showing **[MATCH]** marker
- Agent response synthesizing the recalled information

### Expected Agent Response

```
Based on our Phoenix golf course analysis from last week, here's what we found:

**Before Golf Course Visits:**
- 42.3% of golfers stopped at convenience stores
- 35.4% stopped at gas stations

**After Golf Course Visits:**
- 65.2% stopped at convenience stores (54% increase from pre-round)
- 42.1% stopped at gas stations

The key insight was that post-round convenience store visits spiked significantly, suggesting golfers are much more receptive to purchases after playing. This pattern held across the top 5 Phoenix courses including TPC Scottsdale and Troon North.

This should inform your Dallas outlet prioritization - focus on convenience stores and gas stations along the post-golf journey routes.
```

### User Message 2 (Type slowly)

```
Great recall. What were the visit volumes for those top Phoenix courses?
```

**Expected Agent Behavior:**

1. Use context from previous retrieval (conversation still in context window)
2. Reference TPC Scottsdale (18,500), Troon North (14,200), Grayhawk (12,800) from memory
3. No need for another tool call - information already available

### Expected Agent Response

```
The top Phoenix courses we analyzed were:

1. TPC Scottsdale - Stadium Course: 18,500 monthly visits
2. Troon North Golf Club: 14,200 monthly visits
3. Grayhawk Golf Club: 12,800 monthly visits

These were the volume leaders that drove the path-to-purchase patterns we discussed.
```

---

## Success Criteria

✅ Agent successfully retrieves 7-day-old conversation using keyword search
✅ Tool interaction visible in UI with parameters and results
✅ Agent extracts exact percentages (42.3%, 65.2%, etc.) from matched conversation
✅ Agent synthesizes insights without user re-explaining context
✅ Second query answered from retained context without redundant tool call

---

## Failure Mode (Not Tested Here)

If no Phoenix conversations exist, agent should respond:

> "I don't have any previous conversations about Phoenix golf course analysis. Would you like me to run that analysis now?"
