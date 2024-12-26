import spacy
from collections import Counter

# Загружаем English NLP модель spaCy
nlp = spacy.load("en_core_web_sm")

# Список заранее определенных навыков (можно будет вынести его в файл конфигурации)
SKILLS_LIST = [
    # Языки программирования
    'python', 'java', 'javascript', 'typescript', 'c', 'c++', 'c#', 'go',
    'ruby', 'php', 'swift', 'kotlin', 'r', 'perl', 'dart', 'scala', 'rust',
    'objective-c', 'matlab', 'shell', 'powershell', 'visual basic',
    'assembly', 'lua',

    # Веб-разработка: frontend
    'html', 'css', 'bootstrap', 'sass', 'less', 'javascript', 'jquery',
    'react', 'vue.js', 'angular', 'svelte', 'next.js', 'nuxt.js', 'elm',

    # Веб-разработка: backend
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


def extract_skills_with_spacy(text: str) -> list:
    """
    Использует spaCy для извлечения навыков из текста.
    :param text: Текст, из которого извлекаются навыки.
    :return: Список найденных навыков.
    """
    doc = nlp(text.lower())

    # Ищем только совпадения из SKILLS_LIST
    found_skills = []
    for token in doc:
        if token.text in SKILLS_LIST:
            found_skills.append(token.text)

    # Проверяем на составные фразы (биграммы, триграммы)
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower().strip()
        if chunk_text in SKILLS_LIST:
            found_skills.append(chunk_text)

    # Убираем повторяющиеся элементы
    return list(set(found_skills))


def process_vacancies(data: dict):
    """
    Анализирует вакансии на основе NLP методов.
    :param data: JSON-объект со списком вакансий.
    :return: ТОП-10 навыков и общее число обработанных вакансий.
    """
    all_skills = []
    analyzed_vacancies_count = 0

    if "items" not in data:
        return [], 0

    for item in data["items"]:
        try:
            snippet = item.get('snippet', {})
            requirement = snippet.get('requirement', '')
            responsibility = snippet.get('responsibility', '')

            # Консолидируем текст
            text = f"{requirement} {responsibility}"

            # Извлечение навыков через spaCy
            skills = extract_skills_with_spacy(text)
            if skills:
                all_skills.extend(skills)

            analyzed_vacancies_count += 1
        except Exception as e:
            print(f"Ошибка при обработке одной из вакансий: {e}")

    # Подсчёт частоты навыков
    skills_counter = Counter(all_skills)
    return skills_counter.most_common(), analyzed_vacancies_count


def format_skills_output(top_skills, total_vacancies):
    """
    Формирует результаты анализа навыков для удобного вывода.
    :param top_skills: Список (навык, частота).
    :param total_vacancies: Количество вакансий.
    """
    output = [f"Количество проанализированных вакансий: {total_vacancies}\n", "ТОП-10 навыков из вакансий:\n"]

    for idx, (skill, count) in enumerate(top_skills[:10], start=1):
        output.append(f"{idx}. {skill.capitalize()} — {count} упоминаний")

    return "\n".join(output)

