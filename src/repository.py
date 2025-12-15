import sqlite3
from pathlib import Path
from typing import Dict, Optional

from .models import Usuario, ResultadoExperimento


DB_PATH = Path("experimento_tanque.db")


class MemoriaRepository:
    """Repositório simples em memória (sem banco de dados)."""

    def __init__(self) -> None:
        self._usuarios: Dict[str, Usuario] = {}          # chave = email
        self._resultados: Dict[str, ResultadoExperimento] = {}  # chave = email

    # ---------- Usuários ----------

    def salvar_usuario(self, usuario: Usuario) -> None:
        self._usuarios[usuario.email] = usuario

    def obter_usuario(self, email: str) -> Optional[Usuario]:
        return self._usuarios.get(email)

    # ---------- Resultados ----------

    def salvar_resultado(self, email: str, resultado: ResultadoExperimento) -> None:
        self._resultados[email] = resultado

    def obter_resultado(self, email: str) -> Optional[ResultadoExperimento]:
        return self._resultados.get(email)


class SQLiteRepository:
    """Repositório usando SQLite (persistente)."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._criar_tabelas()

    def _conectar(self):
        return sqlite3.connect(self.db_path)

    def _criar_tabelas(self) -> None:
        with self._conectar() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    email TEXT PRIMARY KEY,
                    nome  TEXT NOT NULL,
                    tipo  TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS resultados (
                    email        TEXT PRIMARY KEY,
                    tempo        BLOB NOT NULL,
                    nivel_ideal  BLOB NOT NULL,
                    nivel_aluno  BLOB NOT NULL,
                    erro_medio   REAL NOT NULL,
                    altura_max   REAL NOT NULL,
                    tempo_total  INTEGER NOT NULL,
                    FOREIGN KEY(email) REFERENCES usuarios(email)
                )
                """
            )
            conn.commit()

    # ---------- Usuários ----------

    def salvar_usuario(self, usuario: Usuario) -> None:
        with self._conectar() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO usuarios (email, nome, tipo)
                VALUES (?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    nome = excluded.nome,
                    tipo = excluded.tipo
                """,
                (usuario.email, usuario.nome, usuario.tipo),
            )
            conn.commit()

    def obter_usuario(self, email: str) -> Optional[Usuario]:
        with self._conectar() as conn:
            cur = conn.cursor()
            cur.execute("SELECT nome, email, tipo FROM usuarios WHERE email = ?", (email,))
            row = cur.fetchone()

        if row is None:
            return None
        nome, email, tipo = row
        return Usuario(nome=nome, email=email, tipo=tipo)  # type: ignore[arg-type]

    # ---------- Resultados ----------

    def salvar_resultado(self, email: str, resultado: ResultadoExperimento) -> None:
        import numpy as np
        
        tempo_bytes = resultado.tempo.tobytes()
        ideal_bytes = resultado.nivel_ideal.tobytes()
        aluno_bytes = resultado.nivel_aluno.tobytes()

        with self._conectar() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO resultados (
                    email, tempo, nivel_ideal, nivel_aluno,
                    erro_medio, altura_max, tempo_total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    tempo       = excluded.tempo,
                    nivel_ideal = excluded.nivel_ideal,
                    nivel_aluno = excluded.nivel_aluno,
                    erro_medio  = excluded.erro_medio,
                    altura_max  = excluded.altura_max,
                    tempo_total = excluded.tempo_total
                """,
                (
                    email,
                    tempo_bytes,
                    ideal_bytes,
                    aluno_bytes,
                    resultado.erro_medio,
                    resultado.altura_maxima,
                    resultado.tempo_total,
                ),
            )
            conn.commit()

    def obter_resultado(self, email: str) -> Optional[ResultadoExperimento]:
        import numpy as np

        with self._conectar() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT tempo, nivel_ideal, nivel_aluno,
                       erro_medio, altura_max, tempo_total
                FROM resultados
                WHERE email = ?
                """,
                (email,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        tempo_bytes, ideal_bytes, aluno_bytes, erro_medio, altura_max, tempo_total = row

        tempo = np.frombuffer(tempo_bytes, dtype=np.float64)
        nivel_ideal = np.frombuffer(ideal_bytes, dtype=np.float64)
        nivel_aluno = np.frombuffer(aluno_bytes, dtype=np.float64)

        return ResultadoExperimento(
            tempo=tempo,
            nivel_ideal=nivel_ideal,
            nivel_aluno=nivel_aluno,
            erro_medio=erro_medio,
            altura_maxima=altura_max,
            tempo_total=tempo_total,
        )
