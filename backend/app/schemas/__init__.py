"""AdTicks schemas package."""
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.keyword import KeywordCreate, KeywordResponse, RankingResponse
from app.schemas.prompt import PromptResponse, ResponseResponse, MentionResponse
from app.schemas.score import ScoreResponse
from app.schemas.recommendation import RecommendationResponse
from app.schemas.gsc import GSCDataResponse
from app.schemas.ads import AdsDataResponse
from app.schemas.insight import InsightResponse

__all__ = [
    "UserCreate", "UserLogin", "UserResponse", "Token",
    "ProjectCreate", "ProjectResponse", "ProjectUpdate",
    "KeywordCreate", "KeywordResponse", "RankingResponse",
    "PromptResponse", "ResponseResponse", "MentionResponse",
    "ScoreResponse", "RecommendationResponse",
    "GSCDataResponse", "AdsDataResponse", "InsightResponse",
]
