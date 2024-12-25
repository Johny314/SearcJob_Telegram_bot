import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", 5432)


def get_connection():
    """
    Устанавливает соединение с базой данных PostgreSQL.
    Возвращает объект соединения.
    """
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return connection
    except psycopg2.Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None


def add_to_search_history(user_id, search_query):
    """
    Добавляет новый запрос в историю запросов пользователя.

    :param user_id: ID пользователя
    :param search_query: текст поискового запроса
    """
    query = """
    INSERT INTO search_history (user_id, search_query, search_date)
    VALUES (%s, %s, NOW());
    """

    connection = get_connection()
    if not connection:
        return

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (user_id, search_query))
    except psycopg2.Error as e:
        print(f"Ошибка при добавлении запроса в базу данных: {e}")
    finally:
        connection.close()


def get_last_searches(user_id, limit=5):
    """
    Извлекает последние поисковые запросы пользователя.

    :param user_id: ID пользователя
    :param limit: количество запросов для извлечения
    :return: список строк с запросами
    """
    query = """
    SELECT search_query
    FROM search_history
    WHERE user_id = %s
    GROUP BY search_query
    ORDER BY MAX(search_date) DESC
    LIMIT %s;
    """

    connection = get_connection()
    if not connection:
        return []

    try:
        with connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (user_id, limit))
                results = cursor.fetchall()
                return [row['search_query'] for row in results]
    except psycopg2.Error as e:
        print(f"Ошибка при извлечении истории запросов: {e}")
        return []
    finally:
        connection.close()
