import os

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.common import send_menu, generate_back_button
from services.database_service import get_last_searches, add_to_search_history
from services.search_service import fetch_vacancies

# Загрузка переменных окружения
load_dotenv()

SEARCH_WAITING_FOR_QUERY = int(os.getenv("SEARCH_WAITING_FOR_QUERY"))

async def prompt_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Промежуточный шаг: предлагает ввести текстовый запрос для поиска вакансий.
    """
    user_id = update.callback_query.from_user.id

    # Получаем историю запросов пользователя
    history = await get_last_searches(user_id=user_id, limit=5)

    # Формируем кнопки истории
    buttons = []
    for query in history:
        buttons.append([InlineKeyboardButton(query, callback_data=f"search_query_{query}")])

    # Добавляем кнопку для ручного ввода нового запроса
    buttons.append([InlineKeyboardButton("Введите новый запрос", callback_data="search_new_query")])

    # Добавляем кнопку "Назад"
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="action_back")])

    # Формируем разметку кнопок
    reply_markup = InlineKeyboardMarkup(buttons)

    # Отправляем сообщение с предложением ввести данные
    await send_menu(update, "Введите текст для поиска или выберите из истории:", reply_markup)
    return SEARCH_WAITING_FOR_QUERY


async def execute_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("is_processing", False):
        chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
        await context.bot.send_message(
            chat_id=chat_id,
            text="Ваш запрос уже обрабатывается. Подождите завершения текущего действия."
        )
        return SEARCH_WAITING_FOR_QUERY

    context.user_data["is_processing"] = True  # Устанавливаем флаг выполнения

    try:
        if update.message and update.message.text:
            query = update.message.text.strip()
            chat_id = update.message.chat_id
        elif update.callback_query and update.callback_query.data:
            query = update.callback_query.data.removeprefix("search_query_").strip()
            chat_id = update.callback_query.message.chat_id
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Не могу обработать запрос. Пожалуйста, попробуйте снова."
            )
            return SEARCH_WAITING_FOR_QUERY

        if not query:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Пожалуйста, введите текст для анализа."
            )
            return SEARCH_WAITING_FOR_QUERY

        # Сохранение запроса в историю пользователя
        user_id = update.effective_user.id
        await add_to_search_history(user_id, query)

        # Запрашиваем вакансии
        data = await fetch_vacancies(query=query, page=0, per_page=5)

        if data and data.get("items"):
            # Формируем красивый вывод вакансий
            results = []
            for item in data["items"]:
                name = item.get("name", "Не указано")  # Название вакансии
                employer = item.get("employer", {}).get("name", "Не указан")  # Работодатель
                city = item.get("area", {}).get("name", "Не указан")  # Город
                salary = item.get("salary")  # Зарплата
                url = item.get("alternate_url", "#")  # Ссылка на вакансию

                # Форматируем зарплату
                if salary:
                    if salary.get("from") and salary.get("to"):
                        salary = f"{salary['from']} - {salary['to']} {salary['currency']}"
                    elif salary.get("from"):
                        salary = f"от {salary['from']} {salary['currency']}"
                    elif salary.get("to"):
                        salary = f"до {salary['to']} {salary['currency']}"
                    else:
                        salary = "Не указана"
                else:
                    salary = "Не указана"

                # Формируем блок одной вакансии
                vacancy_text = (
                    f"📝 <b>{name}</b>\n"
                    f"🏢 Работодатель: {employer}\n"
                    f"📍 Город: {city}\n"
                    f"💰 Зарплата: {salary}\n"
                    f"🔗 <a href='{url}'>Подробнее о вакансии</a>"
                )
                results.append(vacancy_text)

            # Объединяем вакансии в единый текст
            results_text = "\n\n".join(results)
        else:
            results_text = "По вашему запросу вакансий не найдено."

        # Отправляем результат
        await context.bot.send_message(
            chat_id=chat_id,
            text=results_text,
            reply_markup=generate_back_button(),
            parse_mode="HTML",  # Указываем HTML для форматирования
            disable_web_page_preview=True  # Отключаем превью ссылок
        )

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Произошла ошибка: {e}")

    finally:
        context.user_data["is_processing"] = False

    return SEARCH_WAITING_FOR_QUERY



