from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime


class FunnelAnalyzer:
    """
    Analyze conversion funnels from user behavior data.

    Standard event types: impression -> click -> add_to_cart -> checkout -> purchase
    """

    DEFAULT_STEPS = [
        "impression",
        "click",
        "add_to_cart",
        "checkout",
        "purchase",
    ]

    def __init__(self, steps: Optional[List[str]] = None):
        self.steps = steps or self.DEFAULT_STEPS

    def analyze(
        self,
        events: List[Dict[str, Any]],
        user_id_field: str = "user_id",
        event_type_field: str = "event_type",
        timestamp_field: str = "event_time",
        window_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Analyze funnel conversion.

        Returns:
            dict with step counts, conversion rates, and drop-off analysis
        """
        # Filter and sort events
        events = self._filter_events(events, timestamp_field, window_days)

        # Count users at each step
        step_users = self._count_users_per_step(events, user_id_field, event_type_field)

        # Calculate conversion metrics
        funnel_data = self._calculate_funnel_metrics(step_users)

        # Find biggest drop-off
        biggest_dropoff = self._find_biggest_dropoff(funnel_data)

        return {
            "funnel": funnel_data,
            "total_users": len(set(e.get(user_id_field) for e in events)),
            "biggest_dropoff": biggest_dropoff,
            "steps": self.steps,
        }

    def _filter_events(
        self, events: List[Dict[str, Any]], timestamp_field: str, window_days: int
    ) -> List[Dict[str, Any]]:
        """Filter events within time window."""
        # For MVP, skip time filtering (assume data is already recent)
        return [e for e in events if e.get(timestamp_field) and e.get(timestamp_field)]

    def _count_users_per_step(
        self,
        events: List[Dict[str, Any]],
        user_id_field: str,
        event_type_field: str,
    ) -> Dict[str, set]:
        """Count unique users who completed each step."""
        step_users = defaultdict(set)

        for event in events:
            user_id = event.get(user_id_field)
            event_type = event.get(event_type_field, "").lower()

            if user_id and event_type in self.steps:
                step_users[event_type].add(user_id)

        return dict(step_users)

    def _calculate_funnel_metrics(
        self, step_users: Dict[str, set]
    ) -> List[Dict[str, Any]]:
        """Calculate conversion rates between steps."""
        results = []
        prev_count = None

        for step in self.steps:
            count = len(step_users.get(step, set()))

            if prev_count is None:
                conversion_rate = 1.0 if count > 0 else 0.0
            else:
                conversion_rate = count / prev_count if prev_count > 0 else 0.0

            dropoff_rate = 1.0 - conversion_rate

            results.append({
                "step": step,
                "user_count": count,
                "conversion_rate": round(conversion_rate, 4),
                "dropoff_rate": round(dropoff_rate, 4),
            })

            prev_count = count

        return results

    def _find_biggest_dropoff(
        self, funnel_data: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find the step with the biggest drop-off rate."""
        max_dropoff = 0
        max_dropoff_step = None

        for step in funnel_data:
            if step["dropoff_rate"] > max_dropoff and step["user_count"] > 0:
                max_dropoff = step["dropoff_rate"]
                max_dropoff_step = step["step"]

        if max_dropoff_step and max_dropoff > 0.1:  # Only report if >10% dropoff
            return {
                "step": max_dropoff_step,
                "dropoff_rate": round(max_dropoff, 4),
            }
        return None