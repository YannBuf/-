from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
from weasyprint import HTML


class ReportGenerator:
    """
    Generate PDF reports from analysis data.

    MVP uses WeasyPrint for PDF generation.
    Future: React-PDF for frontend rendering.
    """

    TEMPLATES = {
        "weekly": "周报",
        "monthly": "月报",
        "funnel": "漏斗分析报告",
        "rfm": "客户分析报告",
        "custom": "自定义报告",
    }

    def __init__(self, output_dir: str = "/tmp/reports"):
        self.output_dir = output_dir

    async def generate(
        self,
        report_type: str,
        data: Dict[str, Any],
        title: Optional[str] = None,
    ) -> str:
        """
        Generate PDF report and return file path.

        Args:
            report_type: Type of report (weekly/monthly/funnel/rfm/custom)
            data: Analysis data to include
            title: Optional custom title

        Returns:
            Path to generated PDF file
        """
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        template_name = self.TEMPLATES.get(report_type, "报告")
        timestamp = datetime.now().timestamp()

        content = self._build_html_content(
            title=title or f"{template_name} - {datetime.now().strftime('%Y-%m-%d')}",
            report_type=report_type,
            data=data,
        )

        # Generate PDF using WeasyPrint
        pdf_filename = f"report_{timestamp}.pdf"
        pdf_path = f"{self.output_dir}/{pdf_filename}"
        HTML(string=content).write_pdf(pdf_path)

        return pdf_path

    def _build_html_content(
        self,
        title: str,
        report_type: str,
        data: Dict[str, Any],
    ) -> str:
        """Build HTML content for the report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; }}
        h1 {{ color: #333; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric-card {{ display: inline-block; padding: 20px; margin: 10px; background: #f5f5f5; border-radius: 8px; min-width: 150px; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #0066cc; }}
        .metric-label {{ color: #666; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f0f0f0; font-weight: 600; }}
        .insight {{ background: #e8f4fc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ margin-top: 40px; color: #999; font-size: 0.8em; text-align: center; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}</p>

    {self._render_data_content(report_type, data)}

    <div class="footer">
        由电商数据分析智能助手生成
    </div>
</body>
</html>
"""
        return html

    def _render_data_content(self, report_type: str, data: Dict[str, Any]) -> str:
        """Render specific content based on report type."""
        if report_type == "funnel":
            return self._render_funnel_content(data)
        elif report_type == "rfm":
            return self._render_rfm_content(data)
        elif report_type in ["weekly", "monthly"]:
            return self._render_summary_content(data)
        else:
            return self._render_generic_content(data)

    def _render_funnel_content(self, data: Dict[str, Any]) -> str:
        """Render funnel analysis content."""
        funnel = data.get("funnel", [])
        rows = ""
        for step in funnel:
            rows += f"""
            <tr>
                <td>{step.get('step', '')}</td>
                <td>{step.get('user_count', 0)}</td>
                <td>{step.get('conversion_rate', 0)*100:.1f}%</td>
                <td>{step.get('dropoff_rate', 0)*100:.1f}%</td>
            </tr>"""

        return f"""
    <h2>转化漏斗分析</h2>
    <table>
        <tr>
            <th>步骤</th>
            <th>用户数</th>
            <th>转化率</th>
            <th>流失率</th>
        </tr>
        {rows}
    </table>
    {self._render_insight(data.get('biggest_dropoff'), "最大流失环节")}
"""

    def _render_rfm_content(self, data: Dict[str, Any]) -> str:
        """Render RFM analysis content."""
        summary = data.get("summary", {})
        distribution = data.get("segment_distribution", {})

        segment_rows = ""
        for segment, count in distribution.items():
            segment_rows += f"<tr><td>{segment}</td><td>{count}</td></tr>"

        return f"""
    <h2>客户分析</h2>
    <div class="metric-card">
        <div class="metric-value">{summary.get('total_customers', 0)}</div>
        <div class="metric-label">总客户数</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">{summary.get('high_value_count', 0)}</div>
        <div class="metric-label">高价值客户</div>
    </div>
    <div class="metric-card">
        <div class="metric-value">¥{summary.get('avg_monetary', 0):.0f}</div>
        <div class="metric-label">平均消费</div>
    </div>

    <h3>客户分层</h3>
    <table>
        <tr><th>分层</th><th>客户数</th></tr>
        {segment_rows}
    </table>
"""

    def _render_summary_content(self, data: Dict[str, Any]) -> str:
        """Render weekly/monthly summary."""
        html = "<h2>核心指标</h2>"
        metrics = data.get("metrics", {})

        for key, value in metrics.items():
            display_value = f"¥{value:.0f}" if "amount" in key.lower() else f"{value:.2f}" if isinstance(value, float) else str(value)
            html += f"""
    <div class="metric-card">
        <div class="metric-value">{display_value}</div>
        <div class="metric-label">{key}</div>
    </div>"""

        return html

    def _render_generic_content(self, data: Dict[str, Any]) -> str:
        """Render generic content."""
        return f"<pre>{json.dumps(data, ensure_ascii=False, indent=2)}</pre>"

    def _render_insight(self, insight: Optional[Dict], label: str) -> str:
        """Render insight section."""
        if not insight:
            return ""

        return f"""
    <div class="insight">
        <strong>{label}:</strong> {insight.get('step', '')} (流失率: {insight.get('dropoff_rate', 0)*100:.1f}%)
    </div>
"""
