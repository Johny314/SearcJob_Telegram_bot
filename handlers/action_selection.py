from telegram import Update
from telegram.ext import ContextTypes


# Обработчик выбора действия из меню
async def handle_action_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает кнопки меню."""
    query = update.callback_query

    if query:
        await query.answer()

        # В зависимости от выбора выполняем действие
        if query.data == "search":
            await query.edit_message_text("Введите запрос для поиска вакансий 🔍")
        elif query.data == "analyze":
            await query.edit_message_text("Введите запрос для анализа навыков 📊")
        elif query.data == "about":
            await query.edit_message_text(
                "Этот бот помогает искать вакансии и анализировать ключевые навыки ℹ️"
            )
