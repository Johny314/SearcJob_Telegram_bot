from db_config import get_connection

def create_tables():
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE search_history (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255),
                    search_query VARCHAR(255),
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