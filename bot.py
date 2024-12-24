import os

import requests
from db_config import get_connection
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import re
import nltk
import math
from nltk.corpus import stopwords
from collections import Counter
from telegram.ext import CommandHandler, Application, ContextTypes, CallbackQueryHandler

# Загружаем переменные окружения из файла .env
load_dotenv()

# Параметры поиска вакансий из .env
PAGE = int(os.getenv("PAGE", 0))  # Начальная страница
PER_PAGE = int(os.getenv("PER_PAGE", 10))  # Количество вакансий на странице
TOTAL_PAGES = int(os.getenv("TOTAL_PAGES", 39))  # Количество страниц

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
HH_API_URL = os.getenv("HH_API_URL")

# Загрузка стоп-слов
nltk.download("punkt")
nltk.download("stopwords")
nltk.download('punkt_tab')
stop_words = set(stopwords.words("russian"))

# Используем deque для хранения последних 5 поисков
search_history = {}

def get_vacancy_details(vacancy_id):
    """Получение детальной информации о вакансии"""
    try:
        response = requests.get(f"https://api.hh.ru/vacancies/{vacancy_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка получения вакансии {vacancy_id}: {e}")
        return None

def extract_skills(vacancy):
    """Извлечение навыков из key_skills или из других полей вакансии"""
    skills = []

    # Пробуем извлечь навыки из key_skills, если оно присутствует
    if "key_skills" in vacancy:
        skills = [skill["name"] for skill in vacancy["key_skills"] if "name" in skill]

    # Если key_skills пустое или отсутствует, пробуем извлечь навыки из поля snippet
    if not skills and "snippet" in vacancy:
        snippet = vacancy["snippet"]
        # В требовании можно найти ключевые навыки, такие как Python, Django и т. д.
        skills_from_snippet = analyze_skills(snippet.get("requirement", ""))

        # Проверяем тип данных, который вернула analyze_skills
        if isinstance(skills_from_snippet, dict):
            # Если это словарь, то используем items()
            skills.extend([skill for skill, count in skills_from_snippet.items()])
        elif isinstance(skills_from_snippet, list):
            # Если это список, просто добавляем его
            skills.extend(skills_from_snippet)

    return skills

def analyze_skills(text):
    if not text:  # Проверяем, что текст не None и не пустой
        return []
    """Анализируем текст для извлечения ключевых навыков"""
    # Пример навыков, которые ищем в тексте
    skills_list = [
        'python', 'java', 'sql', 'javascript', 'c++', 'html', 'css', 'django', 'fastapi', 'git', 'gitlab',
        'react', 'angular', 'vue', 'node.js', 'express', 'mongodb', 'postgresql', 'mysql', 'redis',
        'aws', 'azure', 'docker', 'kubernetes', 'devops', 'scrum', 'ci/cd', 'terraform', 'jenkins', 'docker',
        'flutter', 'spring', 'scala', 'ruby', 'rails', 'php', 'wordpress', 'laravel', 'golang', 'bash', 'typescript',
        'graphql', 'flutter', 'objective-c', 'swift', 'xcode', 'android', 'flutter', 'flutter', 'kotlin', 'flutter',
        'linux', 'unix', 'apache', 'nginx', 'azure', 'c#', 'maven', 'vagrant', 'pytorch', 'tensorflow', 'keras',
        'machine learning', 'data science', 'artificial intelligence', 'cloud', 'big data', 'spark', 'hadoop',
        'blockchain', 'ethereum', 'solidity', 'kotlin', 'ios', 'android', 'flutter', 'testing', 'selenium', 'cypress',
        'junit', 'mocha', 'jest', 'testng', 'api', 'rest', 'graphql', 'html5', 'sass', 'less', 'tailwind', 'responsive',
        'redux', 'flutter', 'jest', 'scrum', 'agile', 'ux', 'ui', 'ux/ui', 'product', 'design', 'sql server', 'mongodb',
        'devops', 'jenkins', 'gitlab', 'bitbucket', 'jenkins', 'postman', 'web services', 'microservices', 'tdd', 'bdd',
        'visual studio', 'pycharm', 'intellij', 'eclipse', 'intellij idea', 'phpstorm', 'vscode', 'docker-compose'
    ]
    words = text.lower().split()  # Преобразуем в нижний регистр и разбиваем на слова
    word_counts = Counter(word for word in words if word in skills_list)
    return word_counts

def clean_text(text):
    """Очищаем текст от лишних символов"""
    text = re.sub(r'\W+', ' ', text)  # Убираем все неалфавитные символы
    return text.lower()

def search_vacancies(query, page=PAGE, per_page=10):
    """Поиск вакансий через API hh.ru"""
    params = {
        "text": query,        # Поисковый запрос
        "area": 113,          # Россия (код региона)
        "page": page,         # Номер страницы
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

def add_to_search_history(user_id, query):
    """Сохраняем запрос в истории поиска"""
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # Вставляем новый поисковый запрос в таблицу
            cursor.execute("""
                INSERT INTO search_history (user_id, search_query)
                VALUES (%s, %s);
            """, (user_id, query))
            connection.commit()
            print("Search query added successfully!")
        except Exception as e:
            print(f"Error adding search query: {e}")
        finally:
            cursor.close()
            connection.close()

def get_last_searches(user_id, limit=5):
    """Получаем последние уникальные поисковые запросы пользователя из базы данных"""
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # Получаем последние уникальные запросы пользователя
            cursor.execute("""
                SELECT search_query
                FROM search_history
                WHERE user_id = %s
                GROUP BY search_query
                ORDER BY MAX(search_date) DESC
                LIMIT %s;
            """, (user_id, limit))
            result = cursor.fetchall()
            # Преобразуем результат в список строк
            return [row[0] for row in result]
        except Exception as e:
            print(f"Error fetching search history: {e}")
            return []
        finally:
            cursor.close()
            connection.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветственное сообщение"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я помогу вам искать вакансии. "
        f"Введите команду /search для начала поиска."
    )

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Анализ компетенций в вакансиях с прогресс-баром, обновляемым на каждой странице"""
    if context.args:
        query = " ".join(context.args)
        # Отправляем начальное сообщение с прогресс-баром
        progress_message = await update.message.reply_text(
            f"Ищу вакансии для анализа по запросу: {query}...\nПрогресс: 0%",
            parse_mode="Markdown"
        )

        # Параметры для пагинации
        per_page = PER_PAGE
        total_pages = TOTAL_PAGES
        all_skills = Counter()
        analyzed_vacancies = 0  # Счетчик проанализированных вакансий
        page = 1  # Начальная страница
        last_progress = 0  # Переменная для хранения предыдущего прогресса

        while page <= total_pages:
            # Поиск вакансий
            vacancies = search_vacancies(query, page, per_page)
            if vacancies and "items" in vacancies:
                results = vacancies["items"]
                if not results:
                    break  # Если на странице нет вакансий, выходим из цикла

                # Анализируем каждую вакансию
                for vacancy in results:
                    # Извлечение навыков из поля key_skills
                    skills = extract_skills(vacancy)
                    if skills:
                        analyzed_vacancies += 1  # Увеличиваем счетчик, если навыки найдены
                    all_skills.update(skills)

                    # Анализ текста описания вакансии
                    if "description" in vacancy:
                        text = clean_text(vacancy["description"])
                        skills_from_text = analyze_skills(text)
                        all_skills.update(dict(skills_from_text))

                # Обновление прогресса после обработки страницы
                progress_percentage = math.floor((page / total_pages) * 100)

                # Только обновляем сообщение, если прогресс изменился
                if progress_percentage != last_progress:
                    await progress_message.edit_text(
                        f"Ищу вакансии для анализа по запросу: {query}...\nПрогресс: {progress_percentage}%"
                    )
                    last_progress = progress_percentage  # Обновляем прогресс

                page += 1  # Переходим к следующей странице
            else:
                break  # Если вакансий не найдено, выходим из цикла

        # Форматирование результата
        if all_skills:
            skills_message = "\n".join([f"{skill}: {count}" for skill, count in all_skills.most_common(10)])
            await progress_message.edit_text(
                f"Наиболее востребованные навыки:\n{skills_message}\n\n"
                f"Проанализировано {analyzed_vacancies} вакансий."
            )
        else:
            await progress_message.edit_text(
                f"Не удалось извлечь навыки из вакансий.\nПроанализировано {analyzed_vacancies} вакансий."
            )
    else:
        await update.message.reply_text("Введите запрос для анализа, например: /analyze Python разработчик")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия на кнопку с историей поиска"""
    query = update.callback_query.data.replace('search_', '')  # Извлекаем запрос из callback_data
    await update.callback_query.answer()

    # Используем callback_query.message для ответа
    if update.callback_query.message:
        # Переиспользуем код из search, передав данные в контекст
        context.args = [query]  # Добавляем запрос в context.args
        # Ответ на сообщение с историей поиска
        await update.callback_query.message.reply_text(f"Повторный поиск по запросу: {query}...")

        # Переиспользуем код из search с тем же запросом
        await search(update, context)
    else:
        await update.callback_query.answer("Произошла ошибка: сообщение недоступно.")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды поиска вакансий"""
    user = update.effective_user
    if context.args:
        query = " ".join(context.args)

        # Проверяем, какой объект доступен для ответа (callback_query или message)
        if update.message:
            await update.message.reply_text(f"Ищу вакансии по запросу: {query}...")
        elif update.callback_query.message:
            await update.callback_query.message.reply_text(f"Ищу вакансии по запросу: {query}...")

        # Сохраняем запрос в историю поиска
        add_to_search_history(user.id, query)

        # Запрос к API hh.ru
        vacancies = search_vacancies(query)
        if vacancies and "items" in vacancies:
            results = vacancies["items"]
            if results:
                message = "\n\n".join([
                    f"🔹 {vacancy['name']}\nКомпания: {vacancy['employer']['name']}\n"
                    f"Ссылка: {vacancy['alternate_url']}"
                    for vacancy in results
                ])
                # Ответ на поиск вакансий
                if update.message:
                    await update.message.reply_text(f"Найдено:\n{message}")
                elif update.callback_query.message:
                    await update.callback_query.message.reply_text(f"Найдено:\n{message}")

                # Добавление кнопок с последними запросами
                last_searches = get_last_searches(user.id)
                keyboard = [
                    [InlineKeyboardButton(text=query, callback_data=f"search_{query}")]
                    for query in last_searches
                ]
                if keyboard:
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    if update.message:
                        await update.message.reply_text(
                            "Последние ваши поиски:", reply_markup=reply_markup
                        )
                    elif update.callback_query.message:
                        await update.callback_query.message.reply_text(
                            "Последние ваши поиски:", reply_markup=reply_markup
                        )

            else:
                if update.message:
                    await update.message.reply_text("По вашему запросу ничего не найдено.")
                elif update.callback_query.message:
                    await update.callback_query.message.reply_text("По вашему запросу ничего не найдено.")
        else:
            if update.message:
                await update.message.reply_text("Произошла ошибка при запросе к API hh.ru.")
            elif update.callback_query.message:
                await update.callback_query.message.reply_text("Произошла ошибка при запросе к API hh.ru.")
    else:
        if update.message:
            await update.message.reply_text(
                "Введите запрос после команды /search, например: /search Python разработчик"
            )
        elif update.callback_query.message:
            await update.callback_query.message.reply_text(
                "Введите запрос после команды /search, например: /search Python разработчик"
            )

def main():
    """Основная логика бота"""
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("analyze", analyze))
    application.add_handler(CallbackQueryHandler(button))
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()