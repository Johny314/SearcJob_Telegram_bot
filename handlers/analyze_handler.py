import os

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from handlers.common import send_menu, generate_back_button
from services import (
    process_vacancies,
    add_to_search_history,
    fetch_vacancies
)

from services.database_service import get_last_searches

# Загрузка переменных окружения
load_dotenv()

ANALYZE_WAITING_FOR_QUERY = int(os.getenv("ANALYZE_WAITING_FOR_QUERY"))

async def prompt_analyze_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Предлагает пользователю ввести запрос для анализа навыков или выбрать запрос из истории.
    """
    user_id = update.callback_query.from_user.id

    # Получаем историю запросов пользователя
    history = await get_last_searches(user_id=user_id, limit=5)

    # Формируем кнопки: сначала для истории, потом другие действия
    buttons = []
    if history:
        for query in history:
            buttons.append([InlineKeyboardButton(query, callback_data=f"analyze_query_{query}")])

    # Добавляем кнопку для ввода нового запроса и возврата
    buttons.append([InlineKeyboardButton("Ввести новый запрос для анализа", callback_data="analyze_new_query")])
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="action_back")])

    reply_markup = InlineKeyboardMarkup(buttons)

    # Отправляем сообщение
    await send_menu(update, "Выберите действие для анализа навыков:", reply_markup)
    return ANALYZE_WAITING_FOR_QUERY


async def execute_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("is_processing", False):
        chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
        await context.bot.send_message(
            chat_id=chat_id,
            text="Ваш запрос уже обрабатывается. Подождите завершения текущего действия."
        )
        return ANALYZE_WAITING_FOR_QUERY

    context.user_data["is_processing"] = True

    try:
        if update.message and update.message.text:
            query = update.message.text.strip()
            chat_id = update.message.chat_id
        elif update.callback_query and update.callback_query.data:
            query = update.callback_query.data.removeprefix("analyze_query_").strip()
            chat_id = update.callback_query.message.chat_id
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Не могу обработать запрос. Пожалуйста, попробуйте снова."
            )
            return ANALYZE_WAITING_FOR_QUERY

        if not query:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Пожалуйста, введите текст для анализа."
            )
            return ANALYZE_WAITING_FOR_QUERY

        # Сохранение запроса в историю пользователя
        user_id = update.effective_user.id
        await add_to_search_history(user_id, query)

        # Сообщение о начале прогресса
        progress_message = await context.bot.send_message(
            chat_id=chat_id,
            text="🔄 Прогресс загрузки: 0%"
        )

        # Загрузка данных (vacancies)
        total_vacancies_to_fetch = 2000
        all_vacancies = []
        per_page = 100
        page = 0

        current_progress_text = progress_message.text

        while len(all_vacancies) < total_vacancies_to_fetch:
            data = await fetch_vacancies(query=query, page=page, per_page=per_page)
            if not data or "items" not in data:
                break

            all_vacancies.extend(data["items"])
            progress_percent = min(int(len(all_vacancies) / total_vacancies_to_fetch * 100), 100)

            new_progress_text = f"🔄 Прогресс загрузки: {progress_percent}%"
            if current_progress_text != new_progress_text:
                try:
                    await progress_message.edit_text(text=new_progress_text)
                    current_progress_text = new_progress_text
                except Exception as e:
                    if "Message is not modified" in str(e):
                        pass
                    else:
                        raise

            if len(data["items"]) < per_page:
                break

            page += 1

        if not all_vacancies:
            raise Exception("Не удалось загрузить вакансии.")

        # Обновляем сообщение о прогрессе
        await progress_message.edit_text(text="🔄 Данные загружены. Начинаем анализ...")

        # Анализ вакансий
        top_skills, total_vacancies = process_vacancies({"items": all_vacancies})

        if total_vacancies > 0 and top_skills:
            # Форматируем результаты анализа
            results = (
                f"📊 <b>Результаты анализа</b>\n"
                f"✅ <b>Проанализировано вакансий:</b> {total_vacancies}\n\n"
                f"<b>ТОП-10 навыков:</b>\n"
            )
            for i, (skill, count) in enumerate(top_skills[:10], 1):
                results += f"  {i}. {skill.capitalize()} — {count} упоминаний\n"
        else:
            results = "Не удалось извлечь ключевые навыки из предоставленных вакансий."

        # Удаляем сообщение с прогрессом загрузки
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=progress_message.message_id)
        except Exception as e:
            print(f"Ошибка при удалении сообщения о прогрессе: {e}")

        # После успешного анализа
        await context.bot.send_message(
            chat_id=chat_id,
            text=results,
            reply_markup=generate_back_button(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Произошла ошибка: {e}")

    finally:
        context.user_data["is_processing"] = False

    return ANALYZE_WAITING_FOR_QUERY