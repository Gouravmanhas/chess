import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import json
import requests

# ═══════════════════════════════════════════════════════════════
# DATA LOADING (cached for speed)
# ═══════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    df = pd.read_csv("games.csv")
    df.dropna(inplace=True)
    df.drop_duplicates(inplace=True)

    # Derived numeric features
    df['avg_match_rating'] = (df['white_rating'] + df['black_rating']) / 2
    df['rating_diff'] = df['white_rating'] - df['black_rating']

    # Rating tiers
    rating_bins = [0, 1200, 1500, 1800, 3000]
    rating_labels = [
        'Beginner (<1200)',
        'Low-Intermediate (1200-1500)',
        'High-Intermediate (1500-1800)',
        'Advanced (>1800)'
    ]
    df['rating_tier'] = pd.cut(df['avg_match_rating'], bins=rating_bins, labels=rating_labels)

    # Opening base + variation
    df['opening_base'] = df['opening_name'].str.split(':').str[0].str.strip()
    df['opening_variation'] = (
        df['opening_name'].str.split(':').str[1].str.strip().fillna('Main Line')
    )

    # Duration in minutes
    df['duration_mins'] = (df['last_move_at'] - df['created_at']) / 60000.0
    df = df[(df['duration_mins'] > 0.1) & (df['duration_mins'] < 180)]

    # Base time & game format
    df['base_time_mins'] = pd.to_numeric(
        df['increment_code'].str.split('+').str[0], errors='coerce'
    ).fillna(10)

    format_bins = [-1, 2.9, 8, 25, 300]
    format_labels = [
        '1. Bullet (<3m)',
        '2. Blitz (3-8m)',
        '3. Rapid (9-25m)',
        '4. Classical (>25m)'
    ]
    df['game_format'] = pd.cut(df['base_time_mins'], bins=format_bins, labels=format_labels)

    return df


df = load_data()

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════
def get_top_performing_openings(data_subset, min_games=40):
    """Filters for popular openings and calculates an effective win rate."""
    counts = data_subset['opening_base'].value_counts()
    valid_openings = counts[counts >= min_games].index
    filtered = data_subset[data_subset['opening_base'].isin(valid_openings)]

    win_rates = (
        filtered.groupby('opening_base')['winner']
        .value_counts(normalize=True)
        .unstack()
        .fillna(0)
    )
    if 'draw' not in win_rates.columns:
        win_rates['draw'] = 0

    win_rates['success_score'] = win_rates.get('white', 0) + (0.5 * win_rates['draw'])
    win_rates['total_games'] = filtered.groupby('opening_base').size()
    return (
        win_rates.sort_values(by='success_score', ascending=False)
        .head(10)
        .reset_index()
    )


def get_opening_stats(opening_name, data):
    """Return a dict of summary stats for a single base opening."""
    subset = data[data['opening_base'] == opening_name]
    if subset.empty:
        return None
    total = len(subset)
    white_wins = int((subset['winner'] == 'white').sum())
    black_wins = int((subset['winner'] == 'black').sum())
    draws = int((subset['winner'] == 'draw').sum())
    return {
        'opening': opening_name,
        'total_games': total,
        'white_win_pct': round(white_wins / total * 100, 1),
        'black_win_pct': round(black_wins / total * 100, 1),
        'draw_pct': round(draws / total * 100, 1),
        'success_score': round((white_wins + 0.5 * draws) / total, 3),
        'avg_turns': round(subset['turns'].mean(), 1),
        'avg_duration': round(subset['duration_mins'].mean(), 1),
        'avg_rating': round(subset['avg_match_rating'].mean(), 0),
    }


# ═══════════════════════════════════════════════════════════════
# CONSISTENT COLOR MAPS
# ═══════════════════════════════════════════════════════════════
FORMAT_COLORS = {
    '1. Bullet (<3m)': '#FF5733',
    '2. Blitz (3-8m)': '#33FF57',
    '3. Rapid (9-25m)': '#3357FF',
    '4. Classical (>25m)': '#F1C40F',
}

RATING_COLORS = {
    'Beginner (<1200)': '#FF5733',
    'Low-Intermediate (1200-1500)': '#33FF57',
    'High-Intermediate (1500-1800)': '#3357FF',
    'Advanced (>1800)': '#F1C40F',
}

WINNER_COLORS = {
    'white': '#EDEDED',
    'black': '#2C2C2C',
    'draw': '#7F7F7F',
}

# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════
st.set_page_config(page_title="Chessalytics", page_icon="♔", layout="wide")

# ═══════════════════════════════════════════════════════════════
# SIDEBAR — navigation + global filters
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("♛ Chessalytics ♛")

    opt = st.radio(
        "Select a page",
        [
            "🏠 Home",
            "📊 Data Analysis",
            "📈 Visualizations",
            "🔍 Opening Explorer",
            "💡 Key Insights",
            "🧹 Data Cleaning",
            "🤖 Chat Bot",
        ],
        key="page_selector",
    )

    st.markdown("---")
    st.markdown("### 🔧 Global Filters")

    all_rating_tiers = sorted(df['rating_tier'].cat.categories.tolist())
    filter_rating = st.multiselect(
        "Rating Tier",
        options=all_rating_tiers,
        default=all_rating_tiers,
        key="filter_rating",
    )

    all_formats = sorted(df['game_format'].cat.categories.tolist())
    filter_format = st.multiselect(
        "Game Format",
        options=all_formats,
        default=all_formats,
        key="filter_format",
    )

    filter_rated = st.multiselect(
        "Rated?",
        options=[True, False],
        default=[True, False],
        key="filter_rated",
    )

# Apply global filters
df_filtered = df[
    df['rating_tier'].isin(filter_rating)
    & df['game_format'].isin(filter_format)
    & df['rated'].isin(filter_rated)
].copy()

# ═══════════════════════════════════════════════════════════════
# 🏠 HOME
# ═══════════════════════════════════════════════════════════════
if opt == "🏠 Home":

    st.title("♔ Welcome to Chessalytics ♔")
    st.subheader(
        "Advanced chess analytics and trend analysis system ♚", divider="rainbow"
    )
    st.markdown(
        """
    This application provides a deep dive into over **20,000 chess games** from Lichess.
    Explore win rates, opening theories, time control impacts, and player skill dynamics.
    """
    )

    st.markdown("### 📊 Key Metrics")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Games", f"{len(df_filtered):,}", border=True)
    c2.metric("Unique Openings", df_filtered['opening_base'].nunique(), border=True)
    c3.metric("Columns", df_filtered.shape[1], border=True)
    c4.metric("Avg Rating", f"{df_filtered['avg_match_rating'].mean():.0f}", border=True)
    c5.metric("Avg Turns", f"{df_filtered['turns'].mean():.1f}", border=True)
    c6.metric("Null Values", int(df_filtered.isnull().sum().sum()), border=True)

    ch1, ch2 = st.columns(2)

    with ch1:
        fig = px.histogram(
            df_filtered,
            x='game_format',
            color='game_format',
            title='Game Format Distribution',
            color_discrete_map=FORMAT_COLORS,
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        fig = px.histogram(
            df_filtered,
            x='rating_tier',
            color='rating_tier',
            title='Rating Tier Distribution',
            color_discrete_map=RATING_COLORS,
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.info(
        "👈 Use the **sidebar filters** to narrow data across all pages. "
        "Navigate using the radio buttons above."
    )
    st.subheader("Check out the next page for data overview and analysis.", divider='grey')

# ═══════════════════════════════════════════════════════════════
# 📊 DATA ANALYSIS
# ═══════════════════════════════════════════════════════════════
elif opt == "📊 Data Analysis":

    st.title("⌖ Data Overview & Analysis ⌖")
    st.subheader(
        "Overview and statistical analysis of the chess games dataset.",
        divider="rainbow",
    )

    st.subheader("Dataset Preview", divider='green')
    st.dataframe(df_filtered.head(20), use_container_width=True)

    st.subheader("Summary Statistics", divider='green')
    st.dataframe(df_filtered.describe(), use_container_width=True)

    st.subheader("Top Performing Openings (by White success score)", divider='green')
    with st.spinner("Calculating opening performance..."):
        top_openings = get_top_performing_openings(df_filtered)
    st.dataframe(top_openings, use_container_width=True)

    st.subheader("Feature Correlation Heatmap", divider='green')
    numeric_cols = [
        'white_rating', 'black_rating', 'turns', 'opening_ply',
        'avg_match_rating', 'rating_diff', 'duration_mins', 'base_time_mins',
    ]
    corr = df_filtered[numeric_cols].corr()
    fig_corr = px.imshow(
        corr,
        text_auto=".2f",
        color_continuous_scale='RdBu_r',
        title='Correlation Matrix of Numeric Features',
        aspect='auto',
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    st.subheader("Check out the next page for visualizations.", divider='grey')

# ═══════════════════════════════════════════════════════════════
# 📈 VISUALIZATIONS
# ═══════════════════════════════════════════════════════════════
elif opt == "📈 Visualizations":

    st.title("⌖ Visualizations ⌖")
    st.subheader(
        "Visual insights into the chess games dataset.", divider="rainbow"
    )

    t1, t2, t3, t4 = st.tabs(
        ["Macro Trends", "Opening Analysis", "Dynamic Insights", "Advanced Metrics"]
    )

    # ── TAB 1: Macro Trends ──────────────────────────────────
    with t1:
        st.markdown("#### 👉 Win Rate & Format Volume")
        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(
                df_filtered,
                names='winner',
                title='1. Overall Match Outcome Share',
                color='winner',
                color_discrete_map=WINNER_COLORS,
                hole=0.4,
            )
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.pie(
                df_filtered,
                names='game_format',
                title='2. Pace of Play (Game Formats)',
                color_discrete_sequence=px.colors.sequential.Plasma,
                hole=0.4,
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader(
            "Check out the next tab for opening analysis.", divider='grey'
        )

    # ── TAB 2: Opening Analysis ──────────────────────────────
    with t2:
        st.markdown("#### 👉 Opening Popularity & Success Rates")

        top_10 = (
            df_filtered['opening_base']
            .value_counts()
            .head(10)
            .reset_index()
        )
        fig = px.bar(
            top_10,
            x='count',
            y='opening_base',
            orientation='h',
            title='3. Top 10 Most Played Openings',
            color='opening_base',
            color_discrete_sequence=px.colors.sequential.Plasma,
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

        top_list = df_filtered['opening_base'].value_counts().head(12).index
        heatmap_data = (
            df_filtered[df_filtered['opening_base'].isin(top_list)]
            .groupby(['rating_tier', 'opening_base'])
            .size()
            .reset_index(name='count')
        )
        fig = px.density_heatmap(
            heatmap_data,
            x='rating_tier',
            y='opening_base',
            z='count',
            title='4. Opening Popularity Matrix Across Skill Levels',
            color_continuous_scale='Viridis',
            labels={'count': 'Number of Games'},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Success Rates by Tier")
        tier_choice = st.selectbox(
            "Select Rating Tier",
            options=[
                'Beginner (<1200)',
                'Intermediate (1200-1800)',
                'Advanced (>1800)',
            ],
            key='success_tier',
        )

        with st.spinner("Calculating..."):
            if tier_choice == 'Beginner (<1200)':
                tier_df = df_filtered[
                    df_filtered['rating_tier'] == 'Beginner (<1200)'
                ]
                tier_win = get_top_performing_openings(tier_df, min_games=20)
                if not tier_win.empty:
                    fig = px.bar(
                        tier_win,
                        x='success_score',
                        y='opening_base',
                        orientation='h',
                        title='5. Best Openings for Beginners',
                        color='success_score',
                        color_continuous_scale='viridis',
                    )
                    st.plotly_chart(fig, use_container_width=True)

            elif tier_choice == 'Intermediate (1200-1800)':
                tier_df = df_filtered[
                    df_filtered['rating_tier'].isin(
                        [
                            'Low-Intermediate (1200-1500)',
                            'High-Intermediate (1500-1800)',
                        ]
                    )
                ]
                tier_win = get_top_performing_openings(tier_df, min_games=50)
                if not tier_win.empty:
                    fig = px.bar(
                        tier_win,
                        x='success_score',
                        y='opening_base',
                        orientation='h',
                        title='6. Best Openings for Intermediates',
                        color='success_score',
                        color_continuous_scale='Bluered',
                    )
                    st.plotly_chart(fig, use_container_width=True)

            else:
                tier_df = df_filtered[
                    df_filtered['rating_tier'] == 'Advanced (>1800)'
                ]
                tier_win = get_top_performing_openings(tier_df, min_games=30)
                if not tier_win.empty:
                    fig = px.bar(
                        tier_win,
                        x='success_score',
                        y='opening_base',
                        orientation='h',
                        title='7. Best Openings for Advanced Players',
                        color='success_score',
                        color_continuous_scale='Plasma',
                    )
                    st.plotly_chart(fig, use_container_width=True)

        # Stacked outcome chart
        top_names = df_filtered['opening_name'].value_counts().head(10).index
        filtered_open = df_filtered[df_filtered['opening_name'].isin(top_names)]
        crosstab = pd.crosstab(filtered_open['opening_name'], filtered_open['winner'])
        crosstab_pct = crosstab.div(crosstab.sum(axis=1), axis=0) * 100
        crosstab_pct = crosstab_pct.reset_index()
        fig = px.bar(
            crosstab_pct,
            x='opening_name',
            y=['white', 'black', 'draw'],
            title='8. Opening vs Game Outcome (%)',
            barmode='stack',
            color_discrete_map=WINNER_COLORS,
            opacity=0.85,
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader(
            "Check out the next tab for dynamic insights.", divider='grey'
        )

    # ── TAB 3: Dynamic Insights ──────────────────────────────
    with t3:
        st.markdown("#### 👉 Termination & Rating Impact")

        fig = px.histogram(
            df_filtered,
            x='game_format',
            color='victory_status',
            barmode='stack',
            title='9. How Games End by Time Control',
            color_discrete_sequence=px.colors.sequential.Plasma,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### White Advantage by Rating Tier")
        fig = px.histogram(
            df_filtered,
            x='rating_tier',
            color='winner',
            barmode='group',
            title="10. White's Advantage by Skill Level",
            color_discrete_map=WINNER_COLORS,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### White Advantage by Time Control")
        no_draw = df_filtered[df_filtered['winner'] != 'draw']
        fig = px.histogram(
            no_draw,
            x='game_format',
            color='winner',
            barmode='group',
            title="11. White's Advantage by Time Control",
            color_discrete_map={'white': '#EDEDED', 'black': '#2C2C2C'},
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader(
            "Check out the next tab for advanced metrics.", divider='grey'
        )

    # ── TAB 4: Advanced Metrics ──────────────────────────────
    with t4:
        st.markdown("#### 👉 Time & Moves Correlation")
        sample = df_filtered.sample(
            n=min(len(df_filtered), 3000), random_state=42
        )

        fig = px.scatter(
            sample,
            x='turns',
            y='duration_mins',
            color='game_format',
            title='12. Time Spent vs Moves Played',
            opacity=0.6,
            color_discrete_map=FORMAT_COLORS,
        )
        st.plotly_chart(fig, use_container_width=True)

        fig = px.box(
            df_filtered,
            x='game_format',
            y='turns',
            color='game_format',
            title='13. Turn Distribution by Format',
            color_discrete_sequence=px.colors.sequential.Plasma,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Advanced Metrics")

        fig = px.scatter(
            sample,
            x='avg_match_rating',
            y='opening_ply',
            trendline='ols',
            title='14. Opening Depth vs Player ELO',
            opacity=0.4,
            color_discrete_sequence=['#1f77b4'],
        )
        st.plotly_chart(fig, use_container_width=True)

        fig = px.box(
            df_filtered,
            x='rated',
            y='turns',
            color='winner',
            title='15. Casual vs Competitive Turn Spans',
            color_discrete_map=WINNER_COLORS,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader(
            "Check out the Opening Explorer for deep-dive comparisons.",
            divider='grey',
        )

# ═══════════════════════════════════════════════════════════════
# 🔍 OPENING EXPLORER  (NEW)
# ═══════════════════════════════════════════════════════════════
elif opt == "🔍 Opening Explorer":

    st.title("🔍 Opening Comparison & Drill-Down Explorer")
    st.subheader(
        "Select openings to compare side-by-side, or drill into variations of a single opening.",
        divider="rainbow",
    )

    all_openings = sorted(df_filtered['opening_base'].unique().tolist())

    tab_compare, tab_drill = st.tabs(
        ["⚔️ Compare Openings", "🔬 Variation Drill-Down"]
    )

    # ── COMPARE TAB ──────────────────────────────────────────
    with tab_compare:
        st.markdown("#### Select 2–4 openings to compare side-by-side")
        selected = st.multiselect(
            "Choose openings to compare:",
            options=all_openings,
            default=all_openings[:2] if len(all_openings) >= 2 else all_openings,
            max_selections=4,
        )

        if len(selected) >= 2:
            # Summary table
            stats_list = []
            for op in selected:
                s = get_opening_stats(op, df_filtered)
                if s:
                    stats_list.append(s)
            stats_df = pd.DataFrame(stats_list)

            st.markdown("##### 📋 Summary Statistics")
            st.dataframe(
                stats_df.set_index('opening'), use_container_width=True
            )

            # Grouped bar — win / draw / loss
            st.markdown("##### 🏆 Win / Draw / Loss Comparison")
            fig = go.Figure()
            for op in selected:
                sub = df_filtered[df_filtered['opening_base'] == op]
                total = len(sub)
                if total == 0:
                    continue
                fig.add_trace(
                    go.Bar(
                        name=op,
                        x=['White Win %', 'Black Win %', 'Draw %'],
                        y=[
                            round((sub['winner'] == 'white').sum() / total * 100, 1),
                            round((sub['winner'] == 'black').sum() / total * 100, 1),
                            round((sub['winner'] == 'draw').sum() / total * 100, 1),
                        ],
                    )
                )
            fig.update_layout(
                barmode='group',
                title='Outcome Distribution — Selected Openings',
                yaxis_title='Percentage (%)',
            )
            st.plotly_chart(fig, use_container_width=True)

            # Radar chart
            st.markdown("##### 🕸️ Multi-Metric Radar Comparison")
            categories = [
                'White Win %',
                'Avg Turns',
                'Avg Duration',
                'Avg Rating /30',
                'Success ×100',
            ]
            fig_radar = go.Figure()
            for _, row in stats_df.iterrows():
                fig_radar.add_trace(
                    go.Scatterpolar(
                        r=[
                            row['white_win_pct'],
                            row['avg_turns'],
                            row['avg_duration'],
                            row['avg_rating'] / 30,
                            row['success_score'] * 100,
                        ],
                        theta=categories,
                        fill='toself',
                        name=row['opening'],
                        opacity=0.6,
                    )
                )
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True)),
                title='Radar Comparison (values scaled for visual clarity)',
                showlegend=True,
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            # Violin — rating distribution
            st.markdown("##### 📊 Rating Distribution per Opening")
            fig = px.violin(
                df_filtered[df_filtered['opening_base'].isin(selected)],
                x='opening_base',
                y='avg_match_rating',
                color='opening_base',
                box=True,
                points='outliers',
                title='Rating Spread of Players Using Each Opening',
            )
            st.plotly_chart(fig, use_container_width=True)

            # Format breakdown
            st.markdown("##### ⏱️ Game Format Breakdown per Opening")
            fmt_data = (
                df_filtered[df_filtered['opening_base'].isin(selected)]
                .groupby(['opening_base', 'game_format'])
                .size()
                .reset_index(name='count')
            )
            fig = px.bar(
                fmt_data,
                x='opening_base',
                y='count',
                color='game_format',
                barmode='group',
                title='Format Popularity per Opening',
                color_discrete_map=FORMAT_COLORS,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Avg turns & duration side-by-side
            st.markdown("##### 🔄 Avg Turns & Duration Comparison")
            ca, cb = st.columns(2)
            with ca:
                fig = px.bar(
                    stats_df,
                    x='opening',
                    y='avg_turns',
                    title='Average Number of Turns',
                    color='avg_turns',
                    color_continuous_scale='Plasma',
                )
                st.plotly_chart(fig, use_container_width=True)
            with cb:
                fig = px.bar(
                    stats_df,
                    x='opening',
                    y='avg_duration',
                    title='Average Duration (minutes)',
                    color='avg_duration',
                    color_continuous_scale='Viridis',
                )
                st.plotly_chart(fig, use_container_width=True)

            # Termination breakdown
            st.markdown("##### 💀 How Games End per Opening")
            term_data = (
                df_filtered[df_filtered['opening_base'].isin(selected)]
                .groupby(['opening_base', 'victory_status'])
                .size()
                .reset_index(name='count')
            )
            fig = px.bar(
                term_data,
                x='opening_base',
                y='count',
                color='victory_status',
                barmode='stack',
                title='Termination Type per Opening',
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Rating tier breakdown
            st.markdown("##### 🎯 Rating Tier Breakdown per Opening")
            tier_data = (
                df_filtered[df_filtered['opening_base'].isin(selected)]
                .groupby(['opening_base', 'rating_tier'])
                .size()
                .reset_index(name='count')
            )
            fig = px.bar(
                tier_data,
                x='opening_base',
                y='count',
                color='rating_tier',
                barmode='group',
                title='Rating Tier Distribution per Opening',
                color_discrete_map=RATING_COLORS,
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("Please select at least **2 openings** to compare.")

    # ── DRILL-DOWN TAB ───────────────────────────────────────
    with tab_drill:
        st.markdown("#### Pick a base opening to explore its variations")
        base_choice = st.selectbox(
            "Base Opening:", options=all_openings, key='drill_base'
        )

        if base_choice:
            var_df = df_filtered[
                df_filtered['opening_base'] == base_choice
            ].copy()

            st.markdown(
                f"**{base_choice}** — {len(var_df):,} games, "
                f"{var_df['opening_variation'].nunique()} variations"
            )

            # Variation frequency
            var_counts = (
                var_df['opening_variation']
                .value_counts()
                .head(15)
                .reset_index()
            )
            fig = px.bar(
                var_counts,
                x='count',
                y='opening_variation',
                orientation='h',
                title=f'Top Variations of {base_choice}',
                color='count',
                color_continuous_scale='Plasma',
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

            # Variation win rates
            st.markdown("##### Win Rates by Variation (min 5 games)")
            valid_vars = var_counts[var_counts['count'] >= 5]['opening_variation'].tolist()
            var_min = var_df[var_df['opening_variation'].isin(valid_vars)]

            if not var_min.empty:
                var_win = (
                    var_min.groupby('opening_variation')['winner']
                    .value_counts(normalize=True)
                    .unstack()
                    .fillna(0)
                    * 100
                )
                for col in ['white', 'black', 'draw']:
                    if col not in var_win.columns:
                        var_win[col] = 0
                var_win = var_win.reset_index()

                fig = px.bar(
                    var_win,
                    x='opening_variation',
                    y=['white', 'black', 'draw'],
                    title=f'Outcome % by Variation — {base_choice}',
                    barmode='stack',
                    color_discrete_map=WINNER_COLORS,
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

            # Variation × rating tier heatmap
            st.markdown("##### Variation Popularity by Rating Tier")
            var_heat = (
                var_df.groupby(['rating_tier', 'opening_variation'])
                .size()
                .reset_index(name='count')
            )
            top_vars = var_counts.head(8)['opening_variation'].tolist()
            var_heat_f = var_heat[var_heat['opening_variation'].isin(top_vars)]
            fig = px.density_heatmap(
                var_heat_f,
                x='rating_tier',
                y='opening_variation',
                z='count',
                title=f'Variation × Rating Tier — {base_choice}',
                color_continuous_scale='Viridis',
            )
            st.plotly_chart(fig, use_container_width=True)

            # Avg turns per variation
            st.markdown("##### Average Game Length by Variation")
            var_turns = (
                var_df.groupby('opening_variation')['turns']
                .agg(['mean', 'count'])
                .reset_index()
            )
            var_turns = (
                var_turns[var_turns['count'] >= 5]
                .sort_values('mean', ascending=True)
                .tail(15)
            )
            fig = px.bar(
                var_turns,
                x='mean',
                y='opening_variation',
                orientation='h',
                title=f'Avg Turns per Variation — {base_choice}',
                color='mean',
                color_continuous_scale='RdYlGn_r',
                labels={
                    'mean': 'Avg Turns',
                    'opening_variation': 'Variation',
                },
            )
            st.plotly_chart(fig, use_container_width=True)

            # Avg rating per variation
            st.markdown("##### Average Player Rating by Variation")
            var_rating = (
                var_df.groupby('opening_variation')['avg_match_rating']
                .agg(['mean', 'count'])
                .reset_index()
            )
            var_rating = (
                var_rating[var_rating['count'] >= 5]
                .sort_values('mean', ascending=False)
                .head(15)
            )
            fig = px.bar(
                var_rating,
                x='mean',
                y='opening_variation',
                orientation='h',
                title=f'Avg Rating per Variation — {base_choice}',
                color='mean',
                color_continuous_scale='Blues',
                labels={
                    'mean': 'Avg Rating',
                    'opening_variation': 'Variation',
                },
            )
            st.plotly_chart(fig, use_container_width=True)

            # Variation vs game format
            st.markdown("##### Game Format per Variation")
            var_fmt = (
                var_df[var_df['opening_variation'].isin(top_vars)]
                .groupby(['opening_variation', 'game_format'])
                .size()
                .reset_index(name='count')
            )
            fig = px.bar(
                var_fmt,
                x='opening_variation',
                y='count',
                color='game_format',
                barmode='group',
                title=f'Format Distribution per Variation — {base_choice}',
                color_discrete_map=FORMAT_COLORS,
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# 💡 KEY INSIGHTS
# ═══════════════════════════════════════════════════════════════
elif opt == "💡 Key Insights":

    st.title("⌖ Key Insights & Takeaways ⌖")
    st.markdown("Derived from the data visualizations above.")
    st.markdown(
        """
    ### 🏆 1. The White Advantage is Real
    - **Observation:** Across all skill levels, White maintains a higher win rate than Black.
    - **Detail:** Most pronounced in **Classical** games where players have time to capitalize
      on the first-move advantage. In Bullet chess, the advantage diminishes due to time pressure.

    ### ⏱️ 2. Time Control Dictates Game End
    - **Bullet/Blitz:** High frequency of **Timeouts** (flagging).
    - **Rapid/Classical:** High frequency of **Resignations** and **Checkmates**.
      Players rarely run out of time in long formats.

    ### 📚 3. Opening Complexity vs. Skill
    - Beginners heavily favor generic "King's Pawn" openings.
    - Advanced players diversify across Sicilian, French, and Queen's Pawn openings.

    ### 📉 4. Opening vs. Game Outcome
    - Sicilian Defence and Van't Kruijs openings favor Black.
    - Scandinavian Defense and Philidor Defense favor White.

    ### 🎯 5. Rating Tier Impacts Strategy
    - Advanced players employ complex opening systems.
    - Beginners rely on fundamental strategies.

    ### 💡 6. Recommendations
    - **Beginners:** Solidify your endgame in Classical formats, avoid timeouts,
      and study standard King's Pawn openings.
    - **Intermediate Players:** Diversify your opening repertoire and practice
      time management in Blitz formats.
    - **Advanced Players:** Explore unconventional openings and analyze opponent
      tendencies to gain a competitive edge.
    """
    )
    st.success(
        "💡 Use the **Opening Explorer** page to compare openings and find "
        "the best fit for your playing style!"
    )
    st.subheader(
        "Check out the next page for data cleaning steps.", divider='grey'
    )

# ═══════════════════════════════════════════════════════════════
# 🧹 DATA CLEANING
# ═══════════════════════════════════════════════════════════════
elif opt == "🧹 Data Cleaning":

    st.title("🧹 Dataset Information & Cleaning")
    st.subheader("About the Dataset", divider='rainbow')
    st.markdown("🟢 **Source:** Kaggle – Chess Game Dataset (Lichess)")
    st.markdown("🔵 **Rows:** 20,058 games")
    st.markdown("🟠 **Time period:** 2016–2017")
    st.markdown("🔴 **Columns:** 16+ (including derived features)")

    with st.expander("🔄 Data Cleaning Steps", expanded=True):
        st.markdown(
            """
        - Dropped entirely empty rows (original has few NaNs)
        - Removed duplicate rows
        - Removed games with zero or unrealistic duration (< 0.1 min or > 180 min)
        - Extracted base time from `increment_code` → categorized into
          Bullet / Blitz / Rapid / Classical
        - Normalized opening names → base name + variation
        - Categorized average match rating into four tiers
        - Created derived features: `avg_match_rating`, `rating_diff`,
          `duration_mins`, `base_time_mins`, `rating_tier`, `game_format`,
          `opening_base`, `opening_variation`
        """
        )

    with st.expander("View Processing Code"):
        st.code(
            """
df.dropna(inplace=True)
df.drop_duplicates(inplace=True)
df['avg_match_rating'] = (df['white_rating'] + df['black_rating']) / 2
df['rating_diff'] = df['white_rating'] - df['black_rating']

rating_bins = [0, 1200, 1500, 1800, 3000]
rating_labels = ['Beginner (<1200)', 'Low-Intermediate (1200-1500)',
                 'High-Intermediate (1500-1800)', 'Advanced (>1800)']
df['rating_tier'] = pd.cut(df['avg_match_rating'], bins=rating_bins, labels=rating_labels)

df['opening_base'] = df['opening_name'].str.split(':').str[0].str.strip()
df['opening_variation'] = df['opening_name'].str.split(':').str[1].str.strip().fillna('Main Line')

df['duration_mins'] = (df['last_move_at'] - df['created_at']) / 60000.0
df = df[(df['duration_mins'] > 0.1) & (df['duration_mins'] < 180)]

df['base_time_mins'] = pd.to_numeric(
    df['increment_code'].str.split('+').str[0], errors='coerce'
).fillna(10)

format_bins = [-1, 2.9, 8, 25, 300]
format_labels = ['1. Bullet (<3m)', '2. Blitz (3-8m)', '3. Rapid (9-25m)', '4. Classical (>25m)']
df['game_format'] = pd.cut(df['base_time_mins'], bins=format_bins, labels=format_labels)
            """,
            language="python",
        )

    st.markdown("---")
    st.subheader("Sample of Cleaned Data")
    st.dataframe(df.head(10), use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# 🤖 CHAT BOT
# ═══════════════════════════════════════════════════════════════
elif opt == "🤖 Chat Bot":

    st.title("♟️ Chess Chatbot")

    API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
    if not API_KEY:
        st.error(
            "OpenRouter API key not found. "
            "Add it to `.streamlit/secrets.toml` as `OPENROUTER_API_KEY`."
        )
        st.stop()

    # Initialize conversation history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # System prompt with dataset context
    system_msg = {
        "role": "system",
        "content": (
            "You are a chess analytics assistant. The user has a dataset of "
            "~20,000 Lichess games with columns: ratings, openings, time controls, "
            "outcomes, turns, victory status, etc. Answer questions about chess "
            "strategy, openings, and data insights helpfully and concisely."
        ),
    }

    # Display existing history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    question = st.chat_input("Ask a chess or data question...")

    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Send last 10 messages for context
        messages = [system_msg] + st.session_state.chat_history[-10:]

        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "poolside/laguna-m.1:free",
                        "messages": messages,
                    },
                    timeout=30,
                )
            except requests.exceptions.Timeout:
                st.error("Request timed out. Please try again.")
                response = None
            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}")
                response = None

        if response is not None and response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )
            with st.chat_message("assistant"):
                st.markdown(answer)
        elif response is not None:
            st.error(f"Error {response.status_code}: {response.text}")

    # Clear button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()