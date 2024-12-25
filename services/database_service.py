import asyncpg
import os

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", 5432)


async def get_connection():
    """
    Устанавливает асинхронное соединение с базой данных PostgreSQL.
    Возвращает объект соединения.
    """
    try:
        connection = await asyncpg.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
        )
        return connection
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None


async def get_last_searches(user_id, limit=5):
    """
    Асинхронно извлекает последние поисковые запросы пользователя.

    :param user_id: ID пользователя
    :param limit: Количество запросов для извлечения
    :return: Список строк с запросами
    """
    query = """
    SELECT search_query
    FROM search_history
    WHERE user_id = $1
    GROUP BY search_query
    ORDER BY MAX(search_date) DESC
    LIMIT $2;
    """

    connection = await get_connection()
    if not connection:
        return []

    try:
        # Выполняем запрос с параметрами
        rows = await connection.fetch(query, user_id, limit)
        return [row['search_query'] for row in rows]
    except Exception as e:
        print(f"Ошибка при извлечении истории запросов: {e}")
        return []
    finally:
        await connection.close()

async def add_to_search_history(user_id, search_query):
    """
    Добавляет новый запрос в историю запросов пользователя.

    :param user_id: ID пользователя
    :param search_query: текст поискового запроса
    """
    query = """
    INSERT INTO search_history (user_id, search_query, search_date)
    VALUES ($1, $2, NOW());
    """

    # Используем асинхронное подключение с asyncpg
    connection = await get_connection()
    if not connection:
        return

    try:
        # Выполняем запрос асинхронно
        await connection.execute(query, user_id, search_query)
    except Exception as e:
        print(f"Ошибка при добавлении запроса в базу данных: {e}")
    finally:
        # Закрываем соединение асинхронно
        await connection.close()
