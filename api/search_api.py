import requests
from typing import List, Dict
import os
from bs4 import BeautifulSoup
import html2text

class SearchAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True

    def get_page_content(self, url: str) -> str:
        """
        Fetch and extract text content from a webpage
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Convert HTML to markdown/text
            text = self.html_converter.handle(str(soup))
            
            # Clean up the text
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = ' '.join(lines)
            
            # Truncate if too long
            return clean_text[:10000] if len(clean_text) > 10000 else clean_text
            
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return ""

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search using Google Custom Search API and fetch full content
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (max 10 for free tier)
            
        Returns:
            List of search results with full content
        """
        try:
            response = requests.get(
                self.base_url,
                params={
                    "q": query,
                    "key": self.api_key,
                    "cx": self.search_engine_id,
                    "num": min(max_results, 10)
                }
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("items", []):
                title = item.get("title", "")
                url = item.get("link", "")
                snippet = item.get("snippet", "")
                
                # Fetch full content
                content = self.get_page_content(url)
                
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "content": content
                })
            
            return results
            
        except Exception as e:
            print(f"Google Search API error: {str(e)}")
            return [] 