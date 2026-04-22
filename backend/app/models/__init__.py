"""
AdTicks — models package.

Importing all models here ensures they are registered with SQLAlchemy's
metadata before Alembic or the lifespan event calls create_all.
"""

from app.models.aeo import (
    AEOVisibility,
    AEOTrends,
    SnippetTracking,
    PAA,
    ContentRecommendation,
    GeneratedFAQ,
)
from app.models.ads import AdsData
from app.models.cluster import Cluster
from app.models.competitor import Competitor
from app.models.geo import (
    Location,
    LocalRank,
    Review,
    ReviewSummary,
    Citation,
)
from app.models.gsc import GSCData
from app.models.keyword import Keyword, Ranking
from app.models.project import Project
from app.models.prompt import Mention, Prompt, Response
from app.models.recommendation import Recommendation
from app.models.score import Score
from app.models.user import User

__all__ = [
    "User",
    "Project",
    "Competitor",
    "Keyword",
    "Ranking",
    "Prompt",
    "Response",
    "Mention",
    "Cluster",
    "Score",
    "Recommendation",
    "GSCData",
    "AdsData",
    "AEOVisibility",
    "AEOTrends",
    "SnippetTracking",
    "PAA",
    "ContentRecommendation",
    "GeneratedFAQ",
    "Location",
    "LocalRank",
    "Review",
    "ReviewSummary",
    "Citation",
]
