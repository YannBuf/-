from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.llm import OpenAICompatibleLLM
from app.services.insight import InsightGenerator, NLUnderstanding
from app.config import get_settings
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter()
settings = get_settings()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    context: Optional[Dict[str, Any]] = None


class InsightRequest(BaseModel):
    insight_type: str  # "funnel", "rfm", "dashboard"
    data: Dict[str, Any]


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Process chat message and return AI response."""
    try:
        # Initialize LLM and insight generator
        llm = OpenAICompatibleLLM(
            api_url=settings.LLM_API_URL,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
        )
        insight_gen = InsightGenerator(llm)
        nl_parser = NLUnderstanding(llm)

        # Parse user intent
        parsed = await nl_parser.parse(request.message)

        # Build context-aware response
        if request.context:
            if parsed.get("query_type") == "funnel_analysis":
                response_text = await insight_gen.generate_funnel_insight(request.context.get("funnel_data", {}))
            elif parsed.get("query_type") == "rfm_analysis":
                response_text = await insight_gen.generate_rfm_insight(request.context.get("rfm_data", {}))
            elif parsed.get("query_type") == "general":
                # Generate a general response based on context
                response_text = await insight_gen.generate_dashboard_summary(
                    request.context.get("metrics", {}),
                    request.context.get("funnel_data", {}),
                    request.context.get("rfm_data", {}),
                )
            else:
                response_text = "我理解你想了解这方面的数据，让我为你分析一下。"
        else:
            response_text = "你好！我是你的电商数据助手。有什么关于生意的问题可以问我，比如\"最近转化率怎么样？\"或者\"有哪些高价值客户？\""

        return {
            "response": response_text,
            "parsed_intent": parsed,
        }
    except Exception as e:
        # Return a fallback response if LLM fails
        return {
            "response": f"抱歉，我现在无法处理你的请求。请稍后再试。",
            "error": str(e),
        }


@router.post("/insight")
async def generate_insight(
    request: InsightRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate AI insight for specific analysis data."""
    try:
        llm = OpenAICompatibleLLM(
            api_url=settings.LLM_API_URL,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
        )
        insight_gen = InsightGenerator(llm)

        if request.insight_type == "funnel":
            insight = await insight_gen.generate_funnel_insight(request.data)
        elif request.insight_type == "rfm":
            insight = await insight_gen.generate_rfm_insight(request.data)
        elif request.insight_type == "dashboard":
            insight = await insight_gen.generate_dashboard_summary(
                request.data.get("metrics", {}),
                request.data.get("funnel", {}),
                request.data.get("rfm", {}),
            )
        else:
            insight = "数据已加载，请告诉我你想了解什么。"

        return {"insight": insight}
    except Exception as e:
        return {"insight": f"抱歉，生成洞察时出现错误。"}
