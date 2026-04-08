from collections import Counter, defaultdict
from dataclasses import dataclass

import pandas as pd


@dataclass
class AnalyticsResult:
    topic_frequency: list[dict]
    yearly_heatmap: list[dict]
    topic_difficulty: list[dict]


def build_analytics(frame: pd.DataFrame) -> AnalyticsResult:
    topic_counts = Counter(frame["topic"].tolist())
    topic_frequency = [
        {"topic": topic, "count": count}
        for topic, count in topic_counts.most_common()
    ]

    yearly_topic_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for _, row in frame.iterrows():
        yearly_topic_counts[int(row["year"])][row["topic"]] += 1

    yearly_heatmap = []
    for year, topics in sorted(yearly_topic_counts.items()):
        for topic, count in sorted(topics.items(), key=lambda item: (-item[1], item[0])):
            yearly_heatmap.append({"year": year, "topic": topic, "count": count})

    topic_difficulty = (
        frame.groupby("topic")["difficulty"].mean().reset_index().sort_values("difficulty", ascending=False)
    )
    topic_difficulty_records = [
        {"topic": row.topic, "difficulty": round(float(row.difficulty), 2)}
        for row in topic_difficulty.itertuples(index=False)
    ]

    return AnalyticsResult(
        topic_frequency=topic_frequency,
        yearly_heatmap=yearly_heatmap,
        topic_difficulty=topic_difficulty_records,
    )