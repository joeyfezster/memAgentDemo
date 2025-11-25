"""Persona-specific conversation seeds for demo purposes"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.crud import conversation as conversation_crud
from app.models.conversation import Conversation
from app.models.types import MessageRole
from app.models.user import User


async def seed_conversations_for_daniel(
    session: AsyncSession, user: User
) -> list[Conversation]:
    """Seed golf-focused conversations for Daniel persona (tobacco consumer insights)"""
    now = datetime.now(UTC)
    conversations = []

    # Conversation 1: Phoenix Golf Course Path-to-Purchase Analysis (7 days ago)
    conv1 = await conversation_crud.create_conversation(session, user_id=user.id)
    conv1.title = "Phoenix Golf Course Path-to-Purchase Analysis"
    conv1.created_at = now - timedelta(days=7)

    messages_conv1 = [
        (
            MessageRole.USER,
            "For the Phoenix metro area, identify the top 10 golf courses by visit volume over the last 12 months, then map where their visitors most frequently go immediately before and after a course visit. Break the results down by venue type - I need to understand the path-to-purchase behavior.",
        ),
        (
            MessageRole.AGENT,
            "I'll analyze Phoenix golf courses and visitor journey patterns. Let me search for the top courses and map their before/after visit behaviors.",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "search_places",
                "tool_input": {
                    "geo_filter": {
                        "type": "metro",
                        "config": {"metro_name": "Phoenix-Mesa-Scottsdale, AZ"},
                    },
                    "category_ids": ["golf_course", "golf_practice_facility"],
                    "limit": 10,
                },
                "tool_result": {
                    "places": [
                        {
                            "id": "phx_golf_001",
                            "name": "TPC Scottsdale - Stadium Course",
                            "monthly_visits": 18500,
                        },
                        {
                            "id": "phx_golf_002",
                            "name": "Troon North Golf Club",
                            "monthly_visits": 14200,
                        },
                        {
                            "id": "phx_golf_003",
                            "name": "Grayhawk Golf Club",
                            "monthly_visits": 12800,
                        },
                        {
                            "id": "phx_golf_004",
                            "name": "We-Ko-Pa Golf Club",
                            "monthly_visits": 11600,
                        },
                        {
                            "id": "phx_golf_005",
                            "name": "Talking Stick Golf Club",
                            "monthly_visits": 10900,
                        },
                    ],
                    "total": 10,
                },
            },
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_visit_flows",
                "tool_input": {
                    "origin_place_ids": [
                        "phx_golf_001",
                        "phx_golf_002",
                        "phx_golf_003",
                        "phx_golf_004",
                        "phx_golf_005",
                    ],
                    "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
                    "window_before_minutes": 120,
                    "window_after_minutes": 120,
                    "group_by": "category",
                    "min_shared_visitors": 100,
                },
                "tool_result": {
                    "flows": [
                        {
                            "origin_id": "phx_golf_001",
                            "before_visit": [
                                {
                                    "category": "convenience_store",
                                    "visitor_count": 3450,
                                    "percentage": 42.3,
                                },
                                {
                                    "category": "gas_station",
                                    "visitor_count": 2890,
                                    "percentage": 35.4,
                                },
                                {
                                    "category": "coffee_shop",
                                    "visitor_count": 1820,
                                    "percentage": 22.3,
                                },
                            ],
                            "after_visit": [
                                {
                                    "category": "convenience_store",
                                    "visitor_count": 5320,
                                    "percentage": 65.2,
                                },
                                {
                                    "category": "gas_station",
                                    "visitor_count": 3440,
                                    "percentage": 42.1,
                                },
                                {
                                    "category": "bar_restaurant",
                                    "visitor_count": 2560,
                                    "percentage": 31.4,
                                },
                                {
                                    "category": "grocery_store",
                                    "visitor_count": 1230,
                                    "percentage": 15.1,
                                },
                            ],
                        }
                    ]
                },
            },
        ),
        (
            MessageRole.AGENT,
            "Based on the Phoenix golf course analysis, here are the key path-to-purchase patterns:\n\n**Top Golf Courses (Monthly Visits):**\n1. TPC Scottsdale - Stadium Course: 18,500 visits\n2. Troon North Golf Club: 14,200 visits\n3. Grayhawk Golf Club: 12,800 visits\n\n**Before Golf Course Visits:**\n- 42.3% stop at convenience stores\n- 35.4% stop at gas stations\n- 22.3% stop at coffee shops\n\n**After Golf Course Visits (Higher capture rate):**\n- 65.2% stop at convenience stores\n- 42.1% stop at gas stations\n- 31.4% stop at bars/restaurants\n- 15.1% stop at grocery stores\n\n**Key Insight:** Post-round convenience store visits are 54% higher than pre-round (65.2% vs 42.3%), indicating golfers are more receptive to purchases after playing. Gas stations show similar patterns. This suggests optimal product placement timing is for the post-golf journey.",
        ),
        (
            MessageRole.USER,
            "Perfect, this is exactly the pattern I expected. The post-round spike at convenience stores is significant. Archive this analysis.",
        ),
        (
            MessageRole.AGENT,
            "Analysis archived. These Phoenix patterns provide a strong baseline for your Dallas golf launch strategy.",
        ),
    ]

    for role, content, *metadata in messages_conv1:
        tool_metadata = metadata[0] if metadata else None
        await conversation_crud.add_message_to_conversation(
            session,
            conv1.id,
            role=role.value,
            content=content,
            tool_metadata=tool_metadata,
        )

    await session.commit()
    await session.refresh(conv1)
    conversations.append(conv1)

    # Conversation 2: Topgolf Scottsdale Outlet Prioritization (3 days ago)
    conv2 = await conversation_crud.create_conversation(session, user_id=user.id)
    conv2.title = "Topgolf Scottsdale Outlet Prioritization"
    conv2.created_at = now - timedelta(days=3)

    messages_conv2 = [
        (
            MessageRole.USER,
            "I want to analyze Topgolf Scottsdale as a potential anchor location for our golf line. Find nearby convenience stores within a 10-minute drive and rank them by overlap with Topgolf visitors.",
        ),
        (
            MessageRole.AGENT,
            "I'll analyze Topgolf Scottsdale and identify high-overlap convenience stores in the surrounding area.",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "search_places",
                "tool_input": {
                    "geo_filter": {
                        "type": "point_radius",
                        "config": {"lat": 33.4673, "lon": -111.9564, "radius_km": 8},
                    },
                    "text_query": "Topgolf Scottsdale",
                    "limit": 1,
                },
                "tool_result": {
                    "places": [
                        {
                            "id": "topgolf_scottsdale_001",
                            "name": "Topgolf Scottsdale",
                            "lat": 33.4673,
                            "lon": -111.9564,
                        }
                    ]
                },
            },
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_place_summary",
                "tool_input": {
                    "place_ids": ["topgolf_scottsdale_001"],
                    "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
                    "granularity": "monthly",
                    "include_benchmark": True,
                },
                "tool_result": {
                    "summaries": [
                        {
                            "place_id": "topgolf_scottsdale_001",
                            "metrics": {
                                "monthly_visits": 28500,
                                "unique_visitors": 19200,
                                "visit_frequency": 1.48,
                            },
                        }
                    ]
                },
            },
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "search_places",
                "tool_input": {
                    "geo_filter": {
                        "type": "point_radius",
                        "config": {"lat": 33.4673, "lon": -111.9564, "radius_km": 8},
                    },
                    "category_ids": ["convenience_store"],
                    "limit": 10,
                },
                "tool_result": {
                    "places": [
                        {
                            "id": "cvs_001",
                            "name": "7-Eleven - Scottsdale Rd",
                            "lat": 33.4692,
                            "lon": -111.9501,
                        },
                        {
                            "id": "cvs_002",
                            "name": "Circle K - Greenway Pkwy",
                            "lat": 33.471,
                            "lon": -111.9488,
                        },
                        {
                            "id": "cvs_003",
                            "name": "QuikTrip - Loop 101",
                            "lat": 33.4621,
                            "lon": -111.9612,
                        },
                    ]
                },
            },
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_profile_and_overlap",
                "tool_input": {
                    "base_entities": [
                        {"type": "place", "id": "topgolf_scottsdale_001"}
                    ],
                    "comparison_entities": [
                        {"type": "place", "id": "cvs_001"},
                        {"type": "place", "id": "cvs_002"},
                        {"type": "place", "id": "cvs_003"},
                    ],
                    "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
                    "dimensions": ["age", "income"],
                },
                "tool_result": {
                    "overlaps": [
                        {
                            "entity": {"type": "place", "id": "cvs_001"},
                            "overlap_index": 78.4,
                            "shared_visitors": 15040,
                        },
                        {
                            "entity": {"type": "place", "id": "cvs_002"},
                            "overlap_index": 71.2,
                            "shared_visitors": 13664,
                        },
                        {
                            "entity": {"type": "place", "id": "cvs_003"},
                            "overlap_index": 65.8,
                            "shared_visitors": 12636,
                        },
                    ]
                },
            },
        ),
        (
            MessageRole.AGENT,
            "Here's the Topgolf Scottsdale outlet analysis:\n\n**Topgolf Scottsdale Performance:**\n- Monthly visits: 28,500\n- Unique visitors: 19,200\n- Visit frequency: 1.48x per month\n\n**Top 3 Convenience Stores by Visitor Overlap:**\n\n1. **7-Eleven - Scottsdale Rd**\n   - Overlap index: 78.4%\n   - Shared visitors: 15,040 monthly\n   - Distance: 0.8 miles northeast\n\n2. **Circle K - Greenway Pkwy**\n   - Overlap index: 71.2%\n   - Shared visitors: 13,664 monthly\n   - Distance: 1.1 miles north\n\n3. **QuikTrip - Loop 101**\n   - Overlap index: 65.8%\n   - Shared visitors: 12,636 monthly\n   - Distance: 1.4 miles south\n\n**Recommendation:** The 7-Eleven on Scottsdale Rd should be your #1 priority outlet - it captures 78% overlap with Topgolf visitors and sees 15K shared visitors per month. This is an ideal first-wave placement location.",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "manage_user_memory",
                "tool_input": {
                    "operation": "add_poi",
                    "place_id": "topgolf_scottsdale_001",
                    "place_name": "Topgolf Scottsdale",
                    "notes": "Key anchor location for golf line launch. 28.5K monthly visits, 19.2K unique visitors. 7-Eleven Scottsdale Rd (78% overlap) is top priority outlet.",
                },
                "tool_result": {
                    "success": True,
                    "operation": "add_poi",
                    "place_id": "topgolf_scottsdale_001",
                    "message": "Stored place: Topgolf Scottsdale",
                },
            },
        ),
        (
            MessageRole.USER,
            "Excellent. This 7-Eleven location should definitely be in our first wave. Let's track this as a priority.",
        ),
        (
            MessageRole.AGENT,
            "I've stored Topgolf Scottsdale in your memory with the key metrics and the top outlet priority. This will help us track performance post-launch.",
        ),
    ]

    for role, content, *metadata in messages_conv2:
        tool_metadata = metadata[0] if metadata else None
        await conversation_crud.add_message_to_conversation(
            session,
            conv2.id,
            role=role.value,
            content=content,
            tool_metadata=tool_metadata,
        )

    # Add POI to user's memory after seeding conversation
    user.add_poi(
        place_id="topgolf_scottsdale_001",
        place_name="Topgolf Scottsdale",
        notes="Key anchor location for golf line launch. 28.5K monthly visits, 19.2K unique visitors. 7-Eleven Scottsdale Rd (78% overlap) is top priority outlet.",
        conversation_id=conv2.id,
        message_id="seeded_msg_poi",
    )

    # Mark the JSONB field as modified so SQLAlchemy detects the change
    flag_modified(user, "memory_document")

    await session.commit()
    await session.refresh(conv2)
    conversations.append(conv2)

    # Conversation 3: Austin Golf Launch Performance Review (10 days ago)
    conv3 = await conversation_crud.create_conversation(session, user_id=user.id)
    conv3.title = "Austin Golf Launch Performance Review"
    conv3.created_at = now - timedelta(days=10)

    messages_conv3 = [
        (
            MessageRole.USER,
            "We launched the golf line in Austin 6 months ago. Pull the performance data for our top 3 outlets near golf courses and compare to initial projections.",
        ),
        (
            MessageRole.AGENT,
            "I'll analyze your Austin golf line outlets and compare actual performance to projections.",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "search_places",
                "tool_input": {
                    "geo_filter": {
                        "type": "metro",
                        "config": {"metro_name": "Austin-Round Rock, TX"},
                    },
                    "portfolio_tags": ["our_stores", "golf_line_launch"],
                    "limit": 3,
                },
                "tool_result": {
                    "places": [
                        {
                            "id": "austin_outlet_001",
                            "name": "Circle K - Barton Creek",
                            "tags": ["golf_line_launch"],
                        },
                        {
                            "id": "austin_outlet_002",
                            "name": "7-Eleven - Lost Creek",
                            "tags": ["golf_line_launch"],
                        },
                        {
                            "id": "austin_outlet_003",
                            "name": "Stripes - Great Hills",
                            "tags": ["golf_line_launch"],
                        },
                    ]
                },
            },
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_place_summary",
                "tool_input": {
                    "place_ids": [
                        "austin_outlet_001",
                        "austin_outlet_002",
                        "austin_outlet_003",
                    ],
                    "time_range": {"start": "2024-06-01", "end": "2024-11-30"},
                    "granularity": "monthly",
                    "include_benchmark": True,
                },
                "tool_result": {
                    "summaries": [
                        {
                            "place_id": "austin_outlet_001",
                            "metrics": {"monthly_visits": 9800},
                            "trends": {"mom_change": 8.3, "classification": "Growing"},
                        },
                        {
                            "place_id": "austin_outlet_002",
                            "metrics": {"monthly_visits": 8600},
                            "trends": {"mom_change": 6.1, "classification": "Stable"},
                        },
                        {
                            "place_id": "austin_outlet_003",
                            "metrics": {"monthly_visits": 7200},
                            "trends": {"mom_change": 3.2, "classification": "Stable"},
                        },
                    ]
                },
            },
        ),
        (
            MessageRole.AGENT,
            "Here's your Austin golf line performance review:\n\n**Circle K - Barton Creek** (Top Performer)\n- Current monthly visits: 9,800\n- Month-over-month growth: +8.3%\n- Classification: Growing\n- Performance vs projection: Exceeded by 18%\n\n**7-Eleven - Lost Creek**\n- Current monthly visits: 8,600\n- Month-over-month growth: +6.1%\n- Classification: Stable\n- Performance vs projection: Met expectations (+2%)\n\n**Stripes - Great Hills**\n- Current monthly visits: 7,200\n- Month-over-month growth: +3.2%\n- Classification: Stable\n- Performance vs projection: Slight underperformance (-5%)\n\n**Key Finding:** Outlets within 2 miles of high-volume golf courses (Barton Creek Golf Club) are significantly outperforming those with weaker golf associations. The proximity and overlap with golfers drives sustained growth.",
        ),
        (
            MessageRole.USER,
            "This confirms the golf correlation. The Barton Creek location is our proof point that targeting high-overlap outlets works.",
        ),
        (
            MessageRole.AGENT,
            "Absolutely. The Austin data validates the golf-proximity strategy - outlets with 70%+ overlap with course visitors show 15-20% better performance than general market placements.",
        ),
    ]

    for role, content, *metadata in messages_conv3:
        tool_metadata = metadata[0] if metadata else None
        await conversation_crud.add_message_to_conversation(
            session,
            conv3.id,
            role=role.value,
            content=content,
            tool_metadata=tool_metadata,
        )

    await session.commit()
    await session.refresh(conv3)
    conversations.append(conv3)

    return conversations
