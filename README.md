# ♟️ Chessalytics

Chessalytics is an interactive data analytics dashboard built with **Streamlit** that explores over **20,000 chess games** from the Lichess dataset. The dashboard provides interactive visualizations, statistical insights, and an AI-powered chatbot to help users analyze chess openings, player ratings, game outcomes, and gameplay trends.

---

## 🚀 Features

### 🏠 Dashboard
- Dataset overview
- Key performance metrics
- Rating tier distribution
- Game format distribution

### 📊 Data Analysis
- Dataset preview
- Summary statistics
- Top-performing chess openings
- Opening popularity analysis

### 📈 Interactive Visualizations
- Game outcome distribution
- Opening popularity
- Success rates by rating tier
- Opening vs. game outcome
- White advantage analysis
- Time control analysis
- Rating vs. opening depth
- Move count distribution
- Game duration vs. number of moves

### 💡 Key Insights
The dashboard highlights important chess trends, including:
- White first-move advantage
- Impact of different time controls
- Opening preferences across rating levels
- Strategic recommendations for beginners, intermediate, and advanced players

### 🧹 Data Cleaning & Feature Engineering
The application demonstrates the complete preprocessing workflow by:
- Removing missing and duplicate records
- Cleaning unrealistic game durations
- Extracting base opening names
- Calculating average player ratings
- Creating rating tiers
- Categorizing games into Bullet, Blitz, Rapid, and Classical formats
- Generating additional analytical features for visualization

### 🤖 AI Chess Chatbot
An integrated chatbot powered by the OpenRouter API allows users to ask questions about:
- Chess openings
- Game strategies
- Chess concepts
- Gameplay trends within the dataset

---

## 📂 Dataset

**Source:** Kaggle – Lichess Chess Games Dataset

The dataset contains over **20,000 chess games** played on Lichess between **2016 and 2017**, including:

- Player ratings
- Game outcomes
- Opening names
- Number of moves
- Time controls
- Victory status
- Rated and casual games

---

## 🛠️ Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Requests
- OpenRouter API

---

## 📁 Project Structure

```
Chessalytics/
│
├── chess1.py
├── games.csv
├── requirements.txt
├── README.md
└── .streamlit/
```

---

## 📊 Dashboard Preview

The dashboard includes interactive visualizations such as:

- Game Outcome Distribution
- Rating Tier Distribution
- Opening Popularity
- Success Rate Analysis
- White Advantage Analysis
- Time Control Analysis
- Move Count Distribution
- Opening Performance Comparison

*(Add screenshots here after uploading them to your repository.)*

---

## 🎯 Future Improvements

- PGN upload and automatic game analysis
- Stockfish engine integration
- Player vs. Player comparison
- Opening recommendation system
- Move quality analysis
- AI-generated game reports

---

## 🙌 Acknowledgements

- Lichess
- Kaggle
- Streamlit
- Plotly
- OpenRouter

---

## 📄 License

This project was developed for educational and learning purposes.
