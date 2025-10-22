from fastapi import APIRouter, HTTPException, Depends

from modules.open_ai.service import OpenAIService
from modules.open_ai.dependencies import get_ai_service
from modules.open_ai.schemas import SummarizeRequest, SummarizeResponse

router = APIRouter(prefix="/ai", tags=["AI TEST"])


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_text(
    data: SummarizeRequest,
    ai_service: OpenAIService = Depends(get_ai_service),
):
    summary = await ai_service.summarize_text(data.text)

    if summary.startswith("Ошибка"):
        raise HTTPException(status_code=500, detail=summary)

    return SummarizeResponse(summary=summary)