from services.analyze_service import (
    extract_skills_with_spacy,
    process_vacancies,
    format_skills_output
)
from services.search_service import fetch_vacancies, fetch_vacancy_details
from services.database_service import add_to_search_history, get_last_searches
