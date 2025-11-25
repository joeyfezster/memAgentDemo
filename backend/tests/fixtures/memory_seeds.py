from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import conversation as conversation_crud
from app.models.conversation import Conversation
from app.models.types import MessageRole
from app.models.user import User


async def seed_past_conversations_for_sarah(
    session: AsyncSession, user: User
) -> list[Conversation]:
    now = datetime.now(UTC)
    conversations = []

    conv1 = await conversation_crud.create_conversation(session, user_id=user.id)
    conv1.title = "Site evaluation - Westgate Shopping Center"
    conv1.created_at = now - timedelta(days=7)

    messages_conv1 = [
        (
            MessageRole.USER,
            "I need to evaluate a site at the Westgate Shopping Center in Austin. Can you help me compare it against our top performing locations?",
        ),
        (
            MessageRole.AGENT,
            "I'll analyze the Westgate Shopping Center site for you. Let me search for similar locations and gather trade area data to compare against your top performers.",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_location_details",
                "tool_input": {
                    "location": "Westgate Shopping Center Austin",
                    "include_demographics": True,
                },
            },
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_benchmark_locations",
                "tool_input": {
                    "market": "Austin",
                    "performance_tier": "top_quartile",
                    "limit": 5,
                },
            },
        ),
        (
            MessageRole.USER,
            "What does the trade area look like? I'm particularly interested in the demographics and visitor profiles.",
        ),
        (
            MessageRole.AGENT,
            "Based on the trade area analysis, the Westgate location shows strong demographics with median household income of $78K and high concentration of families with children. Visitor profile indicates 65% are regular weekly visitors, which is above your portfolio average of 58%.",
        ),
        (MessageRole.USER, "How does foot traffic compare to our benchmark stores?"),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_foot_traffic_trends",
                "tool_input": {
                    "location_id": "westgate_austin",
                    "time_period": "12_months",
                    "compare_to_benchmarks": True,
                },
            },
        ),
        (
            MessageRole.AGENT,
            "Monthly foot traffic at Westgate Shopping Center averages 42,000 visits, which is 15% higher than your top quartile benchmark of 36,500 visits. Peak hours align well with lunch and dinner dayparts typical for QSR operations.",
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

    conv2 = await conversation_crud.create_conversation(session, user_id=user.id)
    conv2.title = "Cannibalization risk for Dallas infill"
    conv2.created_at = now - timedelta(days=3)

    messages_conv2 = [
        (
            MessageRole.USER,
            "We're considering opening a new location in Dallas near two existing stores. Can you analyze the cannibalization risk?",
        ),
        (
            MessageRole.AGENT,
            "I'll analyze the trade area overlap between the proposed location and your existing Dallas stores to estimate cannibalization impact.",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "analyze_cannibalization",
                "tool_input": {
                    "proposed_location": "Dallas infill site",
                    "existing_stores": ["store_A", "store_B"],
                    "radius_miles": 5,
                },
            },
        ),
        (MessageRole.USER, "What's the overlap percentage?"),
        (
            MessageRole.AGENT,
            "The trade area analysis shows 28% overlap with Store A (3.2 miles away) and 15% overlap with Store B (4.8 miles away). Combined cannibalization risk is estimated at 18-22% of existing store traffic, but the location should capture significant incremental traffic from underserved areas to the south.",
        ),
        (
            MessageRole.USER,
            "What's the net impact on total visits across all three locations?",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "calculate_network_impact",
                "tool_input": {
                    "stores": ["store_A", "store_B", "proposed_infill"],
                    "metric": "total_visits",
                },
            },
        ),
        (
            MessageRole.AGENT,
            "With the new store, total network visits would increase by approximately 35%, from 85,000 to 115,000 monthly visits across all three locations. The incremental lift more than offsets the cannibalization effect, suggesting this is a net-positive infill opportunity.",
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

    await session.commit()
    await session.refresh(conv2)
    conversations.append(conv2)

    conv3 = await conversation_crud.create_conversation(session, user_id=user.id)
    conv3.title = "Portfolio health check - underperforming stores"
    conv3.created_at = now - timedelta(days=1)

    messages_conv3 = [
        (
            MessageRole.USER,
            "I need to review our underperforming stores in the Dallas market. Can you rank them by key metrics?",
        ),
        (
            MessageRole.AGENT,
            "I'll rank your Dallas market stores by visit trends, frequency, and performance vs market benchmarks.",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "rank_stores_by_performance",
                "tool_input": {
                    "market": "Dallas",
                    "metrics": ["visit_trends", "frequency", "benchmark_comparison"],
                    "min_threshold": -10,
                },
            },
        ),
        (
            MessageRole.USER,
            "Which locations should we consider for closure or relocation?",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "identify_closure_candidates",
                "tool_input": {
                    "market": "Dallas",
                    "criteria": [
                        "declining_visits",
                        "weak_frequency",
                        "below_benchmark",
                    ],
                },
            },
        ),
        (
            MessageRole.AGENT,
            "Three locations show concerning trends: Store #458 (Richardson) has declining visits (-12% YoY), Store #502 (Garland) shows weakening frequency metrics, and Store #334 (Oak Cliff) underperforms category benchmarks by 25%. These are candidates for relocation analysis or lease non-renewal consideration.",
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

    conv4 = await conversation_crud.create_conversation(session, user_id=user.id)
    conv4.title = "Lease renewal decision - Store 458"
    conv4.created_at = now - timedelta(hours=2)

    messages_conv4 = [
        (
            MessageRole.USER,
            "The lease is coming up for renewal on Store 458 in Richardson. Should we renew based on recent foot traffic trends?",
        ),
        (
            MessageRole.AGENT,
            "Let me analyze the recent foot traffic trends and competitive dynamics for Store 458.",
        ),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "get_store_performance_trends",
                "tool_input": {
                    "store_id": "458",
                    "time_periods": ["12mo", "24mo"],
                    "include_demographics": True,
                },
            },
        ),
        (MessageRole.USER, "What do the numbers show?"),
        (
            MessageRole.AGENT,
            "",
            {
                "tool_name": "analyze_trade_area_changes",
                "tool_input": {
                    "store_id": "458",
                    "metrics": ["income", "employment", "population"],
                },
            },
        ),
        (
            MessageRole.AGENT,
            "Store 458 shows persistent decline: visits down 12% YoY and 8% vs 2-year baseline. Trade area demographics have weakened with median income dropping and office worker population declining 15% due to corporate relocations. Recommendation: Pursue non-renewal and reallocate to higher-growth Richardson submarket locations identified in our site pipeline.",
        ),
    ]

    for role, content, *metadata in messages_conv4:
        tool_metadata = metadata[0] if metadata else None
        await conversation_crud.add_message_to_conversation(
            session,
            conv4.id,
            role=role.value,
            content=content,
            tool_metadata=tool_metadata,
        )

    await session.commit()
    await session.refresh(conv4)
    conversations.append(conv4)

    return conversations
