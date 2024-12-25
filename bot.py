import os
from collections import Counter

import pandas as pd
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes, MessageHandler, filters,
)
from dotenv import load_dotenv

from search_service import search_vacancies
from database_service import add_to_search_history, get_last_searches
from analyze_service import analyze_skills, extract_skills

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome the user and display buttons for actions."""
    user = update.effective_user
    await display_main_menu(update, context, f"Привет, {user.first_name}! Что вы хотите сделать?")


async def display_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    """Display the main menu with static action buttons."""
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск вакансий", callback_data="action_search")],
        [InlineKeyboardButton("🧩 Анализ компетенций", callback_data="action_analyze")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(message, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)


async def handle_action_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """React to the user's main action choice and show the search menu."""
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "action_search":
        # Display the search query selection menu
        last_searches = get_last_searches(user_id)
        await switch_to_search_menu(query, last_searches, "search_", "поиска вакансий")

    elif query.data == "action_analyze":
        # Display the analysis query selection menu
        last_searches = get_last_searches(user_id)
        await switch_to_search_menu(query, last_searches, "analyze_", "анализа компетенций")


async def switch_to_search_menu(query, last_searches, callback_prefix, mode_label):
    """Display a menu of previously used queries or a button for a new query."""
    keyboard = []

    # Add buttons for the last searches (limit to 5 searches if needed)
    for search_query in last_searches[:5]:
        keyboard.append(
            [InlineKeyboardButton(search_query, callback_data=f"{callback_prefix}{search_query}")]
        )

    # Add button to create a new query
    keyboard.append([InlineKeyboardButton("➕ Новый запрос", callback_data=f"{callback_prefix}new")])

    # Send the message with the menu
    await query.edit_message_text(
        f"Выберите один из последних запросов для {mode_label} или создайте новый:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def search_or_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the search or analysis requests from user input or history."""
    query = update.callback_query
    user_id = query.from_user.id

    button_data = query.data
    mode = "search" if "search_" in button_data else "analyze"

    search_query = button_data.removeprefix("search_").removeprefix("analyze_")
    if search_query == "new":
        # Let the user input a new query
        await query.message.reply_text(
            f"Введите запрос для {'поиска вакансий' if mode == 'search' else 'анализа компетенций'}:"
        )
        context.user_data["mode"] = mode
        context.user_data["waiting_for_input"] = True
    else:
        # Use the selected query for search or analysis
        if mode == "search":
            await perform_search(user_id, search_query, update, context)
        else:
            await perform_analysis(user_id, search_query, update, context)


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new queries typed by the user."""
    user_id = update.effective_user.id
    mode = context.user_data.get("mode")
    if mode and context.user_data.get("waiting_for_input"):
        search_query = update.message.text.strip()

        add_to_search_history(user_id, search_query)
        context.user_data["waiting_for_input"] = False

        if mode == "search":
            await perform_search(user_id, search_query, update, context)
        elif mode == "analyze":
            await perform_analysis(user_id, search_query, update, context)


async def perform_search(user_id, search_query, update, context):
    """Выполняет поиск вакансий по запросу и отправляет результаты."""
    url = "https://api.hh.ru/vacancies"
    params = {"text": search_query, "per_page": 5}  # Укажите параметры запроса

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Формируем список вакансий для вывода
        vacancies = []
        for item in data.get("items", []):
            vacancy = f"{item['name']} - {item['employer']['name']}\n{item['alternate_url']}\n"
            vacancies.append(vacancy)

        if vacancies:
            search_results = "Найденные вакансии:\n\n" + "\n".join(vacancies)
        else:
            search_results = "По вашему запросу ничего не найдено."

    except Exception as e:
        search_results = f"Произошла ошибка при поиске: {e}"

    await display_main_menu(update, context, search_results)


async def perform_analysis(user_id, search_query, update, context):
    """Анализирует данные по навыкам из результатов поиска."""
    url = "https://api.hh.ru/vacancies"
    params = {"text": search_query, "per_page": 100}  # Увелечение количества записей для анализа

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Анализируйте навыки из каждой вакансии
        all_skills = []
        for vacancy in data.get("items", []):
            skills = extract_skills(vacancy)
            all_skills.extend(skills)

        # Подсчитываем топ навыков
        skill_counts = Counter(all_skills)
        top_skills = skill_counts.most_common(10)  # Топ-10 навыков

        if top_skills:
            analysis_results = "Топ-10 ключевых навыков по вашему запросу:\n\n" + \
                               "\n".join([f"{skill}: {count}" for skill, count in top_skills])
        else:
            analysis_results = "Не удалось найти навыков для анализа."

    except Exception as e:
        analysis_results = f"Произошла ошибка при анализе данных: {e}"

    await display_main_menu(update, context, analysis_results)


# --- Main Application ---
def main():
    """Run the bot application."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers for commands
    application.add_handler(CommandHandler("start", start))

    # Handlers for callback queries
    application.add_handler(CallbackQueryHandler(handle_action_selection, pattern="^action_"))
    application.add_handler(CallbackQueryHandler(search_or_analyze, pattern="^(search_|analyze_)"))

    # Handler for user text input
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_message_handler))

    # Start polling
    application.run_polling()


if __name__ == "__main__":
    main()