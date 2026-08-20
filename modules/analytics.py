import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from collections import defaultdict

def create_accuracy_trend_chart(results):
    """Create accuracy trend chart"""
    if not results:
        return None

    dates = [datetime.fromisoformat(r["timestamp"]).date() for r in results]
    accuracies = [r.get("accuracy", 0) for r in results]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=accuracies,
        mode='lines+markers',
        name='正答率',
        line=dict(color='#FF9900', width=3),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title='正答率推移',
        xaxis_title='日付',
        yaxis_title='正答率 (%)',
        hovermode='x unified',
        template='plotly_dark',
        paper_bgcolor='#16191F',
        plot_bgcolor='#1E2329',
        font=dict(color='#FFFFFF'),
        height=400
    )

    return fig

def create_exam_type_chart(results):
    """Create exam type distribution chart"""
    if not results:
        return None

    type_counts = defaultdict(int)
    for result in results:
        exam_type = str(result.get("type", "unknown"))
        type_counts[exam_type] += 1

    fig = go.Figure(data=[
        go.Bar(
            x=list(type_counts.keys()),
            y=list(type_counts.values()),
            marker_color='#0084D1'
        )
    ])

    fig.update_layout(
        title='試験タイプ別実施回数',
        xaxis_title='試験タイプ',
        yaxis_title='実施回数',
        template='plotly_dark',
        paper_bgcolor='#16191F',
        plot_bgcolor='#1E2329',
        font=dict(color='#FFFFFF'),
        height=400,
        showlegend=False
    )

    return fig

def create_study_time_chart(study_times):
    """Create study time chart"""
    if not study_times:
        return None

    # Group by date
    dates = {}
    for study in study_times[-30:]:  # Last 30 days
        date = datetime.fromisoformat(study["timestamp"]).date()
        date_str = str(date)
        if date_str not in dates:
            dates[date_str] = 0
        dates[date_str] += int(study.get("duration", 0) / 60)

    sorted_dates = sorted(dates.keys())
    sorted_minutes = [dates[d] for d in sorted_dates]

    fig = go.Figure(data=[
        go.Bar(
            x=sorted_dates,
            y=sorted_minutes,
            marker_color='#13BB2D'
        )
    ])

    fig.update_layout(
        title='学習時間推移 (分)',
        xaxis_title='日付',
        yaxis_title='学習時間 (分)',
        template='plotly_dark',
        paper_bgcolor='#16191F',
        plot_bgcolor='#1E2329',
        font=dict(color='#FFFFFF'),
        height=400,
        showlegend=False
    )

    return fig

def create_category_accuracy_chart(results):
    """Create category accuracy chart"""
    if not results:
        return None

    category_stats = defaultdict(lambda: {"correct": 0, "total": 0})

    for result in results:
        exam_type = str(result.get("type", "unknown"))
        correct = result.get("correct", 0)
        total = result.get("total", 0)

        category_stats[exam_type]["correct"] += correct
        category_stats[exam_type]["total"] += total

    categories = []
    accuracies = []
    for category, stats in category_stats.items():
        if stats["total"] > 0:
            accuracy = stats["correct"] / stats["total"] * 100
            categories.append(category)
            accuracies.append(accuracy)

    fig = go.Figure(data=[
        go.Bar(
            x=accuracies,
            y=categories,
            orientation='h',
            marker_color='#FF9900'
        )
    ])

    fig.update_layout(
        title='カテゴリ別正答率',
        xaxis_title='正答率 (%)',
        yaxis_title='カテゴリ',
        template='plotly_dark',
        paper_bgcolor='#16191F',
        plot_bgcolor='#1E2329',
        font=dict(color='#FFFFFF'),
        height=400,
        showlegend=False
    )

    return fig

def create_xp_history_chart(user_profile, results):
    """Create XP history chart"""
    if not results:
        return None

    # Simplified: show total XP over time
    cumulative_xp = []
    dates = []
    xp_sum = 0

    for result in sorted(results, key=lambda x: x["timestamp"]):
        date = datetime.fromisoformat(result["timestamp"]).date()
        # Rough estimation: award XP based on accuracy
        accuracy = result.get("accuracy", 0) / 100
        correct_count = result.get("correct", 0)
        xp_award = int(correct_count * 10 * accuracy)

        xp_sum += xp_award
        cumulative_xp.append(xp_sum)
        dates.append(date)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=cumulative_xp,
        mode='lines',
        name='累積XP',
        line=dict(color='#FF9900', width=3),
        fill='tozeroy',
        fillcolor='rgba(255, 153, 0, 0.2)'
    ))

    fig.update_layout(
        title='累積XP推移',
        xaxis_title='日付',
        yaxis_title='累積XP',
        template='plotly_dark',
        paper_bgcolor='#16191F',
        plot_bgcolor='#1E2329',
        font=dict(color='#FFFFFF'),
        height=400,
        showlegend=False
    )

    return fig
