"""seed personas table

Revision ID: seed_personas
Revises: add_letta_agent_id
Create Date: 2025-02-14
"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision: str = "seed_personas"
down_revision: Union[str, None] = "add_letta_agent_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    personas = [
        {
            "id": str(uuid4()),
            "persona_handle": "director_real_estate_qsr",
            "persona_character_name": "sarah",
            "industry": "QSR / Fast Casual",
            "professional_role": "Director of Real Estate",
            "description": "Director of Real Estate for a 600-location fast-casual/QSR chain. Started as a commercial broker, moved in-house to lead site selection, relocations, and lease renewals. Small team of real estate managers and analysts; partners closely with Finance and Operations.",
            "typical_kpis": "New store performance vs pro forma in year 1–2 (traffic and revenue); Portfolio productivity (average sales per store, closures vs openings); Hit rate of 'good boxes' vs underperforming locations; Speed and quality of deal flow (qualified sites approved per quarter)",
            "typical_motivations": "Avoid a string of bad calls that damage credibility and P&L; Show that real estate decisions are a growth lever, not just a cost center; Win internal debates with Finance/Ops using hard data, not anecdotes; Build a repeatable, defensible playbook for expansion and infill",
            "quintessential_queries": "Site selection vs comps: Compare weekly and monthly visit trends, trade areas, and visitor demographics for proposed locations against top-performing stores. Cannibalization risk: Estimate impact of opening new stores on existing locations. Portfolio ranking: Rank current store locations by visit trends and identify at-risk locations.",
        },
        {
            "id": str(uuid4()),
            "persona_handle": "consumer_insights_tobacco",
            "persona_character_name": "daniel",
            "industry": "Tobacco / CPG",
            "professional_role": "Director of Consumer Insights & Activation",
            "description": "Director of Consumer Insights & Activation for a major tobacco company. Previously led consumer insights in beer/spirits; experienced with segmentation, path-to-purchase, and trade activation. Owns where/when/how to launch new products, and how to align launches with channels and moments.",
            "typical_kpis": "New product launch performance: trial, repeat, and share in target segments within 6–12 months; Channel and outlet strategy quality: velocity per point of distribution, not just distribution breadth; ROI on shopper and trade marketing programs; Accuracy of 'market map' and recommendations to senior leadership",
            "typical_motivations": "De-risk launches with concrete behavioral data rather than generic survey panels; Find real-world micro-moments when high-value consumers are most receptive; Demonstrate that precise geo + outlet strategy beats blanket promotions; Build a track record of picking the right locations and channels for launches",
            "quintessential_queries": "Golf path-to-purchase mapping: Identify golf courses and map where visitors go before/after. Priority outlet ranking: Rank convenience stores and outlets by overlap with golf course visitors. Post-launch monitoring: Track whether prioritized outlets are capturing increasing share of target visitors.",
        },
    ]

    op.bulk_insert(
        sa.table(
            "persona",
            sa.column("id", sa.String),
            sa.column("persona_handle", sa.String),
            sa.column("persona_character_name", sa.String),
            sa.column("industry", sa.String),
            sa.column("professional_role", sa.String),
            sa.column("description", sa.Text),
            sa.column("typical_kpis", sa.Text),
            sa.column("typical_motivations", sa.Text),
            sa.column("quintessential_queries", sa.Text),
        ),
        personas,
    )


def downgrade() -> None:
    op.execute("DELETE FROM persona")
