import os, psycopg2
from dotenv import load_dotenv
load_dotenv()

SQL = """
CREATE TABLE IF NOT EXISTS cursos (
  id SERIAL PRIMARY KEY,
  titulo TEXT NOT NULL,
  descricao TEXT,
  nivel TEXT,
  preco NUMERIC(10,2) NOT NULL DEFAULT 0,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  criado_em TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE IF NOT EXISTS pedidos (
  id SERIAL PRIMARY KEY,
  curso_id INT REFERENCES cursos(id),
  nome_cliente TEXT NOT NULL,
  telefone TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'pendente',
  criado_em TIMESTAMPTZ DEFAULT now()
);
"""

with psycopg2.connect(os.getenv("DATABASE_URL"), connect_timeout=10) as con:
    with con.cursor() as cur:
        cur.execute(SQL)
print("Tabelas criadas.")