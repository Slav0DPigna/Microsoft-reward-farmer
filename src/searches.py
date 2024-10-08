import json
import logging
import random
import time
from datetime import date, timedelta

import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from src.browser import Browser


class Searches:

    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.cookies_accepted = False

    def getGoogleTrends(self, wordsCount: int) -> list:
        searchTerms: list[str] = []
        i = 0
        while len(searchTerms) < wordsCount:
            i += 1
            r = requests.get(
                f'https://trends.google.com/trends/api/dailytrends?hl={self.browser.localeLang}&ed={(date.today() - timedelta(days=i)).strftime("%Y%m%d")}&geo={self.browser.localeGeo}&ns=15'
            )
            trends = json.loads(r.text[6:])
            for topic in trends["default"]["trendingSearchesDays"][0][
                "trendingSearches"
            ]:
                searchTerms.append(topic["title"]["query"].lower())
                searchTerms.extend(
                    relatedTopic["query"].lower()
                    for relatedTopic in topic["relatedQueries"]
                )
            searchTerms = list(set(searchTerms))
        del searchTerms[wordsCount : (len(searchTerms) + 1)]
        return searchTerms

    def getRelatedTerms(self, word: str) -> list:
        try:
            r = requests.get(
                f"https://api.bing.com/osjson.aspx?query={word}",
                headers={"User-agent": self.browser.userAgent},
            )
            return r.json()[1]
        except Exception:  # pylint: disable=broad-except
            return []

    def bingSearches(self, numberOfSearches: int):
        logging.info("[BING] " + f"Starting {self.browser.browserType.capitalize()} Edge Bing searches...",)
        pointsCounter = self.browser.utils.getBingAccountPoints()
        i = 0
        search_terms = self.getGoogleTrends(numberOfSearches)
        for word in search_terms:
            i += 1
            logging.info("[BING] " + f"{i}/{numberOfSearches}"+" the search is "+str(word))
            points = self.bingSearch(word)
            if points <= pointsCounter and i > 1:
                logging.warning("Points don't increase. I have to wait about 15 minutes")
                for j in range(15):
                    time.sleep(60)
                    logging.info(str(j+1)+" minutes passed")
                logging.warning("The waiting is finished")
                #relatedTerms = self.getRelatedTerms(word)[:2]
                #for term in relatedTerms:
                #    points = self.bingSearch(term)
                #    if not points <= pointsCounter:
                #        break
            if points > 0:
                pointsCounter = points
            else:
                break
        logging.info(f"[BING] Finished {self.browser.browserType.capitalize()} Edge Bing searches !")
        return pointsCounter

    def accept_cookies(self):
        if not self.cookies_accepted:
            try:
                self.browser.utils.waitUntilClickable(By.ID, "bnp_btn_accept")
                accept_button = self.webdriver.find_element(By.ID, 'bnp_btn_accept')
                accept_button.click()
                logging.info("Search's cockies accepted!!!")
                self.cookies_accepted = True
            except:
                logging.error("I can't accept search's cookies...")
                pass  # Handle the case when the cookie acceptance button is not found

    def bingSearch(self, word: str):
        while True:
            try:
                self.webdriver.get("https://bing.com")
                self.browser.utils.waitUntilClickable(By.ID, "sb_form_q")
                searchbar = self.webdriver.find_element(By.ID, "sb_form_q")
                searchbar.send_keys(word)
                searchbar.submit()
                random_int = random.randint(60, 120)
                logging.info("[BING] time to sleep "+str(random_int)+" seconds")
                time.sleep(random_int)
                return self.browser.utils.getBingAccountPoints()
            except TimeoutException:
                logging.error("[BING] Timeout, retrying in 5 seconds...")
                time.sleep(5)
                continue
