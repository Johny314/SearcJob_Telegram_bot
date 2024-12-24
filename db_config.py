import psycopg2


def get_connection():
    try:
        connection = psycopg2.connect(
            dbname="project_db",
            user="project_user",
            password="your_password",
            host="localhost",
            port="5432"
        )
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

connection = get_connection()
if connection:
    print("Connection successful!")
    connection.close()