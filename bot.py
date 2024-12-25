import os
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
from dotenv import load_dotenv
from handlers import (
    start,
    prompt_search_query,
    execute_search,
    search_query_from_history,
    execute_analyze,
    prompt_analyze_query,
    analyze_query_from_history,
    display_main_menu,
    about_action,
)
from handlers.common import handle_new_query
from constants import SEARCH_WAITING_FOR_QUERY, ANALYZE_WAITING_FOR_QUERY

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Токен бота отсутствует. Проверьте файл .env.")


def main():
    """Основная функция для запуска Telegram-бота."""
    # Создаем приложение с использованием токена
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))

    # ConversationHandler для поиска
    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(prompt_search_query, pattern="^search$")],
            states={
                SEARCH_WAITING_FOR_QUERY: [
                    CallbackQueryHandler(search_query_from_history, pattern="^search_query_"),
                    CallbackQueryHandler(handle_new_query, pattern="^search_new_query$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, execute_search),
                ],
            },
            fallbacks=[CallbackQueryHandler(display_main_menu, pattern="^action_back$")],
        )
    )

    # ConversationHandler для анализа
    application.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(prompt_analyze_query, pattern="^action_analyze$")],
            states={
                ANALYZE_WAITING_FOR_QUERY: [
                    CallbackQueryHandler(analyze_query_from_history, pattern="^analyze_query_"),
                    CallbackQueryHandler(handle_new_query, pattern="^analyze_new_query$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, execute_analyze),
                ],
            },
            fallbacks=[CallbackQueryHandler(display_main_menu, pattern="^action_back$")],
        )
    )

    # CallbackHandler для раздела "О боте"
    application.add_handler(CallbackQueryHandler(about_action, pattern="^action_about$"))

    # Лог успешного запуска
    print("Бот запущен. Ожидаем взаимодействия с пользователями...")

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    main()
