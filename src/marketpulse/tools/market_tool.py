import logging
logging.getLogger('opentelemetry.trace').setLevel(logging.ERROR)

from crewai.tools import BaseTool
from typing import Type, List, Optional
from pydantic import BaseModel, Field
from langchain_community.utilities import BingSearchAPIWrapper
import os
import requests
from datetime import datetime, timedelta
import json

class NewsSearchInput(BaseModel):
    """Input schema for NewsSearchTool."""
    query: str = Field(
        ...,
        description="Search query to find cryptocurrency news."
    )

class FinancialNewsSearchTool(BaseTool):
    name: str = "crypto_news_search"
    description: str = (
        "Use this tool to search for cryptocurrency and blockchain news. "
        "It can find articles about cryptocurrencies, blockchain projects, DeFi, "
        "NFTs, and crypto market trends from specialized news sources."
    )
    args_schema: Type[BaseModel] = NewsSearchInput
    bing_search: BingSearchAPIWrapper = None

    def __init__(self):
        super().__init__()
        self.bing_search = BingSearchAPIWrapper(
            bing_subscription_key=os.getenv('BING_SUBSCRIPTION_KEY'),
            bing_search_url="https://api.bing.microsoft.com/v7.0/search"
        )

    def _run(self, query: str) -> str:
        """Run the tool with caching and usage tracking"""
        cache_dir = ".cache/news"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Create a cache key based on the query
        cache_key = "".join(x for x in query if x.isalnum() or x.isspace()).lower().replace(" ", "_")
        cache_file = f"{cache_dir}/{cache_key}.json"
        
        # Check if we have a cached result for this query from today
        if os.path.exists(cache_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if file_time.date() == datetime.now().date():
                with open(cache_file, 'r') as f:
                    return f.read()
        
        # If no cache or cache is old, make the actual API call
        try:
            # Update search query to focus on cryptocurrency news
            results = self.bing_search.run(f"cryptocurrency crypto blockchain news {query}")
            
            # Create logs directory if it doesn't exist
            os.makedirs(".logs", exist_ok=True)
            
            # Log usage
            with open(".logs/bing_usage.log", "a") as log:
                log.write(f"{datetime.now().isoformat()},query,{query}\n")
            
            # Cache the results
            with open(cache_file, 'w') as f:
                f.write(results)
                
            return results
        except Exception as e:
            return f"Error performing search: {str(e)}"


class CryptoQuoteInput(BaseModel):
    """Input schema for CryptoQuoteTool."""
    symbol: str = Field(
        ...,
        description="Cryptocurrency symbol to get quote data for (e.g., 'BTC', 'ETH')."
    )

class CryptoCategory(BaseModel):
    """Represents a cryptocurrency category."""
    name: str = Field(..., description="Category name (e.g., 'Layer 1', 'DeFi', 'NFT Platform')")
    id: Optional[str] = Field(None, description="Category ID in the CoinMarketCap system")

class CryptoQuoteTool(BaseTool):
    name: str = "crypto_quote"
    description: str = (
        "Use this tool to get current cryptocurrency price data and basic information. "
        "Provide a cryptocurrency symbol to get current price, change, volume, market cap, "
        "and other basic data."
    )
    args_schema: Type[BaseModel] = CryptoQuoteInput

    def _run(self, symbol: str) -> str:
        """Run the tool to get cryptocurrency quote data"""
        cache_dir = ".cache/quotes"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Create a cache file for this symbol
        cache_file = f"{cache_dir}/{symbol.upper()}.json"
        
        # Check if we have a recent cached result (less than 30 minutes old for crypto)
        if os.path.exists(cache_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_time < timedelta(minutes=30):
                with open(cache_file, 'r') as f:
                    return f.read()
        
        # If no cache or cache is old, make the actual API call
        try:
            # Using CoinMarketCap API
            api_key = os.getenv('COINMARKETCAP_API_KEY')
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            
            headers = {
                'X-CMC_PRO_API_KEY': api_key,
                'Accept': 'application/json'
            }
            
            # Convert common symbols to their IDs if needed
            # For simplicity, use symbol directly - in production, you might want to convert BTC -> bitcoin, etc.
            params = {
                'symbol': symbol.upper(),
                'convert': 'USD'
            }
            
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            # Create logs directory if it doesn't exist
            os.makedirs(".logs", exist_ok=True)
            
            # Log usage
            with open(".logs/coinmarketcap_usage.log", "a") as log:
                log.write(f"{datetime.now().isoformat()},quote,{symbol}\n")
            
            # Format the response
            if 'data' in data and symbol.upper() in data['data']:
                crypto_data = data['data'][symbol.upper()]
                quote = crypto_data['quote']['USD']
                
                # Extract category data if available
                category = None
                if 'category' in crypto_data:
                    category = crypto_data['category']
                
                result = {
                    "symbol": crypto_data['symbol'],
                    "name": crypto_data['name'],
                    "price": str(quote['price']),
                    "change_24h": str(quote['percent_change_24h']),
                    "change_7d": str(quote['percent_change_7d']),
                    "volume_24h": str(quote['volume_24h']),
                    "market_cap": str(quote['market_cap']),
                    "category": category,
                    "last_updated": quote['last_updated']
                }
                formatted_result = json.dumps(result, indent=2)
                
                # Cache the result
                with open(cache_file, 'w') as f:
                    f.write(formatted_result)
                
                return formatted_result
            else:
                error_message = data.get('status', {}).get('error_message', f"Could not retrieve quote data for {symbol}")
                return f"Error: {error_message}"
                
        except Exception as e:
            return f"Error retrieving cryptocurrency quote: {str(e)}"


class CryptocurrencyListInput(BaseModel):
    """Input schema for CryptocurrencyListTool."""
    limit: int = Field(
        default=100,
        description="Number of cryptocurrencies to retrieve (1-5000)."
    )
    category: Optional[str] = Field(
        None,
        description="Category filter (e.g., 'defi', 'layer-1', 'nft')"
    )

class CryptocurrencyListTool(BaseTool):
    name: str = "crypto_list"
    description: str = (
        "Use this tool to get a list of top cryptocurrencies by market cap. "
        "You can filter by category and limit the number of results."
    )
    args_schema: Type[BaseModel] = CryptocurrencyListInput

    def _run(self, limit: int = 100, category: Optional[str] = None) -> str:
        """Run the tool to get list of cryptocurrencies"""
        cache_dir = ".cache/crypto_lists"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Create a cache key
        cache_key = f"top_{limit}"
        if category:
            cache_key += f"_{category.lower()}"
        cache_file = f"{cache_dir}/{cache_key}.json"
        
        # Check if we have a recent cached result (less than 6 hours old)
        if os.path.exists(cache_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - file_time < timedelta(hours=6):
                with open(cache_file, 'r') as f:
                    return f.read()
        
        # If no cache or cache is old, make the actual API call
        try:
            # Using CoinMarketCap API
            api_key = os.getenv('COINMARKETCAP_API_KEY')
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
            
            headers = {
                'X-CMC_PRO_API_KEY': api_key,
                'Accept': 'application/json'
            }
            
            params = {
                'limit': min(limit, 5000),  # Cap at 5000 which is CMC's max
                'convert': 'USD',
                'sort': 'market_cap',
                'sort_dir': 'desc'
            }
            
            # Add category filter if provided
            if category:
                # In production, map common category names to CMC's category IDs
                # For simplicity, we're using the category name directly
                params['cryptocurrency_type'] = category
            
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            # Create logs directory if it doesn't exist
            os.makedirs(".logs", exist_ok=True)
            
            # Log usage
            with open(".logs/coinmarketcap_usage.log", "a") as log:
                log.write(f"{datetime.now().isoformat()},list,limit={limit},category={category}\n")
            
            # Format the response
            if 'data' in data:
                # Extract relevant info from each cryptocurrency
                results = []
                for crypto in data['data']:
                    quote = crypto['quote']['USD']
                    results.append({
                        "symbol": crypto['symbol'],
                        "name": crypto['name'],
                        "price": quote['price'],
                        "market_cap": quote['market_cap'],
                        "volume_24h": quote['volume_24h'],
                        "percent_change_24h": quote['percent_change_24h'],
                        "category": crypto.get('category', None)
                    })
                
                formatted_result = json.dumps({"cryptocurrencies": results}, indent=2)
                
                # Cache the result
                with open(cache_file, 'w') as f:
                    f.write(formatted_result)
                
                return formatted_result
            else:
                error_message = data.get('status', {}).get('error_message', "Could not retrieve cryptocurrency list")
                return f"Error: {error_message}"
                
        except Exception as e:
            return f"Error retrieving cryptocurrency list: {str(e)}"