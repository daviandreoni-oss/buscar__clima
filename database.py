import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


# ── Conexão ──────────────────────────────────────────────────────────────────

def get_connection():
    """Retorna uma conexão com o banco PostgreSQL (Neon)."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError(
            "Variável de ambiente DATABASE_URL não configurada. "
            "Adicione-a no arquivo .env."
        )
    return psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)


# ── Inicialização da tabela ───────────────────────────────────────────────────

def criar_tabela():
    """Cria a tabela historico_clima caso ainda não exista."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS historico_clima (
                        id           SERIAL PRIMARY KEY,
                        cidade       TEXT   NOT NULL,
                        data         TEXT   NOT NULL,
                        umidade      REAL,
                        vento        REAL,
                        precipitacao REAL,
                        temp_min     REAL,
                        temp_max     REAL,
                        UNIQUE (cidade, data)
                    )
                ''')
    finally:
        conn.close()


# ── Leitura ───────────────────────────────────────────────────────────────────

def buscar_no_banco(cidade: str) -> dict | None:
    """
    Busca o registro mais recente da cidade no banco.
    Retorna um dict com os dados ou None se não houver nenhum registro.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT cidade, data, umidade, vento, precipitacao, temp_min, temp_max
                FROM   historico_clima
                WHERE  cidade = %s
                ORDER  BY data DESC
                LIMIT  1
                ''',
                (cidade.strip().lower(),)
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


# ── Escrita ───────────────────────────────────────────────────────────────────

def salvar_historico(dados_clima: dict) -> bool:
    """
    Salva os dados climáticos no banco.
    Retorna True  → registro inserido.
    Retorna False → cidade/data já existia, nada foi salvo.
    """
    cidade       = dados_clima.get('cidade', '').strip().lower()
    data         = dados_clima.get('data')
    previsao     = dados_clima.get('previsao', [])
    primeiro_dia = previsao[0] if previsao else {}

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    INSERT INTO historico_clima
                        (cidade, data, umidade, vento, precipitacao, temp_min, temp_max)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (cidade, data) DO NOTHING
                    ''',
                    (
                        cidade,
                        data,
                        dados_clima.get('umidade'),
                        dados_clima.get('vento'),
                        dados_clima.get('precipitacao'),
                        primeiro_dia.get('temperatura_min'),
                        primeiro_dia.get('temperatura_max'),
                    )
                )
                return cur.rowcount > 0   # True = inseriu / False = já existia
    finally:
        conn.close()


# Garante que a tabela exista ao importar o módulo
criar_tabela()


# ── Listagem ─────────────────────────────────────────────────────────────────

def listar_historico() -> list:
    """Retorna todos os registros do histórico ordenados por data decrescente."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT id, cidade, data, umidade, vento, precipitacao, temp_min, temp_max
                FROM   historico_clima
                ORDER  BY data DESC, cidade ASC
            ''')
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()