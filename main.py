"""
This module provides a FastAPI application for scraping and retrieving live football match data from the Betclic website.
Endpoints:
- /live-matches: Retrieve all live football matches from 'futebol-s1' page, with unnecessary data removed and the relevant details structured.
- /live-match-urls: Retrieve all the URLs of live football matches available on 'futebol-s1' page.
- /raw-matches: Retrieve all football matches from 'futebol-s1' page in the original, unprocessed format (with all data included).
- /match-stats: Retrieve the match stats for a specific match using its URL.
- /all-match-stats: Retrieve all match stats for each live match on 'futebol-s1' page. (doest work because of 403)
- /match-odds: Retrieve the odds for a specific match using its URL.
- /positive-ev-odds: Retrieve the odds with positive expected value (EV) for a specific match.
"""

import json
from typing import Union, List
from fastapi import FastAPI
from betclic_scraper import BetclicScraper
from live_match_scraper import LiveMatchScraper
from fastapi import HTTPException
from OpenAIHelper import OpenAIHelper as llm

# Initialize FastAPI app
app = FastAPI()

# Initialize the BetclicScraper instance
url = "https://www.betclic.pt/futebol-s1"
scraper = BetclicScraper(url, log_file="betclic_scraper.log")

@app.get("/live-matches", description="Retrieve all live football matches from 'futebol-s1' page, with unnecessary data removed and the relevant details structured.")
async def live_matches():
    """Return cleaned JSON of live matches."""
    live_matches = scraper.get_clean_json()
    return {"live_matches": live_matches}

@app.get("/live-match-urls", description="Retrieve all the URLs of live football matches available on 'futebol-s1' page.")
async def live_match_urls():
    """Return URLs of live matches."""
    urls = scraper.get_live_match_urls()
    return {"live_match_urls": urls}

@app.get("/raw-matches", description="Retrieve all football matches from 'futebol-s1' page in the original, unprocessed format (with all data included)")
async def raw_matches():
    """Scrape and return matches."""
    matches = scraper.scrape_betclic_matches()
    if matches:
        return {"status": "success", "match_count": len(matches), "matches": matches}
    else:
        return {"status": "error", "message": "No matches found"}


@app.post("/match-stats", description="Retrieve the match stats for a specific match using its URL.")
async def match_stats(request: dict):
    """Parse and return match stats from a given match URL."""
    try:
        # Retrieve the URL directly from the request body
        url = request.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="URL must be provided.")
        
        # Initialize the scraper for the specific match
        scraper = LiveMatchScraper(url)
        
        # Parse match stats using the scraper
        stats = scraper.parse_match_stats()
        
        # Return the stats
        return {"status": "success", "match_stats": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.get("/all-match-stats", description="Retrieve all match stats for each live match on 'futebol-s1' page.")
async def all_match_stats():
    """
    Fetch all match stats for each live match available on the Betclic website.
    20 seconds for each live match to avoid 403
    Proxy Servers and IP Rotation can solve this issue
    """
    try:
        # Call the get_all_match_stats method from the scraper instance
        match_stats_data = scraper.get_all_match_stats()
        return {"status": "success", "match_stats_data": match_stats_data}
    except Exception as e:
        # Log and handle any unexpected errors
        return {"status": "error", "message": str(e)}
    
    
@app.post("/match-odds", description="Retrieve the odds for a specific match using its URL.")
async def get_match_odds(request: dict):
    """
    Retrieve the match-specific odds for a specific match from the provided URL.
    """
    try:
        # Retrieve the URL from the request body
        url = request.get("url")
        # Check if the URL is provided
        if not url:
            raise HTTPException(status_code=400, detail="Match URL must be provided.")
        
        # Initialize the scraper for the specific match
        scraper = LiveMatchScraper(url)
        
        # Fetch the match odds using the scraper
        odds = scraper.get_match_specific_odds(url)

        print(odds)
        
        # If no odds are found, return an error message
        if odds is None:
            raise HTTPException(status_code=404, detail="No odds found for this match.")
        
        return {"status": "success", "match_odds": odds}
    
    except Exception as e:
        # Handle any unexpected errors
        return {"status": "error", "message": str(e)}
    
@app.post("/positive-ev-odds", description="Retrieve the odds with positive expected value (EV) for a specific match.")
async def positive_ev_odds(request: dict):
    try:
        # Retrieve the URL from the request body
        url = request.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="Match URL must be provided.")
    
        scraper = LiveMatchScraper(url)
        
        # Parse match stats using the scraper
        match_stats_json = scraper.parse_match_stats()
        print(match_stats_json)  # Debugging the stats
        
        # Fetch the match odds using the scraper
        odds = scraper.get_match_specific_odds(url)

        print(odds)  # Debugging the odds
        
        helper = llm() 

        positive_ev_odds = helper.get_positive_ev_odds(odds, match_stats_json)
        
        if not positive_ev_odds:
            raise HTTPException(status_code=404, detail="No positive EV odds found for this match.")
        
        return {"status": "success", "match_odds": positive_ev_odds}
    
    except Exception as e:
        # Handle unexpected errors
        return {"status": "error", "message": str(e)}
    

