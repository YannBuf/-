from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class RFMResult:
    """RFM analysis result for a single customer."""
    user_id: str
    recency: int  # days since last purchase
    frequency: int  # number of purchases
    monetary: float  # total amount
    rfm_score: Tuple[int, int, int]  # R, F, M scores (1-5 each)
    segment: str  # customer segment name


class RFMAnalyzer:
    """
    RFM (Recency, Frequency, Monetary) customer analysis.

    Divides customers into segments based on purchase behavior.
    """

    # Segment definitions
    SEGMENTS = {
        "champions": "高价值 champion 客户 - 最近活跃购买频繁",
        "loyal": "忠诚客户 - 购买频次高",
        "potential_loyalist": "潜在忠诚 - 有购买历史的新客户",
        "recent": "新客户 - 最近有购买",
        "promising": "有潜力 - 最近有互动但需培养",
        "needs_attention": "需关注 - 活跃度下降",
        "at_risk": "风险客户 - 很久没购买",
        "lost": "流失客户 - 长期未购买",
    }

    def __init__(self, reference_date: Optional[datetime] = None):
        self.reference_date = reference_date or datetime.now()

    def analyze(
        self,
        orders: List[Dict[str, Any]],
        user_id_field: str = "user_id",
        order_time_field: str = "event_time",
        amount_field: str = "amount",
    ) -> Dict[str, Any]:
        """
        Perform RFM analysis on order data.

        Returns:
            dict with segment distribution and individual customer results
        """
        # Aggregate customer metrics
        customer_metrics = self._aggregate_metrics(
            orders, user_id_field, order_time_field, amount_field
        )

        # Calculate RFM scores
        scored_customers = self._score_customers(customer_metrics)

        # Segment customers
        segmented = self._segment_customers(scored_customers)

        return {
            "segment_distribution": self._count_segments(segmented),
            "segment_details": self.SEGMENTS,
            "customers": [self._rfm_to_dict(rfm) for rfm in segmented],
            "summary": self._generate_summary(segmented),
        }

    def _aggregate_metrics(
        self,
        orders: List[Dict[str, Any]],
        user_id_field: str,
        order_time_field: str,
        amount_field: str,
    ) -> Dict[str, Dict[str, Any]]:
        """Aggregate order data by user."""
        customer_data = defaultdict(lambda: {"orders": [], "amounts": []})

        for order in orders:
            user_id = str(order.get(user_id_field, ""))
            if not user_id:
                continue

            order_time_str = order.get(order_time_field)
            amount = float(order.get(amount_field, 0) or 0)

            # Parse datetime
            if isinstance(order_time_str, str):
                try:
                    order_time = datetime.fromisoformat(order_time_str.replace("Z", "+00:00"))
                except ValueError:
                    continue
            elif isinstance(order_time_str, datetime):
                order_time = order_time_str
            else:
                continue

            customer_data[user_id]["orders"].append(order_time)
            customer_data[user_id]["amounts"].append(amount)

        # Calculate R, F, M per customer
        result = {}
        for user_id, data in customer_data.items():
            if not data["orders"]:
                continue

            last_order = max(data["orders"])
            recency = (self.reference_date - last_order).days
            frequency = len(data["orders"])
            monetary = sum(data["amounts"])

            result[user_id] = {
                "recency": recency,
                "frequency": frequency,
                "monetary": monetary,
            }

        return result

    def _score_customers(
        self, customer_metrics: Dict[str, Dict[str, Any]]
    ) -> List[RFMResult]:
        """Calculate RFM scores (1-5) for each customer."""
        if not customer_metrics:
            return []

        # Get quintile boundaries
        recencies = [m["recency"] for m in customer_metrics.values()]
        frequencies = [m["frequency"] for m in customer_metrics.values()]
        monetaries = [m["monetary"] for m in customer_metrics.values()]

        # R: lower is better (less days since purchase)
        r_quintiles = self._get_quintile_boundaries(recencies, lower_is_better=True)
        # F: higher is better
        f_quintiles = self._get_quintile_boundaries(frequencies, lower_is_better=False)
        # M: higher is better
        m_quintiles = self._get_quintile_boundaries(monetaries, lower_is_better=False)

        results = []
        for user_id, metrics in customer_metrics.items():
            r_score = self._calculate_score(metrics["recency"], r_quintiles, lower_is_better=True)
            f_score = self._calculate_score(metrics["frequency"], f_quintiles, lower_is_better=False)
            m_score = self._calculate_score(metrics["monetary"], m_quintiles, lower_is_better=False)

            rfm_score = (r_score, f_score, m_score)

            results.append(RFMResult(
                user_id=user_id,
                recency=metrics["recency"],
                frequency=metrics["frequency"],
                monetary=metrics["monetary"],
                rfm_score=rfm_score,
                segment="",  # Will be filled by _segment_customers
            ))

        return results

    def _get_quintile_boundaries(
        self, values: List[float], lower_is_better: bool
    ) -> List[float]:
        """Get quintile (20%) boundaries for scoring."""
        if not values:
            return [0, 0, 0, 0]

        sorted_values = sorted(values)
        n = len(sorted_values)

        # 5 quintiles = 6 boundaries (including min and max)
        q1 = sorted_values[int(n * 0.2)]
        q2 = sorted_values[int(n * 0.4)]
        q3 = sorted_values[int(n * 0.6)]
        q4 = sorted_values[int(n * 0.8)]

        if lower_is_better:
            return [float('inf'), q4, q3, q2, q1, -float('inf')]
        else:
            return [-float('inf'), q1, q2, q3, q4, float('inf')]

    def _calculate_score(
        self, value: float, quintiles: List[float], lower_is_better: bool
    ) -> int:
        """Calculate score (1-5) based on quintile boundaries."""
        for i, boundary in enumerate(quintiles[1:], 1):
            if value < boundary:
                return 6 - i if lower_is_better else i
        return 1 if lower_is_better else 5

    def _segment_customers(self, customers: List[RFMResult]) -> List[RFMResult]:
        """Assign segment names to customers based on RFM scores."""
        for customer in customers:
            r, f, m = customer.rfm_score
            score_sum = r + f + m

            if r >= 4 and f >= 4 and m >= 4:
                customer.segment = "champions"
            elif f >= 4 and m >= 3:
                customer.segment = "loyal"
            elif r >= 3 and f >= 2:
                customer.segment = "potential_loyalist"
            elif r >= 3:
                customer.segment = "recent"
            elif r >= 2:
                customer.segment = "promising"
            elif score_sum >= 6:
                customer.segment = "needs_attention"
            elif f >= 2:
                customer.segment = "at_risk"
            else:
                customer.segment = "lost"

        return customers

    def _count_segments(self, customers: List[RFMResult]) -> Dict[str, int]:
        """Count customers in each segment."""
        counts = defaultdict(int)
        for customer in customers:
            counts[customer.segment] += 1
        return dict(counts)

    def _rfm_to_dict(self, rfm: RFMResult) -> Dict[str, Any]:
        """Convert RFMResult to dict for JSON serialization."""
        return {
            "user_id": rfm.user_id,
            "recency": rfm.recency,
            "frequency": rfm.frequency,
            "monetary": round(rfm.monetary, 2),
            "rfm_score": rfm.rfm_score,
            "segment": rfm.segment,
        }

    def _generate_summary(self, customers: List[RFMResult]) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not customers:
            return {"total_customers": 0}

        total = len(customers)
        segments = self._count_segments(customers)

        return {
            "total_customers": total,
            "avg_recency": sum(c.recency for c in customers) / total,
            "avg_frequency": sum(c.frequency for c in customers) / total,
            "avg_monetary": sum(c.monetary for c in customers) / total,
            "top_segment": max(segments, key=segments.get) if segments else None,
            "high_value_count": sum(1 for c in customers if c.segment in ["champions", "loyal"]),
        }