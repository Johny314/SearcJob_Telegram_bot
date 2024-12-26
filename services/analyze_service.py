import re
from collections import Counter

# Список заранее определенных навыков (можно будет вынести его в файл конфигурации)
SKILLS_LIST = [
    # Языки программирования
    'python', 'java', 'javascript', 'typescript', 'c', 'c++', 'c#', 'go',
    'ruby', 'php', 'swift', 'kotlin', 'r', 'perl', 'dart', 'scala', 'rust',
    'objective-c', 'matlab', 'shell', 'powershell', 'visual basic',
    'assembly', 'lua',

    # Веб-разработка: фронтенд
    'html', 'css', 'bootstrap', 'sass', 'less', 'javascript', 'jquery',
    'react', 'vue.js', 'angular', 'svelte', 'next.js', 'nuxt.js', 'elm',

    # Веб-разработка: бэкенд
    'node.js', 'express.js', 'nest.js', 'django', 'flask', 'fastapi',
    'spring', 'spring boot', 'asp.net', 'laravel', 'symfony',
    'rails', 'ruby on rails', 'cakephp', 'gin',

    # Мобильная разработка
    'flutter', 'react native', 'xamarin', 'jetpack compose', 'kotlin multi-platform',

    # Работа с данными
    'sql', 'mysql', 'postgresql', 'sqlite', 'mongodb', 'redis', 'couchdb',
    'cassandra', 'hive', 'bigquery', 'clickhouse', 'elasticsearch',
    'spark', 'hadoop', 'presto', 'dask', 'pandas', 'numpy',

    # DevOps и системное администрирование
    'docker', 'kubernetes', 'jenkins', 'terraform', 'ansible', 'puppet',
    'saltstack', 'vagrant', 'nginx', 'apache', 'haproxy', 'prometheus',
    'grafana', 'elastic stack', 'splunk', 'bash', 'zabbix',

    # Облачные платформы
    'aws', 'amazon web services', 'azure', 'google cloud platform',
    'ibm cloud', 'oracle cloud', 'digitalocean', 'heroku', 'vercel',

    # Машинное обучение и Data Science
    'tensorflow', 'keras', 'pytorch', 'scikit-learn', 'xgboost',
    'lightgbm', 'mlflow', 'data analysis', 'machine learning',
    'deep learning', 'computer vision', 'natural language processing',
    'openai', 'huggingface',

    # Работа с графикой и анимацией
    'three.js', 'unity', 'unreal engine', 'blender',

    # Работа с API и микро-сервисами
    'graphql', 'rest', 'soap', 'grpc', 'json',

    # Инструменты тестирования
    'selenium', 'cypress', 'pytest', 'junit', 'mocha', 'karma',
    'jasmine', 'appium', 'testng',

    # Виртуализация и контейнеризация
    'vmware', 'hyper-v', 'qemu', 'virtualbox',

    # Безопасность
    'penetration testing', 'ethical hacking', 'kali linux',
    'nessus', 'nmap',

    # Дополнительно
    'git', 'github', 'gitlab', 'bitbucket', 'ci/cd', 'linux', 'shell scripting',
    'postgresql', 'firebase', 'stripe', 'mapbox', 'openstreetmap',

    # Ручное и автоматическое тестирование
    'postman', 'jmeter', 'soapui', 'katalon studio',
]


def clean_text(text: str) -> str:
    """Очищает текст от спецсимволов и переводит в нижний регистр."""
    if not text:  # Если текст пустой - защищаемся.
        return ""
    return re.sub(r'[^\w\s]', ' ', text).lower()


def analyze_skills(text: str) -> Counter:
    """
    Анализирует список ключевых навыков на основе текста.
    Возвращает Counter с частотой упоминания каждого навыка.
    """
    # Очистка текста и выделение слов
    words = clean_text(text).split()

    # Подсчет навыков, которые есть в SKILLS_LIST
    return Counter(word for word in words if word in SKILLS_LIST)


def extract_skills(vacancy: dict) -> list:
    """
    Извлечение навыков из данных вакансии.
    :param vacancy: Данные одной вакансии (словарь)
    :return: Список навыков
    """
    skills = []

    # Извлекаем поле snippet и его содержимое
    snippet = vacancy.get('snippet', {})
    if not snippet:
        return skills

    # Извлекаем "requirement" и "responsibility", если они есть
    requirement = snippet.get('requirement', '')
    responsibility = snippet.get('responsibility', '')

    for word in SKILLS_LIST:
        if word.lower() in requirement.lower() or word.lower() in responsibility.lower():
            skills.append(word)

    return skills


def process_vacancies(data: dict):
    """
       Обрабатывает данные о вакансиях, извлекает навыки и подсчитывает их популярность.
       :param data: Ответ API с данными о вакансиях.
       :return: Список топ-способностей (name, count) и общее количество проанализированных вакансий.
       """
    all_skills = []
    analyzed_vacancies_count = 0

    if not data or "items" not in data:
        return [], 0

    for item in data["items"]:
        try:
            skills = extract_skills(item)
            if skills:
                all_skills.extend(skills)
            analyzed_vacancies_count += 1
        except Exception as e:
            print(f"Ошибка при обработке одной из вакансий: {e}")

    skills_counter = Counter(all_skills)
    top_skills = skills_counter.most_common()

    return top_skills, analyzed_vacancies_count


def format_skills_output(top_skills, total_vacancies):
    """
    Форматирует результат анализа навыков для удобного вывода.
    :param top_skills: Список топ-навыков и их частот (например, [("Python", 20), ("SQL", 15)]).
    :param total_vacancies: Общее число анализируемых вакансий.
    :return: Строка с результатами.
    """
    output = [f"Количество проанализированных вакансий: {total_vacancies}\n", "ТОП-10 навыков из вакансий:\n"]

    for i, (skill, count) in enumerate(top_skills[:10], 1):  # Ограничение до 10 навыков
        output.append(f"{i}. {skill.capitalize()} — {count} упоминаний")

    return "\n".join(output)

