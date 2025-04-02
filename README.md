# CryptoPulse: Cryptocurrency Sentiment Analysis System

An automated system that analyzes cryptocurrency news, market data, and blockchain trends to provide personalized trading recommendations based on crypto market sentiment.

## Features

- **Multi-Agent Architecture**: Leverages crewAI to orchestrate specialized agents for different aspects of crypto market analysis
- **Daily Sentiment Analysis**: Collects and analyzes global cryptocurrency news, token-specific developments, and market trends
- **Portfolio-Aware Recommendations**: Generates trading recommendations tailored to user's crypto portfolio and preferences
- **Caching System**: Efficiently reuses API responses to minimize costs
- **API & CLI Interfaces**: Access via RESTful API or command line

## Setup Instructions

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/cryptopulse-backend.git
cd cryptopulse-backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy the environment template
cp .env.template .env

# Edit .env and add your API keys
# You'll need:
# - OpenAI API key
# - Bing Search API key
# - CoinMarketCap API key
```

### 3. Create Portfolio and Preferences Files

See examples in the `examples/` directory:
- `portfolio.json`: Your cryptocurrency holdings
- `preferences.json`: Your investment preferences

### 4. Running the Application

#### Via CLI:

```bash
# Run a one-time analysis
python -m src.marketpulse.cli --portfolio examples/portfolio.json --preferences examples/preferences.json --output analysis.json
```

#### As a Web Service:

```bash
# Start the API server
python app.py

# The API will be available at:
# http://localhost:8000/api/sentiment/analyze (POST)
# http://localhost:8000/api/sentiment/demo (GET)
```

## API Usage

### Analyze Portfolio Sentiment

```bash
curl -X POST http://localhost:8000/api/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d @examples/request.json
```

Where `request.json` contains:

```json
{
  "portfolio": {
    "holdings": [
      {"symbol": "BTC", "name": "Bitcoin", "allocation": 40, "category": "Layer 1"},
      {"symbol": "ETH", "name": "Ethereum", "allocation": 30, "category": "Layer 1"},
      {"symbol": "SOL", "name": "Solana", "allocation": 15, "category": "Layer 1"},
      {"symbol": "LINK", "name": "Chainlink", "allocation": 10, "category": "Oracle"},
      {"symbol": "UNI", "name": "Uniswap", "allocation": 5, "category": "DeFi"}
    ]
  },
  "preferences": {
    "risk_tolerance": "aggressive",
    "preferred_categories": ["Layer 1", "DeFi", "Gaming"],
    "investment_horizon": "medium-term"
  }
}
```

## Deployment

The application is designed to be deployed on Railway or similar platforms:

```bash
# Deploy to Railway
railway up
```

## Cost Optimization

The system uses several cost-optimization strategies:

1. **Intelligent Caching**: API responses are cached to avoid redundant calls (with shorter timeframes for crypto's volatility)
2. **Shared Global Analysis**: Market-wide data is shared among all users
3. **GPT-4o-mini**: Uses efficient LLM to minimize token costs
4. **24/7 Analysis**: Unlike traditional markets, crypto trades 24/7, so the system is designed for continuous analysis

## Future Enhancements

- Integration with popular crypto wallets for automated portfolio importing
- On-chain metrics integration for deeper insights
- Technical indicator analysis
- Social sentiment analysis from crypto Twitter/Discord/Telegram
- User dashboard for tracking recommendation performance
- Custom news source integrations