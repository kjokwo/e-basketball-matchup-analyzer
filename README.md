🏀 E-Basketball Matchup & Spread Analyzer

A Python-based **command-line application** that analyzes head-to-head e-basketball matchups using real match data from a REST API.  
The tool computes win/loss records, average margins, recent form, and identifies score spread lines with high historical hit rates.

---

 📌 Features
- Fetches real historical match data via a REST API  
- Analyzes head-to-head records** between two players  
- Calculates average margin of victory 
- Evaluates recent form over customizable game ranges  
- Identifies spread lines with 80–100% historical hit rates 
- Interactive command-line interface (CLI) with menu-based navigation  
- Handles API pagination and missing or missing data safely  

---

🛠️ Tech Stack
- Python
- Requests (HTTP requests)
- REST API integration
- JSON parsing
- Command-Line Interface (CLI)



🚀 Getting Started

1. Clone the repository
bash
git clone https://github.com/kjokwo/e-basketball-matchup-analyzer.git
cd e-basketball-matchup-analyzer
2. Install dependencies
pip install requests

3. Configure API Token

This project uses a third-party sports data API.

Inside the Python file, replace:

API_TOKEN = "YOUR_API_TOKEN"


with your own API token.

▶️ Running the Application
python main.py


You will be prompted with a menu:

1. Analyze Matchup (Spreads & Stats)
2. Analyze Form (Recent Performance)
3. Exit

📊 Example Output

The application outputs:

Head-to-head win/loss records

Average scoring margins

Recent win percentages

Spread lines with historical hit rates displayed in the terminal

🧠 How It Works

Sends HTTP requests to a sports data REST API

Retrieves and parses JSON responses

Extracts match data such as scores and player IDs

Applies custom statistical logic to analyze performance trends

Displays results through an interactive CLI

🧪 Error Handling

Gracefully handles missing or malformed API responses

Prevents crashes from invalid user input

Stops pagination automatically when no more results are available

🔮 Future Improvements

Convert the CLI tool into a Flask REST API

Add unit tests using pytest

Add data visualizations for performance trends

Refactor the codebase into object-oriented design

Deploy as a web-based analytics service

👤 Author

Kobi Okonkwo
Bachelor of Science, Computer Science
Founder – WebMotive
🌐 https://webmotiveco.com******
