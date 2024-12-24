from db_config import get_connection

def create_tables():
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,  -- Используем INTEGER для user_id
                    search_query TEXT NOT NULL,  -- Используем TEXT для search_query
                    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            connection.commit()
            print("Tables created successfully!")
        except Exception as e:
            print(f"Error creating tables: {e}")
        finally:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    create_tables()