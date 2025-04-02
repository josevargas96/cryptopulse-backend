# src/marketpulse/clean_json.py

import json
import re
from typing import Dict, Any, Optional


def extract_json_string(response: str) -> str:
    """
    Attempts to extract just the JSON part from a string.
    Finds the first '{' and the matching last '}' and returns the substring.
    Also handles potential formatting issues.
    """
    # Find JSON structure beginning and end
    start_idx = response.find('{')
    end_idx = response.rfind('}')
    
    if start_idx == -1 or end_idx == -1:
        raise ValueError("No JSON object braces found in response.")
    
    json_str = response[start_idx:end_idx + 1]
    
    # Clean up common formatting issues
    # Remove trailing commas in arrays
    json_str = re.sub(r',(\s*])', r'\1', json_str)
    # Remove trailing commas in objects
    json_str = re.sub(r',(\s*})', r'\1', json_str)
    
    try:
        # Verify it's valid JSON but return the string
        json.loads(json_str)
        return json_str
    except json.JSONDecodeError as e:
        problem_char = e.pos
        context = json_str[max(0, problem_char - 50):min(len(json_str), problem_char + 50)]
        print(f"JSON parse error near: ...{context}...")
        raise ValueError(f"Failed to parse JSON after cleaning: {str(e)}. Error location: {context}")


def clean_and_parse_json(response: str) -> dict:
    """
    Clean and parse JSON from a string response.
    Handles common formatting issues and returns a parsed JSON object.
    """
    try:
        # First try direct parsing
        return json.loads(response)
    except json.JSONDecodeError:
        try:
            # Try to extract and clean JSON, then parse it
            cleaned_str = extract_json_string(response)
            return json.loads(cleaned_str)  # Parse the cleaned string into a dict
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Full response that failed to parse: {response}")
            raise ValueError(f"Failed to parse JSON after cleaning: {str(e)}. Content: {response[:100]}...")


def extract_crypto_quote(data: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
    """
    Extract cryptocurrency quote data from CoinMarketCap API response.
    
    Args:
        data: The JSON response from CoinMarketCap API
        symbol: The cryptocurrency symbol (e.g., 'BTC', 'ETH')
        
    Returns:
        Dictionary with extracted and formatted data or None if extraction fails
    """
    try:
        # Check if we have data and the symbol exists
        if 'data' in data and symbol.upper() in data['data']:
            crypto_data = data['data'][symbol.upper()]
            quote = crypto_data['quote']['USD']
            
            # Extract category data if available
            category = None
            if 'category' in crypto_data:
                category = crypto_data['category']
            
            # Create a formatted result
            result = {
                "symbol": crypto_data['symbol'],
                "name": crypto_data['name'],
                "price": str(quote['price']),
                "change_24h": str(quote['percent_change_24h']),
                "change_7d": str(quote.get('percent_change_7d', 0)),
                "volume_24h": str(quote['volume_24h']),
                "market_cap": str(quote['market_cap']),
                "category": category,
                "last_updated": quote['last_updated']
            }
            return result
        else:
            # Handle error cases
            error_message = data.get('status', {}).get('error_message', f"Could not find data for {symbol}")
            print(f"Error extracting crypto quote: {error_message}")
            return None
    except Exception as e:
        print(f"Error processing cryptocurrency data: {str(e)}")
        return None


def format_crypto_list(data: Dict[str, Any], limit: int = 100) -> Optional[Dict[str, Any]]:
    """
    Format cryptocurrency listings data from CoinMarketCap API.
    
    Args:
        data: The JSON response from CoinMarketCap API
        limit: Maximum number of cryptocurrencies to include
        
    Returns:
        Dictionary with formatted cryptocurrency list or None if formatting fails
    """
    try:
        if 'data' in data:
            # Extract relevant info from each cryptocurrency
            results = []
            for crypto in data['data'][:limit]:
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
            
            return {"cryptocurrencies": results}
        else:
            error_message = data.get('status', {}).get('error_message', "Could not retrieve cryptocurrency list")
            print(f"Error formatting crypto list: {error_message}")
            return None
    except Exception as e:
        print(f"Error processing cryptocurrency list: {str(e)}")
        return None