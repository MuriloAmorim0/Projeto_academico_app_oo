import numpy as np
from typing import Optional

from .models import Usuario, ResultadoExperimento, TipoUsuario
from .repository import SQLiteRepository


class SistemaService:
    def __init__(self) -> None:
        self.repo = SQLiteRepository()

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

    # ---------- Experimento (função de transferência) ----------

    def rodar_experimento(
        self,
        email_usuario: str,
        tempo_total: int,
        vazao_entrada: float,
        vazao_saida: float,
        altura_max: float,
    ) -> ResultadoExperimento:
        """
        Modelo determinístico baseado em função de transferência de 1ª ordem:

            G(s) = K / (tau*s + 1)

        Resposta ao degrau de amplitude U:

            h(t) = K*U*(1 - exp(-t/tau))

        Aqui K e tau são fixos, para que, com os mesmos parâmetros,
        o gráfico gere sempre os mesmos valores.
        """

        # vetor de tempo: 0, 1, 2, ..., tempo_total-1
        tempo = np.linspace(0.0, float(tempo_total), int(tempo_total))

        # entrada (degrau) – usamos a vazão de entrada como amplitude
        U = max(float(vazao_entrada), 0.1)

        # parâmetros fixos da função de transferência
        # ganho estático: em regime o nível tende à altura_max
        K = altura_max / U
        tau = 30.0  # constante de tempo (ajuste didático)

        # resposta ideal do tanque (modelo teórico)
        nivel_ideal = K * U * (1.0 - np.exp(-tempo / tau))
        nivel_ideal = np.clip(nivel_ideal, 0.0, float(altura_max))

        # resposta do "aluno" SEM ruído: segue exatamente o modelo
        nivel_aluno = nivel_ideal.copy()

        # métricas
        erro_medio = float(np.mean(np.abs(nivel_aluno - nivel_ideal)))  # ≈ 0
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

    # ---------- Consulta ----------

    def obter_ultimo_resultado(self, email_usuario: str) -> Optional[ResultadoExperimento]:
        return self.repo.obter_resultado(email_usuario)
