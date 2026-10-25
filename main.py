import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=[""], allow_headers=[""])


def db():
    return psycopg2.connect(DATABASE_URL, connect_timeout=10,
                            cursor_factory=RealDictCursor)


class CursoIn(BaseModel):
    titulo: str
    descricao: str = ""
    nivel: str = ""
    preco: float = 0


class PedidoIn(BaseModel):
    curso_id: int
    nome_cliente: str
    telefone: str


def exigir_admin(token: str | None):
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        raise HTTPException(401, "Não autorizado")


@app.get("/api/cursos")
def listar_cursos():
    with db() as con, con.cursor() as cur:
        cur.execute("SELECT * FROM cursos WHERE ativo ORDER BY id")
        return cur.fetchall()


@app.post("/api/cursos")
def criar_curso(c: CursoIn, x_token: str | None = Header(None)):
    exigir_admin(x_token)
    with db() as con, con.cursor() as cur:
        cur.execute("""INSERT INTO cursos (titulo, descricao, nivel, preco)
                       VALUES (%s,%s,%s,%s) RETURNING *""",
                    (c.titulo, c.descricao, c.nivel, c.preco))
        return cur.fetchone()


@app.post("/api/pedidos")
def criar_pedido(p: PedidoIn):
    with db() as con, con.cursor() as cur:
        cur.execute("""INSERT INTO pedidos (curso_id, nome_cliente, telefone)
                       VALUES (%s,%s,%s) RETURNING *""",
                    (p.curso_id, p.nome_cliente, p.telefone))
        return cur.fetchone()


@app.get("/api/pedidos")
def listar_pedidos(x_token: str | None = Header(None)):
    exigir_admin(x_token)
    with db() as con, con.cursor() as cur:
        cur.execute("""SELECT p.*, c.titulo FROM pedidos p
                       LEFT JOIN cursos c ON c.id = p.curso_id
                       ORDER BY p.id DESC""")
        return cur.fetchall()


# Tem de ficar no fim, depois de todas as rotas /api
app.mount("/", StaticFiles(directory="static", html=True), name="site")