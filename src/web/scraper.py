import aiohttp
import urllib.parse
from bs4 import BeautifulSoup
from abc import abstractmethod
from typing import Optional
from os import getenv
from dataclasses import dataclass


KINOPOISK_API_KEY = getenv("KINOPOISK_API_KEY")


@dataclass
class Film:
    name: str
    rating: int
    url: str
    year: int


class Scraper:
    @abstractmethod
    async def search_film(self, session: aiohttp.ClientSession, name: str) -> Optional[str]:
        pass

class ZonaScraper(Scraper):
    BASE_URL = "https://w140.zona.plus"

    async def search_film(self, session: aiohttp.ClientSession, name: str) -> Optional[str]:
        url = f"{self.BASE_URL}/search/{urllib.parse.quote(name)}"

        async with session.get(url) as resp:
            text = await resp.text()

            soup = BeautifulSoup(text, 'html.parser')

            film_card = soup.select_one('li.results-item-wrap')

            if not film_card:
                return None

            link_elem = film_card.select_one('a.results-item')

            return f"{self.BASE_URL}{link_elem['href']}"

class RutubeScraper:
    BASE_URL = "https://rutube.ru/api/v3/search/video"

    async def search_film(self, session: aiohttp.ClientSession, name: str) -> Optional[str]:
        params: dict[str, str | int] = {"query": name, "limit": 1}
        async with session.get(self.BASE_URL, params=params) as resp:
            data = await resp.json()
            results = data.get("results", [])

            if not results:
                return None

            return results[0].get("video_url")

async def find_film_info(session: aiohttp.ClientSession, name: str) -> Optional[Film]:
    SEARCH_URL = "https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword"
    headers: dict[str, str] = {
        "X-API-KEY": str(KINOPOISK_API_KEY),
        "accept": "application/json"
    }

    params: dict[str, str] = {"keyword": name}

    async with session.get(SEARCH_URL, params=params, headers=headers) as resp:
        data = await resp.json()
        if data.get("searchFilmsCountResult") == 0:
            return None
        else:
            film_id = data.get("films")[0].get("filmId")

    FILM_URL = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/{film_id}"

    async with session.get(FILM_URL, headers=headers) as resp:
        data = await resp.json()
        return Film(
            name=data.get("nameRu") or data.get("nameOriginal"),
            rating=data.get("ratingKinopoisk"),
            url=data.get("webUrl"),
            year=data.get("year")
        )
