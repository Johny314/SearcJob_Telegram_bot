import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API URL and default params
HH_API_URL = os.getenv("HH_API_URL")
AREA = 113  # Россия
PAGE = int(os.getenv("PAGE", 0))  # Начальная страница
PER_PAGE = 10  # Количество вакансий на странице


def search_vacancies(query, page=PAGE, per_page=PER_PAGE):
    """Поиск вакансий через API hh.ru"""
    params = {
        "text": query,  # Поисковый запрос
        "area": AREA,  # Регион поиска
        "page": page,  # Номер страницы
        "per_page": per_page  # Количество вакансий на странице
    }

    try:
        response = requests.get(HH_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data

    except requests.RequestException as e:
        print(f"Ошибка запроса к API hh.ru: {e}")
        return None


def get_vacancy_details(vacancy_id):
    """Получение детальной информации о конкретной вакансии"""
    try:
        response = requests.get(f"{HH_API_URL}/{vacancy_id}")
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        print(f"Ошибка получения вакансии {vacancy_id}: {e}")
        return None
