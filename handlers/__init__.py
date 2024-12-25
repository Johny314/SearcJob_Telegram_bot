from handlers.start_handler import start
from handlers.search_handler import (
    prompt_search_query,
    execute_search,
    search_query_from_history,
)
from handlers.analyze_handler import (
    prompt_analyze_query,  # Добавляем функцию сюда
    execute_analyze,
    analyze_query_from_history,
)
from handlers.common import display_main_menu
from handlers.about_handler import about_action
