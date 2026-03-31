from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.analysis import AnalysisResult, AnalysisStatus, AnalysisType
from app.models.datasource import DataSource
from app.services.session import get_session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Extract current user from session token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    session_data = await get_session(token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return session_data


class FunnelRequest(BaseModel):
    events: List[Dict[str, Any]]
    steps: Optional[List[str]] = None


class RFMPurchaseRequest(BaseModel):
    orders: List[Dict[str, Any]]


class ParseFileRequest(BaseModel):
    columns: List[str]
    sample_data: List[Dict[str, Any]]


@router.post("/funnel")
async def analyze_funnel(
    request: FunnelRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze conversion funnel from events data."""
    try:
        analyzer = FunnelAnalyzer(steps=request.steps)
        result = analyzer.analyze(
            events=request.events,
            user_id_field="user_id",
            event_type_field="event_type",
            timestamp_field="event_time",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rfm")
async def analyze_rfm(
    request: RFMPurchaseRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze customer RFM from orders data."""
    try:
        analyzer = RFMAnalyzer()
        result = analyzer.analyze(
            orders=request.orders,
            user_id_field="user_id",
            order_time_field="event_time",
            amount_field="amount",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-columns")
async def parse_columns(request: ParseFileRequest):
    """Auto-detect column mappings from file columns."""
    try:
        mappings = auto_detect_mappings(request.columns)
        return {
            "mappings": mappings,
            "suggested_mappings": mappings,
            "unmapped_columns": [
                col for col in request.columns
                if col not in mappings
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard overview metrics (mock for now)."""
    # In production, this would aggregate from real data
    return {
        "metrics": {
            "total_visits": 12847,
            "total_orders": 1284,
            "conversion_rate": 10.2,
            "total_customers": 3421,
            "avg_order_value": 256.8,
        },
        "changes": {
            "visits_change": 8.5,
            "orders_change": -2.3,
            "conversion_change": 15.2,
            "customers_change": 5.1,
        },
    }


@router.get("/result")
async def get_analysis_result(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get analysis result for a datasource. Poll this endpoint after upload."""
    # 验证用户认证
    # Note: For polling, we accept the request without strict auth for MVP
    # In production, add: user: dict = Depends(get_current_user)

    try:
        # 查询 datasource 是否存在
        datasource = await db.execute(
            select(DataSource).where(DataSource.id == datasource_id)
        )
        datasource_record = datasource.scalar_one_or_none()
        if not datasource_record:
            raise HTTPException(status_code=404, detail="DataSource not found")

        # 查询 funnel 和 rfm 结果
        results = {}
        status = "processing"

        funnel_result = await db.execute(
            select(AnalysisResult).where(
                AnalysisResult.datasource_id == datasource_id,
                AnalysisResult.analysis_type == AnalysisType.FUNNEL
            )
        )
        funnel_record = funnel_result.scalar_one_or_none()

        rfm_result = await db.execute(
            select(AnalysisResult).where(
                AnalysisResult.datasource_id == datasource_id,
                AnalysisResult.analysis_type == AnalysisType.RFM
            )
        )
        rfm_record = rfm_result.scalar_one_or_none()

        # 确定状态
        if funnel_record and rfm_record:
            if funnel_record.status == AnalysisStatus.FAILED or rfm_record.status == AnalysisStatus.FAILED:
                status = "failed"
                failed_record = funnel_record if funnel_record.status == AnalysisStatus.FAILED else rfm_record
                return {
                    "status": "failed",
                    "error": failed_record.error_message or "分析失败"
                }
            elif funnel_record.status == AnalysisStatus.COMPLETED and rfm_record.status == AnalysisStatus.COMPLETED:
                status = "completed"
                results["funnel_result"] = funnel_record.result_data
                results["rfm_result"] = rfm_record.result_data

                # 生成 overview
                results["overview"] = {
                    "total_orders": rfm_record.result_data.get("total_orders", 0),
                    "total_revenue": rfm_record.result_data.get("total_revenue", 0),
                    "avg_order_value": rfm_record.result_data.get("avg_order_value", 0),
                    "total_customers": rfm_record.result_data.get("total_customers", 0),
                }
            else:
                status = "processing"
        else:
            status = "processing"

        return {
            "status": status,
            **results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询分析结果失败: {str(e)}")
