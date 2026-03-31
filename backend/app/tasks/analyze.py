from celery_app import celery_app
from app.services.funnel import FunnelAnalyzer
from app.services.rfm import RFMAnalyzer
from app.models.analysis import AnalysisResult, AnalysisStatus, AnalysisType
from app.database import SessionLocal
import json


def save_analysis_result(datasource_id: int, user_id: int, analysis_type: AnalysisType, result_data: dict, status: AnalysisStatus = AnalysisStatus.COMPLETED, error_message: str = None):
    """保存分析结果到数据库"""
    db = SessionLocal()
    try:
        # 查找已存在的记录或创建新记录
        existing = db.query(AnalysisResult).filter(
            AnalysisResult.datasource_id == datasource_id,
            AnalysisResult.analysis_type == analysis_type
        ).first()

        if existing:
            existing.status = status
            existing.result_data = result_data
            existing.error_message = error_message
        else:
            analysis_result = AnalysisResult(
                datasource_id=datasource_id,
                user_id=user_id,
                analysis_type=analysis_type,
                status=status,
                result_data=result_data,
                error_message=error_message
            )
            db.add(analysis_result)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.analyze.run_funnel_analysis")
def run_funnel_analysis(data: list, user_id: int, datasource_id: int = None) -> dict:
    """
    Run funnel analysis asynchronously.

    Args:
        data: List of event records
        user_id: User ID for audit logging
        datasource_id: DataSource ID for storing results

    Returns:
        Analysis results
    """
    try:
        analyzer = FunnelAnalyzer()
        result = analyzer.analyze(data)

        if datasource_id:
            save_analysis_result(
                datasource_id=datasource_id,
                user_id=user_id,
                analysis_type=AnalysisType.FUNNEL,
                result_data=result
            )

        return {
            "user_id": user_id,
            "analysis_type": "funnel",
            "result": result,
        }
    except Exception as e:
        if datasource_id:
            save_analysis_result(
                datasource_id=datasource_id,
                user_id=user_id,
                analysis_type=AnalysisType.FUNNEL,
                result_data=None,
                status=AnalysisStatus.FAILED,
                error_message=str(e)
            )
        raise


@celery_app.task(name="app.tasks.analyze.run_rfm_analysis")
def run_rfm_analysis(data: list, user_id: int, datasource_id: int = None) -> dict:
    """
    Run RFM analysis asynchronously.

    Args:
        data: List of order records
        user_id: User ID for audit logging
        datasource_id: DataSource ID for storing results

    Returns:
        Analysis results
    """
    try:
        analyzer = RFMAnalyzer()
        result = analyzer.analyze(data)

        if datasource_id:
            save_analysis_result(
                datasource_id=datasource_id,
                user_id=user_id,
                analysis_type=AnalysisType.RFM,
                result_data=result
            )

        return {
            "user_id": user_id,
            "analysis_type": "rfm",
            "result": result,
        }
    except Exception as e:
        if datasource_id:
            save_analysis_result(
                datasource_id=datasource_id,
                user_id=user_id,
                analysis_type=AnalysisType.RFM,
                result_data=None,
                status=AnalysisStatus.FAILED,
                error_message=str(e)
            )
        raise
