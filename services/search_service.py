import aiohttp
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

HH_API_URL = os.getenv("HH_API_URL") or "https://api.hh.ru/vacancies"


async def fetch_vacancies(query: str, page: int = 0, per_page: int = 10) -> dict:
    """
    Асинхронный API запрос для поиска вакансий.
    :param query: Текстовый запрос для поиска вакансий.
    :param page: Номер страницы.
    :param per_page: Количество вакансий на странице.
    :return: Словарь с результатами поиска.
    """
    params = {
        "text": query,
        "area": 113,  # По умолчанию Россия
        "page": page,
        "per_page": per_page
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(HH_API_URL, params=params) as response:
                response.raise_for_status()
                json_data = await response.json()
                return json_data
        except aiohttp.ClientResponseError as e:
            print(f"API Error: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected Error: {e}")
            return {}


async def fetch_vacancy_details(vacancy_id: str) -> dict:
    """
    Асинхронный API запрос для получения деталей конкретной вакансии.
    :param vacancy_id: ID вакансии.
    :return: Детальная информация о вакансии.
    """
    url = f"{HH_API_URL}/{vacancy_id}"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            print(f"API Error: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected Error: {e}")
            return {}
