import os
import psycopg2
from dotenv import load_dotenv

print("Pasta atual:", os.getcwd())
print("Ficheiros:", os.listdir("."))

load_dotenv()
url = os.getenv("DATABASE_URL")
print("URL lida:", url[:25] if url else None)

conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("SELECT version();")
print(cur.fetchone())
cur.close()
conn.close()