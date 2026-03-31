from typing import Dict, Any, List, Optional
from app.services.llm import BaseLLM
import json


class InsightGenerator:
    """
    Generate human-readable insights from analysis results.

    Uses LLM to convert data metrics into actionable recommendations.
    """

    SYSTEM_PROMPT = """你是一个专业的电商数据分析师。你的任务是：
1. 分析用户提供的业务数据
2. 用通俗易懂的语言解释数据含义
3. 指出关键发现和异常
4. 提供具体的优化建议

请用中文回答。回答要简洁、专业、有洞察力。"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def generate_funnel_insight(self, funnel_data: Dict[str, Any]) -> str:
        """Generate insight for funnel analysis results."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""分析以下漏斗数据，给出简洁的洞察和建议：

{self._format_funnel_data(funnel_data)}

请用2-3句话总结：1) 最大问题在哪 2) 具体建议是什么。"""},
        ]

        response = await self.llm.chat(messages, temperature=0.5, max_tokens=300)
        return response

    async def generate_rfm_insight(self, rfm_data: Dict[str, Any]) -> str:
        """Generate insight for RFM analysis results."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""分析以下客户分层数据，给出简洁的洞察和建议：

{self._format_rfm_data(rfm_data)}

请用2-3句话总结：1) 客户整体质量如何 2) 重点该关注哪类客户 3) 如何提升客户价值。"""},
        ]

        response = await self.llm.chat(messages, temperature=0.5, max_tokens=300)
        return response

    async def generate_dashboard_summary(
        self,
        metrics: Dict[str, Any],
        funnel: Dict[str, Any],
        rfm: Dict[str, Any],
    ) -> str:
        """Generate overall dashboard summary."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"""作为电商数据分析师，请总结以下数据整体情况：

【核心指标】
{self._format_metrics(metrics)}

【转化漏斗】
{self._format_funnel_data(funnel)}

【客户分层】
{self._format_rfm_data(rfm)}

请用3-4句话总结：
1. 本月整体表现如何
2. 最大的机会或风险是什么
3. 最应该关注的一个行动点是什么"""},
        ]

        response = await self.llm.chat(messages, temperature=0.5, max_tokens=400)
        return response

    def _format_funnel_data(self, data: Dict[str, Any]) -> str:
        """Format funnel data for LLM prompt."""
        lines = []
        for step in data.get("funnel", []):
            step_name = step.get("step", "")
            count = step.get("user_count", 0)
            rate = step.get("conversion_rate", 0)
            lines.append(f"- {step_name}: {count}人, 转化率{rate*100:.1f}%")
        return "\n".join(lines)

    def _format_rfm_data(self, data: Dict[str, Any]) -> str:
        """Format RFM data for LLM prompt."""
        summary = data.get("summary", {})
        distribution = data.get("segment_distribution", {})

        lines = [
            f"总客户数: {summary.get('total_customers', 0)}",
            f"高价值客户: {summary.get('high_value_count', 0)}",
            f"平均消费金额: ¥{summary.get('avg_monetary', 0):.0f}",
            "客户分层:",
        ]

        for segment, count in distribution.items():
            lines.append(f"  - {segment}: {count}人")

        return "\n".join(lines)

    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for LLM prompt."""
        lines = []
        for key, value in metrics.items():
            if isinstance(value, float):
                if abs(value) > 100:
                    lines.append(f"- {key}: {value:.0f}")
                else:
                    lines.append(f"- {key}: {value:.2f}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)


class NLUnderstanding:
    """
    Convert natural language queries into structured analysis requests.

    Uses LLM to understand user intent and extract parameters.
    """

    QUERY_TYPES = [
        "funnel_analysis",
        "rfm_analysis",
        "comparison",
        "trend",
        "customer_list",
        "general",
    ]

    SYSTEM_PROMPT = """你是一个电商数据分析助手。用户会用自然语言提问，你需要：
1. 判断用户想做什么分析（漏斗分析/RFM分析/对比/趋势/客户列表/其他）
2. 提取关键参数（时间范围、用户群体、具体指标等）
3. 用JSON格式返回结果

请严格按照以下JSON格式返回，不要添加任何解释：
{
  "query_type": "funnel_analysis|rfm_analysis|comparison|trend|customer_list|general",
  "parameters": {
    "time_range": "最近7天|最近30天|本月|上月|自定义",
    "filters": {},
    "sort_by": null
  },
  "original_question": "用户原始问题"
}"""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def parse(self, user_query: str) -> Dict[str, Any]:
        """Parse user query into structured request."""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ]

        response = await self.llm.chat(messages, temperature=0.3, max_tokens=500)

        # Extract JSON from response
        try:
            # Try to find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
            else:
                return self._default_result(user_query)
        except json.JSONDecodeError:
            return self._default_result(user_query)

    def _default_result(self, user_query: str) -> Dict[str, Any]:
        """Return default result when parsing fails."""
        return {
            "query_type": "general",
            "parameters": {},
            "original_question": user_query,
        }
