# tests/test_crypto_tools.py

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import time
from marketpulse.tools.market_tool import (
    FinancialNewsSearchTool,
    CryptoQuoteTool,
    CryptocurrencyListTool
)
from marketpulse.clean_json import extract_crypto_quote, format_crypto_list


@pytest.fixture
def setup_cache_dirs():
    """Setup and cleanup cache directories for testing"""
    # Create test cache directories
    cache_dirs = [
        ".cache/news",
        ".cache/quotes",
        ".cache/crypto_lists"
    ]
    
    for cache_dir in cache_dirs:
        os.makedirs(cache_dir, exist_ok=True)
    
    os.makedirs(".logs", exist_ok=True)
    
    yield
    
    # Cleanup test cache files
    test_files = [
        ".cache/news/cryptocurrency_crypto_blockchain_news_bitcoin.json",
        ".cache/quotes/BTC.json",
        ".cache/quotes/ETH.json",
        ".cache/crypto_lists/top_10.json"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


@pytest.fixture
def mock_bing_wrapper():
    """Mock BingSearchAPIWrapper to avoid actual API calls"""
    with patch('langchain_community.utilities.BingSearchAPIWrapper') as mock:
        mock_instance = MagicMock()
        mock_instance.run.return_value = "Mocked cryptocurrency news results from Bing API"
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_coinmarketcap_response():
    """Mock CoinMarketCap API response for cryptocurrency quotes"""
    return {
        "status": {
            "timestamp": "2025-04-01T12:34:56.789Z",
            "error_code": 0,
            "error_message": None,
            "elapsed": 10,
            "credit_count": 1
        },
        "data": {
            "BTC": {
                "id": 1,
                "name": "Bitcoin",
                "symbol": "BTC",
                "category": "Layer 1",
                "quote": {
                    "USD": {
                        "price": 45000.0,
                        "volume_24h": 28000000000.0,
                        "percent_change_24h": 2.5,
                        "percent_change_7d": 5.2,
                        "market_cap": 850000000000.0,
                        "last_updated": "2025-04-01T12:30:00.000Z"
                    }
                }
            }
        }
    }


@pytest.fixture
def mock_coinmarketcap_listings_response():
    """Mock CoinMarketCap API response for cryptocurrency listings"""
    return {
        "status": {
            "timestamp": "2025-04-01T12:34:56.789Z",
            "error_code": 0,
            "error_message": None,
            "elapsed": 10,
            "credit_count": 1
        },
        "data": [
            {
                "id": 1,
                "name": "Bitcoin",
                "symbol": "BTC",
                "category": "Layer 1",
                "quote": {
                    "USD": {
                        "price": 45000.0,
                        "volume_24h": 28000000000.0,
                        "percent_change_24h": 2.5,
                        "market_cap": 850000000000.0,
                        "last_updated": "2025-04-01T12:30:00.000Z"
                    }
                }
            },
            {
                "id": 1027,
                "name": "Ethereum",
                "symbol": "ETH",
                "category": "Layer 1",
                "quote": {
                    "USD": {
                        "price": 2500.0,
                        "volume_24h": 15000000000.0,
                        "percent_change_24h": 1.8,
                        "market_cap": 300000000000.0,
                        "last_updated": "2025-04-01T12:30:00.000Z"
                    }
                }
            }
        ]
    }


class TestCryptoTools:
    """Test suite for cryptocurrency-focused tools"""
    
    def test_news_search_tool(self, setup_cache_dirs, mock_bing_wrapper):
        """Test the cryptocurrency news search tool"""
        tool = FinancialNewsSearchTool()
        
        # Verify that tool name and description have been updated
        assert tool.name == "crypto_news_search"
        assert "cryptocurrency" in tool.description.lower()
        assert "blockchain" in tool.description.lower()
        
        # Run the tool to get crypto news
        result = tool._run("bitcoin")
        
        # Verify crypto-specific prefix was added to the query
        mock_bing_wrapper.run.assert_called_with("cryptocurrency crypto blockchain news bitcoin")
        
        # Verify result and caching
        assert result == "Mocked cryptocurrency news results from Bing API"
        assert os.path.exists(".cache/news/cryptocurrency_crypto_blockchain_news_bitcoin.json")
    
    def test_crypto_quote_tool(self, setup_cache_dirs):
        """Test the cryptocurrency quote tool"""
        with patch('requests.get') as mock_get:
            # Set up mock response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": {
                    "BTC": {
                        "id": 1,
                        "name": "Bitcoin",
                        "symbol": "BTC",
                        "category": "Layer 1",
                        "quote": {
                            "USD": {
                                "price": 45000.0,
                                "volume_24h": 28000000000.0,
                                "percent_change_24h": 2.5,
                                "percent_change_7d": 5.2,
                                "market_cap": 850000000000.0,
                                "last_updated": "2025-04-01T12:30:00.000Z"
                            }
                        }
                    }
                }
            }
            mock_get.return_value = mock_response
            
            tool = CryptoQuoteTool()
            
            # Verify tool name and description
            assert tool.name == "crypto_quote"
            assert "cryptocurrency" in tool.description.lower()
            
            # Run the tool to get a crypto quote
            result = tool._run("BTC")
            
            # Parse the result
            result_json = json.loads(result)
            
            # Verify API was called with correct parameters
            args, kwargs = mock_get.call_args
            assert kwargs['headers']['Accept'] == 'application/json'
            assert kwargs['params']['symbol'] == 'BTC'
            assert kwargs['params']['convert'] == 'USD'
            
            # Verify result structure
            assert result_json["symbol"] == "BTC"
            assert result_json["name"] == "Bitcoin"
            assert "price" in result_json
            assert "change_24h" in result_json
            assert "change_7d" in result_json
            assert "volume_24h" in result_json
            assert "market_cap" in result_json
            assert "category" in result_json
            
            # Verify cache file was created
            assert os.path.exists(".cache/quotes/BTC.json")
    
    def test_cryptocurrency_list_tool(self, setup_cache_dirs):
        """Test the cryptocurrency list tool"""
        with patch('requests.get') as mock_get:
            # Set up mock response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [
                    {
                        "id": 1,
                        "name": "Bitcoin",
                        "symbol": "BTC",
                        "category": "Layer 1",
                        "quote": {
                            "USD": {
                                "price": 45000.0,
                                "volume_24h": 28000000000.0,
                                "percent_change_24h": 2.5,
                                "market_cap": 850000000000.0,
                                "last_updated": "2025-04-01T12:30:00.000Z"
                            }
                        }
                    },
                    {
                        "id": 1027,
                        "name": "Ethereum",
                        "symbol": "ETH",
                        "category": "Layer 1",
                        "quote": {
                            "USD": {
                                "price": 2500.0,
                                "volume_24h": 15000000000.0,
                                "percent_change_24h": 1.8,
                                "market_cap": 300000000000.0,
                                "last_updated": "2025-04-01T12:30:00.000Z"
                            }
                        }
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            tool = CryptocurrencyListTool()
            
            # Verify tool name and description
            assert tool.name == "crypto_list"
            assert "cryptocurrencies" in tool.description.lower()
            
            # Run the tool to get crypto listings
            result = tool._run(limit=10)
            
            # Parse the result
            result_json = json.loads(result)
            
            # Verify API was called with correct parameters
            args, kwargs = mock_get.call_args
            assert kwargs['headers']['Accept'] == 'application/json'
            assert kwargs['params']['limit'] == 10
            assert kwargs['params']['convert'] == 'USD'
            assert kwargs['params']['sort'] == 'market_cap'
            
            # Verify result structure
            assert "cryptocurrencies" in result_json
            assert len(result_json["cryptocurrencies"]) == 2
            assert result_json["cryptocurrencies"][0]["symbol"] == "BTC"
            assert result_json["cryptocurrencies"][1]["symbol"] == "ETH"
            
            # Verify cache file was created
            assert os.path.exists(".cache/crypto_lists/top_10.json")
    
    def test_extract_crypto_quote(self, mock_coinmarketcap_response):
        """Test the extract_crypto_quote function"""
        result = extract_crypto_quote(mock_coinmarketcap_response, "BTC")
        
        assert result is not None
        assert result["symbol"] == "BTC"
        assert result["name"] == "Bitcoin"
        assert result["price"] == "45000.0"
        assert result["category"] == "Layer 1"
    
    def test_format_crypto_list(self, mock_coinmarketcap_listings_response):
        """Test the format_crypto_list function"""
        result = format_crypto_list(mock_coinmarketcap_listings_response, 2)
        
        assert result is not None
        assert "cryptocurrencies" in result
        assert len(result["cryptocurrencies"]) == 2
        assert result["cryptocurrencies"][0]["symbol"] == "BTC"
        assert result["cryptocurrencies"][1]["symbol"] == "ETH"
        
        # Test with limit
        result = format_crypto_list(mock_coinmarketcap_listings_response, 1)
        assert len(result["cryptocurrencies"]) == 1
    
    def test_crypto_tools_cache_reuse(self, setup_cache_dirs):
        """Test that the crypto quote tool properly reuses cache"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": {
                    "ETH": {
                        "id": 1027,
                        "name": "Ethereum",
                        "symbol": "ETH",
                        "quote": {
                            "USD": {
                                "price": 2500.0,
                                "volume_24h": 15000000000.0,
                                "percent_change_24h": 1.8,
                                "percent_change_7d": 3.5,
                                "market_cap": 300000000000.0,
                                "last_updated": "2025-04-01T12:30:00.000Z"
                            }
                        }
                    }
                }
            }
            mock_get.return_value = mock_response
            
            tool = CryptoQuoteTool()
            
            # First call - should hit the API
            result1 = tool._run("ETH")
            assert mock_get.call_count == 1
            
            # Second call - should use cache
            result2 = tool._run("ETH")
            assert mock_get.call_count == 1  # Still just 1 call
            
            # Verify results are the same
            assert result1 == result2
            
            # Verify log file was created
            assert os.path.exists(".logs/coinmarketcap_usage.log")
    
    def test_crypto_tools_cache_expiry(self, setup_cache_dirs):
        """Test that crypto cache expires more quickly than stock cache (30 min vs 1 hour)"""
        # Create a fake cache file for ETH
        cache_file = ".cache/quotes/ETH.json"
        with open(cache_file, 'w') as f:
            json.dump({
                "symbol": "ETH",
                "name": "Ethereum",
                "price": "2500.0",
                "change_24h": "1.8",
                "change_7d": "3.5",
                "volume_24h": "15000000000.0",
                "market_cap": "300000000000.0",
                "last_updated": "2025-04-01T12:30:00.000Z"
            }, f)
        
        # Set the modification time to 45 minutes ago
        forty_five_min_ago = datetime.now() - timedelta(minutes=45)
        os.utime(cache_file, (forty_five_min_ago.timestamp(), forty_five_min_ago.timestamp()))
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": {
                    "ETH": {
                        "id": 1027,
                        "name": "Ethereum",
                        "symbol": "ETH",
                        "quote": {
                            "USD": {
                                "price": 2550.0,  # Different price to verify new data is used
                                "volume_24h": 15500000000.0,
                                "percent_change_24h": 2.0,
                                "percent_change_7d": 4.0,
                                "market_cap": 305000000000.0,
                                "last_updated": "2025-04-01T13:15:00.000Z"
                            }
                        }
                    }
                }
            }
            mock_get.return_value = mock_response
            
            tool = CryptoQuoteTool()
            
            # This should ignore the old cache and make a new API call
            result = tool._run("ETH")
            result_json = json.loads(result)
            
            # Verify API was called (because cache is older than 30 minutes)
            assert mock_get.call_count == 1
            
            # Verify the new price is returned
            assert float(result_json["price"]) == 2550.0  # New price, not cached price
            
            # Verify the cache was updated
            with open(cache_file, 'r') as f:
                updated_cache = json.loads(f.read())
                assert float(updated_cache["price"]) == 2550.0