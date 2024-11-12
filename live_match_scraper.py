"""
This module contains the LiveMatchScraper class, which is used to scrape live match statistics and odds from a given URL.
Methods:
    get_match_stats_html(self):
        Scrapes the match stats HTML from the provided URL and returns it.
    get_raw_stats(self):
        Returns the text content of the match stats HTML.
    parse_match_stats(self):
        Parses the raw match stats text and extracts specific data points.
    get_match_specific_odds(self, url: str):
        Scrapes the match specific odds from the provided URL and returns them as JSON.
    find_grouped_markets(data):
        Recursively searches for and returns grouped markets from the provided data.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
from bs4 import BeautifulSoup
import requests
import json
from OpenAIHelper import OpenAIHelper

class LiveMatchScraper:
    def __init__(self, url: str):
        """Initialize the scraper with the URL to scrape."""
        # List of User-Agents (representing different desktop browsers)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/88.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36 Edge/90.0.818.66",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36 OPR/76.0.4017.123"
        ]
        self.url = url

    def get_match_stats_html(self):
        """Scrapes the match stats HTML from the provided URL and returns it."""
        # Randomly select a User-Agent
        selected_user_agent = random.choice(self.user_agents)

        # Setup ChromeOptions with the randomly selected User-Agent
        chrome_options = Options()
        chrome_options.add_argument(f"user-agent={selected_user_agent}")
        chrome_options.add_argument("referer=https://betclic.pt")  # Optional referer header
        chrome_options.headless = True  # Disable headless if needed, set True to run headlessly

        # Initialize the driver with the selected User-Agent
        driver = webdriver.Chrome(options=chrome_options)

        # Open the URL
        driver.get(self.url)

        # Wait for the page to load and bypass 403
        time.sleep(3)  # Adjust as needed

        # Wait for the "Aceitar tudo" button to be clickable
        try:
            accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'popin_tc_privacy_button_2'))
            )
            accept_button.click()
            print("Cookies accepted")
        except Exception as e:
            print("Error clicking the 'Aceitar tudo' button:", e)

        # Wait for a moment to ensure the cookies are accepted
        time.sleep(3)

        # Wait for the overlay or content to load after clicking "Estatísticas"
        try:
            estatisticas_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/app-desktop/app-desktop-sports-layout/div[1]/div/bcdk-content-scroller/div/sports-match-page/sports-match-header/div/sports-events-event/div/sports-events-event-buttons/div/button[2]"))
            )
            estatisticas_button.click()
            print("Clicked the 'Estatísticas' button.")
        except Exception as e:
            print("Error clicking the 'Estatísticas' button:", e)

        time.sleep(5)  # Wait for the overlay to load

        # Locate the element using the provided XPath
        try:
            element = driver.find_element(By.XPATH, "/html/body/div/div[2]/div/mat-dialog-container/div/div/sports-match-stats-modal/bcdk-dialog/div")
            element_html = element.get_attribute('outerHTML')
        except Exception as e:
            print(f"Error locating the element: {e}")
            element_html = None

        # Close the driver
        driver.quit()

        return element_html

    def get_raw_stats(self):
        """returns the text content of the match stats HTML."""
        match_stats_html = self.get_match_stats_html()
        if match_stats_html:            
            soup = BeautifulSoup(match_stats_html, 'html.parser')
            return soup.get_text()
        
    def parse_match_stats(self):
        """
        Data to be extracted: 
        "probability_win",
        "probability_draw",
        "probability_home_win",
        "victories_home_vs_away",
        "draws_home_vs_away",
        "losses_home_vs_away",
        "goals_scored",
        "AEM",
        "more_than_1_5_probability",
        "more_than_2_5_probability",
        "cards_away",
        "corners_away",
        "last_games
        """
        # we cant use this because of 403, the only way to bypass this is to use a proxy server or IP rotation
        # we can try to increase the sleep time but it will be very slow
        helper = OpenAIHelper() 
        raw_text = self.get_raw_stats() 
        result = helper.raw2json(raw_text)
        with open("match_stats.txt", "a") as file:
            file.write(json.dumps(result) + "\n")

        return result
    
    def get_match_specific_odds(self, url: str):
        """Scrapes the match specific odds from the provided URL and returns them as JSON."""
        """ needs alot of clean up to reduce token count"""
        
        response = requests.get(url)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': 'ng-state', 'type': 'application/json'})
        
        if not script_tag:
            return None
        
        try:
            # id muda 
            data = json.loads(script_tag.string.strip())
            return self.find_grouped_markets(data)
        
        except json.JSONDecodeError:
            return None
        
    @staticmethod
    def find_grouped_markets(data):
        # To store results
        grouped_markets = []

        # If the current data is a dictionary, iterate through its keys and values
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "grouped_markets":
                    # If the key is grouped_markets, append it to the result list
                    grouped_markets.append(value)
                # Recursively search in nested dictionaries or lists
                else:
                    grouped_markets.extend(LiveMatchScraper.find_grouped_markets(value))

        elif isinstance(data, list):
            for item in data:
                grouped_markets.extend(LiveMatchScraper.find_grouped_markets(item))

        return grouped_markets
        
if __name__ == "__main__":
    url = "https://www.betclic.pt/futebol-s1/liga-betclic-c32/benfica-fc-porto-m3002641355"
    scraper = LiveMatchScraper(url)
    print(scraper.parse_match_stats())