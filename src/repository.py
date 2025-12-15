from typing import Dict, Optional
from .models import Usuario, ResultadoExperimento


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
