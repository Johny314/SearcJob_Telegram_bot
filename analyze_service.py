import re
from collections import Counter

# Заранее определенные навыки, которые мы будем искать в текстах
SKILLS_LIST = [
    'python', 'java', 'sql', 'javascript', 'c++', 'html', 'css', 'django', 'fastapi',
    'git', 'react', 'docker', 'kubernetes', 'aws', 'azure', 'devops', 'node.js',
    'graphql', 'mongo', 'mysql', 'postgresql', 'linux', 'tensorflow', 'keras',
    'flutter', 'typescript', 'nosql', 'machine learning', 'data analysis'
]


def clean_text(text):
    """Очищает текст вакансий от спецсимволов и приводит к нижнему регистру"""
    if text is None:
        text = ""  # Заменяем None на пустую строку
    return re.sub(r'\W+', ' ', text).lower()


def analyze_skills(text):
    """Анализ ключевых навыков из текста (чистого, без html-разметки)"""
    # Очистка текста и разбиение на слова
    words = clean_text(text).split()

    # Подсчет совпадений слов из текста с навыками
    word_counts = Counter(word for word in words if word in SKILLS_LIST)
    return word_counts


def extract_skills(vacancy):
    """
    Извлекает навыки из предоставленной вакансии:
    - Из поля key_skills
    - Из текстов описания вакансии
    """
    skills = []

    # 1. Сначала проверяем наличие поля key_skills
    if "key_skills" in vacancy:
        skills = [skill["name"] for skill in vacancy["key_skills"] if "name" in skill]

    # 2. Если ключевые навыки отсутствуют, анализируем текст (например, "requirement" в snippet)
    if not skills and "snippet" in vacancy:
        snippet = vacancy["snippet"]
        skills_from_snippet = analyze_skills(snippet.get("requirement", ""))

        # Проверяем, что analyze_skills вернул что-то полезное
        if isinstance(skills_from_snippet, Counter):
            skills.extend([skill for skill, count in skills_from_snippet.items()])

    return skills
