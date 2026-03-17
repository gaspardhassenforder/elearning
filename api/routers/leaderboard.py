from fastapi import APIRouter, Depends
from api.auth import LearnerContext, get_current_learner
from api import leaderboard_service
from api.models import LeaderboardEntry

learner_router = APIRouter()

@learner_router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(learner: LearnerContext = Depends(get_current_learner)):
    return await leaderboard_service.get_company_leaderboard(learner.company_id)
