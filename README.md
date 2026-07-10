# ♟️ Chessalytics

**Chessalytics** is an interactive data analytics dashboard built with **Streamlit** that explores over **20,000 chess games** from the Lichess dataset. It provides insightful visualizations, statistical analysis, feature engineering, and an AI-powered chatbot to help users understand chess trends, openings, and gameplay patterns.

---

## 🚀 Features

### 🏠 Home Dashboard
- Dataset overview
- Key performance metrics
- Rating tier distribution
- Game format distribution

### 📊 Data Analysis
- Dataset preview
- Summary statistics
- Top-performing chess openings
- Popular opening analysis

### 📈 Interactive Visualizations
- Overall game outcomes
- Opening popularity
- Success rates by rating tier
- Opening vs game outcome
- White advantage analysis
- Time control analysis
- Rating vs opening depth
- Move count distributions
- Time vs number of moves

### 💡 Key Insights
Actionable insights generated from the analysis including:
- White first-move advantage
- Impact of time controls
- Opening preferences by skill level
- Strategic recommendations for beginners, intermediate and advanced players

### 🧹 Data Cleaning
Displays:
- Dataset information
- Cleaning process
- Feature engineering steps
- Sample cleaned dataset

### 🤖 Chess Chatbot
Integrated AI chatbot powered by **OpenRouter API** that can answer:
- Chess-related questions
- Opening explanations
- Strategy suggestions
- General chess concepts

---

# 📂 Dataset

- **Source:** Kaggle (Lichess Chess Games Dataset)
- **Games:** 20,058
- **Time Period:** 2016–2017

Dataset contains information such as:
- Player ratings
- Winner
- Opening played
- Number of turns
- Time controls
- Victory status
- Rated/Casual games

---

# ⚙️ Data Processing

The dataset undergoes several preprocessing steps:

- Removed missing values
- Removed duplicate records
- Removed unrealistic game durations
- Extracted base opening names
- Calculated average player rating
- Categorized players into rating tiers
- Classified games into:
  - Bullet
  - Blitz
  - Rapid
  - Classical
- Created additional analytical features for visualization

---

# 🛠️ Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Requests
- OpenRouter API

---

# 📦 Installation

Clone the repository

```bash
git clone https://github.com/yourusername/chessalytics.git
```

Move into the project

```bash
cd chessalytics
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 API Setup

Create a file:

```
.streamlit/secrets.toml
```

Add your OpenRouter API key

```toml
OPENROUTER_API_KEY="your_api_key_here"
```

**Do NOT commit this file to GitHub.**

---

# ▶️ Run the App

```bash
streamlit run chess1.py
```

---

# 📁 Project Structure

```
Chessalytics/
│
├── chess1.py
├── games.csv
├── requirements.txt
├── .gitignore
├── README.md
└── .streamlit/
    └── secrets.toml (local only)
```

---

# 📊 Sample Visualizations

The dashboard includes interactive visualizations such as:

- Game Outcome Distribution
- Rating Tier Distribution
- Opening Popularity Heatmap
- Success Rate Analysis
- White Advantage Analysis
- Time Control Distribution
- Move Duration Correlation
- Opening Performance

---

# 🎯 Future Improvements

- PGN upload and automatic game analysis
- Stockfish engine integration
- Player vs Player comparison
- Opening recommendation system
- Move quality analysis
- AI-generated game reports

---

# 🙌 Acknowledgements

- Lichess
- Kaggle
- Streamlit
- Plotly
- OpenRouter

---

# 📄 License

This project is intended for educational and learning purposes.
