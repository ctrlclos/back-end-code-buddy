import os
import psycopg2


def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Heroku uses postgres:// but psycopg2 requires postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        connection = psycopg2.connect(database_url, sslmode='require')
    else:
        connection = psycopg2.connect(
            host='localhost',
            database=os.getenv('POSTGRES_DATABASE'),
            user=os.getenv('POSTGRES_USERNAME'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
    return connection
