from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from constants import ANALYZE_WAITING_FOR_QUERY
from handlers.common import send_menu, generate_back_button
from services import get_last_searches, format_skills_output, process_vacancies, fetch_vacancies


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
                chat_id=update.message.chat_id if update.message else update.callback_query.message.chat_id,
                text="Пожалуйста, введите текст для анализа."
            )
            return ANALYZE_WAITING_FOR_QUERY

        # Сообщение о начале прогресса
        progress_message = await context.bot.send_message(
            chat_id=update.message.chat_id if update.message else update.callback_query.message.chat_id,
            text="Начинаем загрузку данных... Прогресс: 0%"
        )

        # Загрузка данных (vacancies)
        total_vacancies_to_fetch = 2000
        all_vacancies = []
        per_page = 100
        page = 0

        while len(all_vacancies) < total_vacancies_to_fetch:
            data = await fetch_vacancies(query=query, page=page, per_page=per_page)
            if not data or "items" not in data:
                break

            all_vacancies.extend(data["items"])
            progress_percent = min(int(len(all_vacancies) / total_vacancies_to_fetch * 100), 100)
            await progress_message.edit_text(text=f"Прогресс загрузки: {progress_percent}%")

            if len(data["items"]) < per_page:
                break

            page += 1

        if not all_vacancies:
            raise Exception("Не удалось загрузить вакансии.")

        # Анализируем вакансии
        top_skills, total_vacancies = process_vacancies({"items": all_vacancies})

        if total_vacancies > 0 and top_skills:
            results = format_skills_output(top_skills[:10], total_vacancies)  # Выводим ТОП-10 навыков
        else:
            results = "Не удалось извлечь навыки из предоставленных вакансий."

        # После успешного анализа
        await send_menu(update, f"Анализ завершён! Вот результаты:\n{results}", reply_markup=generate_back_button())

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Произошла ошибка: {e}")

    finally:
        context.user_data["is_processing"] = False

    return ANALYZE_WAITING_FOR_QUERY





