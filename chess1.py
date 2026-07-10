import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import json
import requests


df=pd.read_csv("games.csv")
df.dropna(inplace=True)
df.drop_duplicates(inplace=True)
df['avg_match_rating'] = (df['white_rating'] + df['black_rating']) / 2
df['rating_diff'] = df['white_rating'] - df['black_rating'] # White's perspective

rating_bins = [0, 1200, 1500, 1800, 3000]
rating_labels = ['Beginner (<1200)', 'Low-Intermediate (1200-1500)', 
                     'High-Intermediate (1500-1800)', 'Advanced (>1800)']
df['rating_tier'] = pd.cut(df['avg_match_rating'], bins=rating_bins, labels=rating_labels)

df['opening_base'] = df['opening_name'].str.split(':').str[0].str.strip()

df['duration_mins'] = (df['last_move_at'] - df['created_at']) / 60000.0

df = df[(df['duration_mins'] > 0.1) & (df['duration_mins'] < 180)]

df['base_time_mins'] = pd.to_numeric(df['increment_code'].str.split('+').str[0], errors='coerce').fillna(10)

format_bins = [-1, 2.9, 8, 25, 300]
format_labels = ['1. Bullet (<3m)', '2. Blitz (3-8m)', '3. Rapid (9-25m)', '4. Classical (>25m)']
df['game_format'] = pd.cut(df['base_time_mins'], bins=format_bins, labels=format_labels)
    

def get_top_performing_openings(data_subset, min_games=40):
    """Filters for popular openings and calculates an effective win rate."""
    counts = data_subset['opening_base'].value_counts()
    valid_openings = counts[counts >= min_games].index
    filtered = data_subset[data_subset['opening_base'].isin(valid_openings)]
    
    win_rates = filtered.groupby('opening_base')['winner'].value_counts(normalize=True).unstack().fillna(0)
    if 'draw' not in win_rates.columns:
        win_rates['draw'] = 0
   
    win_rates['success_score'] = win_rates.get('white', 0) + (0.5 * win_rates['draw'])
    return win_rates.sort_values(by='success_score', ascending=False).head(10).reset_index()

st.set_page_config(page_title="Mera page", page_icon=":white_chess_king:", layout="wide")

with st.sidebar:
    st.title("♛Chessalytics♛")
    opt = st.radio("Select a page", ["𖠿Home", "🗁Data Analysis", "𖥸Visualizations","𖡊Key Insights","𓀧Data Cleaning","🖳Chat Bot"], key="page_selector")

if opt == "𖠿Home":
    
    st.title("♔Welcome to the Chess Data Analysis App♔")
    st.subheader("   Advanced chess analytics and trend analyser system ⚚  ",divider="rainbow")
    st.markdown("""
    This application provides a deep dive into over 20,000 chess games. 
    Explore win rates, opening theories, time control impacts, and player skill dynamics.
    """)
    st.markdown("### Key Metrics")
    st.markdown("#### Overview of the dataset")

    col1,col2,col3,col4,col5,col6 = st.columns(6)
    col1.metric("Total Games", f"{len(df):,}",border=True)
    col2.metric("Total Unique Openings", df['opening_base'].nunique(),border=True)
    col3.metric("Total Columns", df.shape[1],border=True)
    col4.metric("Avg Rating", f"{df['avg_match_rating'].mean():.0f}",border=True)
    col5.metric("Avg Turns", f"{df['turns'].mean():.1f}",border=True)
    col6.metric("Empty records", df.isnull().sum().sum(),border=True)

    ch1,ch2=st.columns(2)

    with ch1:
     format_counts = df['game_format'].value_counts()
     fg = px.histogram(df, x='game_format', color='game_format', title='Game Format Distribution',
               color_discrete_map={
                     '1. Bullet (<3m)': '#FF5733', 
                    '2. Blitz (3-8m)': '#33FF57',
                    '3. Rapid (9-25m)': '#3357FF',
                    '4. Classical (>25m)': '#F1C40F'



               }
               )
     st.plotly_chart(fg)

    with ch2:
     rating_counts = df['rating_tier'].value_counts()
     fg2 = px.histogram(df, x='rating_tier', color='rating_tier', title='Rating Tier Distribution',
                color_discrete_map={
                    'Beginner (<1200)': '#FF5733', 
                    'Low-Intermediate (1200-1500)': '#33FF57', 
                    'High-Intermediate (1500-1800)': '#3357FF', 
                    'Advanced (>1800)': '#F1C40F'
                })
     st.plotly_chart(fg2)
    st.markdown("#### Explore the other sections for detailed analysis and visualizations.")
    st.badge("Use the sidebar to navigate through different sections of the app.", color="blue")
    st.subheader("Checkout the next page for data overview and analysis",divider='grey')

elif opt == "🗁Data Analysis":
    st.title("⌖Data overview and Analysis⌖")
    st.subheader("This section provides an overview and  analysis of the chess games dataset.",divider="rainbow")
    
    st.subheader("Dataset Overview",divider='green')
    st.write(df.head())
    
    st.subheader("Summary Statistics",divider='green')
    st.write(df.describe())
    
    st.subheader("Top Performing Openings",divider='green')
    top_openings = get_top_performing_openings(df)
    st.write(top_openings)
    st.subheader("Checkout next page for visualizations and insights",divider='grey')

elif opt == "𖥸Visualizations":
    st.title("⌖Visualizations⌖")
    st.subheader("This section provides visual insights into the chess games dataset.",divider="rainbow")

    t1,t2,t3,t4 = st.tabs(["Macro Trends", "Opening Analysis", "Dynamic Insights", "Advanced Visualizations"])
    with t1:
        st.markdown("👉Win Rate & Format Volume")
        c1,c2=st.columns(2)
        with c1:
         fig = px.pie(df, names='winner', title='1. Overall Match Outcome Share',color ='winner',
                         color_discrete_map={'white': '#EDEDED', 'black': '#004242', 'draw': '#7F7F7F'}, hole=0.4)
         st.plotly_chart(fig, use_container_width=True)
        with c2:
         fig = px.pie(df, names='game_format', title='2. Pace of Play (Game Formats)', 
                         color_discrete_sequence=px.colors.sequential.Plasma, hole=0.4)
         st.plotly_chart(fig, use_container_width=True)
        st.subheader("Checkout next tab for opening analysis and insights",divider='grey')
    with t2:

        st.markdown("👉opening Analysis with Success Rates")
        top_10 = df['opening_base'].value_counts().head(10).reset_index()
        fig = px.bar(top_10, x='count', y='opening_base', orientation='h', title='3. Top 10 Most Frequently Played Openings',color='opening_base', color_discrete_sequence=px.colors.sequential.Plasma)
        st.plotly_chart(fig, use_container_width=True)
        
        
        top_openings_list = df['opening_base'].value_counts().head(12).index
        heatmap_data = df[df['opening_base'].isin(top_openings_list)].groupby(['rating_tier', 'opening_base']).size().reset_index(name='count')
        fig = px.density_heatmap(heatmap_data, x='rating_tier', y='opening_base', z='count',
                                    title='4. Opening Popularity Matrix Across Skill Levels', color_continuous_scale='Viridis', labels={'count': 'Number of Games'})
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("->Success Rates")

        st.selectbox("Select Rating Tier for Success Rate Analysis", options=['Beginner (<1200)', 'Intermediate (1200-1800)', 'Advanced (>1800)'], key='success_rate_tier')
        if st.session_state.success_rate_tier == 'Beginner (<1200)':
         beg_win = get_top_performing_openings(df[df['rating_tier'] == 'Beginner (<1200)'], min_games=20)
         if not beg_win.empty:
                fig = px.bar(beg_win, x='success_score', y='opening_base', orientation='h',
                             title='5. Highest Success Openings for Beginners', color='success_score', color_continuous_scale= 'viridis')
                st.plotly_chart(fig, use_container_width=True)
        elif st.session_state.success_rate_tier == 'Intermediate (1200-1800)':
         int_win = get_top_performing_openings(df[df['rating_tier'].isin(['Low-Intermediate (1200-1500)', 'High-Intermediate (1500-1800)'])], min_games=50)
         if not int_win.empty:
                fig = px.bar(int_win, x='success_score', y='opening_base', orientation='h',
                             title='6. Highest Success Openings for Intermediates', color='success_score', color_continuous_scale='Bluered')
                st.plotly_chart(fig, use_container_width=True)
        elif st.session_state.success_rate_tier == 'Advanced (>1800)':
         adv_win = get_top_performing_openings(df[df['rating_tier'] == 'Advanced (>1800)'], min_games=30)
         if not adv_win.empty:
                fig = px.bar(adv_win, x='success_score', y='opening_base', orientation='h',
                             title='7. Highest Success Openings for Advanced Players', color='success_score', color_continuous_scale='Plasma')
                st.plotly_chart(fig, use_container_width=True)
        top_openings = df['opening_name'].value_counts().head(10).index


        filtered_df = df[df['opening_name'].isin(top_openings)]
        opening_vs_winner = pd.crosstab(filtered_df['opening_name'], filtered_df['winner'])
        opening_vs_winner_pct = opening_vs_winner.div(opening_vs_winner.sum(axis=1), axis=0) * 100
        opening_vs_winner_pct = opening_vs_winner_pct.reset_index()
        fig = px.bar(opening_vs_winner_pct,
             x='opening_name',
             y=['white', 'black', 'draw'],
             title="7. Opening vs Game Outcome (%)",
             barmode='stack',
            color_discrete_map={
            'white': '#F8F9FA',
            'black': '#343A40',
            'draw': '#ADB5BD'
               },
             opacity=0.8
             )
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Checkout next tab for dynamic insights and correlations",divider='grey')

    with t3:
        st.markdown("👉 Termination & Rating Impact")
        c1, c2 = st.columns(2)
        fig = px.histogram(df, x='game_format', color='victory_status', barmode='stack',
                                title='8. How Games End Based on Time Controls',color_discrete_sequence=px.colors.sequential.Plasma)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("->White Advantage by Rating Tier")
        fig = px.histogram(df, x='rating_tier', color='winner', barmode='group',
                            title=" 9. Does White's Advantage Change with Skill?", color_discrete_map={'white': '#EDEDED', 'black': '#3A3A3A', 'draw': '#7F7F7F'})
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("-> White Advantage by Time Control")
        format_winner = df[df['winner'] != 'draw']
        fig = px.histogram(format_winner, x='game_format', color='winner', barmode='group',
                           title=" 10. Does Time Pressure Increase White's First-Move Advantage?", color_discrete_map={'white': '#EDEDED', 'black': '#3A3A3A'})
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Checkout next tab for advanced metrics and correlations",divider='grey')

    with t4:
        st.markdown("👉Time & Moves Correlation")
        df_sample = df.sample(n=min(len(df), 3000), random_state=42)
        c1, c2 = st.columns(2)
        
        fig = px.scatter(df_sample, x='turns', y='duration_mins', color='game_format',
                              title=' 11. Physical Time Spent vs. Number of Moves Played', opacity=0.6,
                              
                              color_discrete_map={
                                  '1. Bullet (<3m)': '#dc143c', 
                                  '2. Blitz (3-8m)': '#c0c0c0', 
                                  '3. Rapid (9-25m)': '#9400d3', 
                                  '4. Classical (>25m)': '#ff8c00'
                              })
        st.plotly_chart(fig, use_container_width=True)
        
        fig = px.box(df, x='game_format', y='turns', color='game_format',
                        title=' 12. Turn Count Distributions by Game Format', color_discrete_sequence=px.colors.sequential.Plasma)
        st.plotly_chart(fig, use_container_width=True)
            
        st.markdown(" ->Advanced Metrics")
        
        fig = px.scatter(df_sample, x='avg_match_rating', y='opening_ply', trendline='ols',
                              title=' 13. Theoretical Opening Depth Stickiness vs Player ELO', opacity=0.4,
                              color_discrete_sequence=['#1f77b4'])
        st.plotly_chart(fig, use_container_width=True)
        
        fig = px.box(df, x='rated', y='turns', color='winner',
                        title=' 14. Casual vs. Competitive Match Turn Spans',
                        color_discrete_map={'white': '#f8f8ff', 'black': '#006b3c ', 'draw': '#708090'})
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("These graphs helped us understand the data better. Checkout the next page for the key insights. ",divider='grey')       

     


elif opt == "𖡊Key Insights":
    st.title("⌖Key Insights and Takeaways⌖")
    st.markdown("Derived from the data visualizations above.")
    st.markdown("""
    ### 🏆 1. The White Advantage is Real
    - **Observation:** Across all skill levels, White maintains a higher win rate than Black.
    - **Detail:** This advantage is most pronounced in **Classical** games where players have time to capitalize on the first-move advantage. In Bullet chess, the advantage diminishes due to time pressure.
    
    ### ⏱️ 2. Time Control Dictates Game End
    - **Observation:** How a game ends depends heavily on the clock.
    - **Detail:** 
        - **Bullet/Blitz:** High frequency of **Timeouts** (Flagging).
        - **Rapid/Classical:** High frequency of **Resignations** and **Checkmates**. Players rarely run out of time in long formats.
    
    ### 📚 3. Opening Complexity vs. Skill
    - **Observation:** Beginners stick to simple openings; Advanced players diversify.
    - **Detail:** The heatmap shows Beginners heavily favoring generic "King's Pawn" openings. Advanced players show a wider distribution across Sicilian, French, and Queen's Pawn openings.
    
    ### 📉 4. Opening vs. Game outcome (%)
    - **Observation:** Certain openings lead to higher win rates for specific players.
    - **Detail:** The bar chart shows that 'Sicilian Defence' and 'Van't Krujis' openings have higher win rates for Black, while white pieces have higher chance of winning with 'Scandinavian Defense' and 'Philidor Defense'.
    
    ### 🎯 5. Rating Tier Impacts Strategy
    - **Observation:** Players in different rating tiers exhibit distinct strategic preferences.
    - **Detail:** Advanced players are more likely to employ complex opening systems, while beginners tend to rely on fundamental strategies.

    ### 💡 6. Key Recommendations for Players
    - **Beginners:** Focus on solidifying your endgame in Classical formats, avoid timeouts, and study standard King's Pawn openings.
    - **Intermediate Players:** Diversify your opening repertoire and practice time management in Blitz formats.
    - **Advanced Players:** Explore unconventional openings and analyze opponent tendencies to gain a competitive edge.
    """)
    st.success("💡 **Recommendation:** If you are a beginner, focus on solidifying your endgame in Classical formats, avoid timeouts, and study standard King's Pawn openings.")
    st.subheader("Checkout next page for data cleaning steps and dataset overview",divider='grey')


    

elif opt == "𓀧Data Cleaning":
    st.title("🧹 Dataset Information & Cleaning")
    st.subheader('About the Dataset',divider='rainbow')
    st.badge("Source: Kaggle – Chess Game Dataset (Lichess)", color="green")
    st.badge("Rows: 20,058 games", color="blue")
    st.badge("Time period: 2016–2017", color="orange")
    st.badge("Columns: 16 columns including players, ratings, moves, openings, victory status, etc.", color="red")


    st.markdown("### Dataset Overview")
   
    with st.expander("🔄 Data Cleaning Steps", expanded=True):
        st.markdown("""
        - **Dropped any entirely empty rows** (original has few NaNs)
        - **Removed games with zero or unrealistic duration** (< 0.1 minutes or > 180 minutes)
        - **Cleaned increment_code** to extract base time (minutes) and categorize into Bullet / Blitz / Rapid / Classical
        - **Normalized opening names** by taking the base variation before colon (e.g., "Sicilian Defense: …" → "Sicilian Defense")
        - **Categorized average match rating** into four tiers (Beginner, Low-Intermediate, High-Intermediate, Advanced)
        - **Created derived features**: `avg_match_rating`, `rating_diff`, `duration_mins`, `base_time_mins`, `rating_tier`, `game_format`, `opening_base`
        """)

    with st.expander("View Processing Code"):
        st.code("""
        df.dropna(inplace=True)
        df.drop_duplicates(inplace=True)
        df['avg_match_rating'] = (df['white_rating'] + df['black_rating']) / 2
        df['rating_diff'] = df['white_rating'] - df['black_rating'] # White's perspective

        rating_bins = [0, 1200, 1500, 1800, 3000]
        rating_labels = ['Beginner (<1200)', 'Low-Intermediate (1200-1500)', 
                 'High-Intermediate (1500-1800)', 'Advanced (>1800)']
        df['rating_tier'] = pd.cut(df['avg_match_rating'], bins=rating_bins, labels=rating_labels)

        df['opening_base'] = df['opening_name'].str.split(':').str[0].str.strip()

        df['duration_mins'] = (df['last_move_at'] - df['created_at']) / 60000.0

        df = df[(df['duration_mins'] > 0.1) & (df['duration_mins'] < 180)]

        df['base_time_mins'] = pd.to_numeric(df['increment_code'].str.split('+').str[0], errors='coerce').fillna(10)

        format_bins = [-1, 2.9, 8, 25, 300]
        format_labels = ['1. Bullet (<3m)', '2. Blitz (3-8m)', '3. Rapid (9-25m)', '4. Classical (>25m)']
        df['game_format'] = pd.cut(df['base_time_mins'], bins=format_bins, labels=format_labels)


        """, language="python")


    st.markdown("---")
    st.subheader("Sample of cleaned data")
    st.dataframe(df.head(10), use_container_width=True) 


elif opt == "🖳Chat Bot":

 import os
 API_KEY=st.secrets["OPENROUTER_API_KEY"]



 st.title("♟️ Chess Chatbot")

# Check if API key exists
 if not API_KEY:
    st.error("OpenRouter API key not found.")
    st.stop()

 question = st.text_input("Ask a question")

 if st.button("Ask") and question:

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "poolside/laguna-m.1:free",
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ],
        },
    )

    if response.status_code == 200:
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        st.write(answer)
    else:
        st.error(f"Error {response.status_code}")
        st.write(response.text)