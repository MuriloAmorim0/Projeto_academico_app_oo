import numpy as np
from typing import Optional
from .models import Usuario, ResultadoExperimento, TipoUsuario
from .repository import MemoriaRepository


class SistemaService:
    def __init__(self) -> None:
        self.repo = MemoriaRepository()

    # ---------- Usuários ----------

    def cadastrar_usuario(self, nome: str, email: str, tipo: TipoUsuario) -> Usuario:
        usuario = Usuario(nome=nome, email=email, tipo=tipo)
        self.repo.salvar_usuario(usuario)
        return usuario

    def login(self, email: str, nome_opcional: str = "") -> Optional[Usuario]:
        usuario = self.repo.obter_usuario(email)
        if usuario:
            return usuario

        # se não existir, cria um aluno simples (simulação)
        if not nome_opcional:
            nome_opcional = "Usuário"

        novo = Usuario(nome=nome_opcional, email=email, tipo="Aluno")
        self.repo.salvar_usuario(novo)
        return novo

    # ---------- Experimento ----------

    def rodar_experimento(
        self,
        email_usuario: str,
        tempo_total: int,
        vazao_entrada: float,
        vazao_saida: float,
        altura_max: float,
    ) -> ResultadoExperimento:
        """Simulação simples, apenas para fins de layout."""
        tempo = np.linspace(0, tempo_total, tempo_total)
        nivel_ideal = altura_max * (1 - np.exp(-tempo / 30))
        nivel_aluno = nivel_ideal + np.random.normal(0, 0.5, tempo_total)

        erro_medio = float(np.mean(np.abs(nivel_aluno - nivel_ideal)))
        altura_maxima = float(np.max(nivel_aluno))

        resultado = ResultadoExperimento(
            tempo=tempo,
            nivel_ideal=nivel_ideal,
            nivel_aluno=nivel_aluno,
            erro_medio=erro_medio,
            altura_maxima=altura_maxima,
            tempo_total=int(tempo_total),
        )

        self.repo.salvar_resultado(email_usuario, resultado)
        return resultado

    def obter_ultimo_resultado(self, email_usuario: str) -> Optional[ResultadoExperimento]:
        return self.repo.obter_resultado(email_usuario)
