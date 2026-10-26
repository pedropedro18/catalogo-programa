import os
from contextlib import contextmanager
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
BASE = Path(__file__).parent

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CursoIn(BaseModel):
    titulo: str
    descricao: str = ""
    categoria: str = ""
    nivel: str = ""
    preco: float


class PedidoIn(BaseModel):
    curso_id: int
    nome_cliente: str
    telefone: str


@contextmanager
def db():
    con = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


@app.on_event("startup")
def preparar_base():
    # Cria a coluna "categoria" se ainda não existir (seguro correr várias vezes)
    try:
        with db() as con, con.cursor() as cur:
            cur.execute(
                "ALTER TABLE cursos ADD COLUMN IF NOT EXISTS categoria TEXT NOT NULL DEFAULT ''"
            )
    except Exception as e:
        print("Aviso ao preparar a base de dados:", e)


def exigir_admin(token: str | None):
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(401, "Não autorizado")


@app.get("/api/verificar")
def verificar(x_token: str | None = Header(None)):
    exigir_admin(x_token)
    return {"ok": True}


@app.get("/api/cursos")
def listar_cursos():
    with db() as con, con.cursor() as cur:
        cur.execute("SELECT * FROM cursos WHERE ativo ORDER BY id")
        return cur.fetchall()


@app.post("/api/cursos")
def criar_curso(c: CursoIn, x_token: str | None = Header(None)):
    exigir_admin(x_token)
    with db() as con, con.cursor() as cur:
        cur.execute(
            """INSERT INTO cursos (titulo, descricao, categoria, nivel, preco)
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (c.titulo, c.descricao, c.categoria, c.nivel, c.preco),
        )
        return cur.fetchone()


@app.put("/api/cursos/{curso_id}")
def atualizar_curso(curso_id: int, c: CursoIn, x_token: str | None = Header(None)):
    exigir_admin(x_token)
    with db() as con, con.cursor() as cur:
        cur.execute(
            """UPDATE cursos SET titulo=%s, descricao=%s, categoria=%s, nivel=%s, preco=%s
               WHERE id=%s RETURNING *""",
            (c.titulo, c.descricao, c.categoria, c.nivel, c.preco, curso_id),
        )
        linha = cur.fetchone()
        if not linha:
            raise HTTPException(404, "Curso não encontrado")
        return linha


@app.delete("/api/cursos/{curso_id}")
def apagar_curso(curso_id: int, x_token: str | None = Header(None)):
    exigir_admin(x_token)
    with db() as con, con.cursor() as cur:
        # só esconde do catálogo, não apaga de vez
        cur.execute("UPDATE cursos SET ativo = FALSE WHERE id=%s", (curso_id,))
    return {"ok": True}


@app.post("/api/pedidos")
def criar_pedido(p: PedidoIn):
    with db() as con, con.cursor() as cur:
        cur.execute(
            """INSERT INTO pedidos (curso_id, nome_cliente, telefone)
               VALUES (%s, %s, %s) RETURNING *""",
            (p.curso_id, p.nome_cliente, p.telefone),
        )
        return cur.fetchone()


@app.get("/api/pedidos")
def listar_pedidos(x_token: str | None = Header(None)):
    exigir_admin(x_token)
    with db() as con, con.cursor() as cur:
        cur.execute("SELECT * FROM pedidos ORDER BY id DESC")
        return cur.fetchall()


@app.get("/")
def pagina_catalogo():
    return FileResponse(BASE / "public" / "static" / "catalogo.html")


@app.get("/admin")
def pagina_admin():
    return FileResponse(BASE / "public" / "admin.html")


# Tem de ficar no fim: serve /admin.html e /static/catalogo.html
app.mount("/", StaticFiles(directory=BASE / "public", html=True), name="public")