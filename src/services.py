import numpy as np
from typing import Optional, List, Dict

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

        O nível "ideal" segue esse modelo.
        O nível da "planta" (aluno) é uma versão levemente diferente, simulando
        incertezas e ruído de medição, permitindo calcular e(t), IAE e ISAE.
        """

        # vetor de tempo: 0, 1, 2, ..., tempo_total-1
        tempo = np.linspace(0.0, float(tempo_total), int(tempo_total))

        # entrada (degrau) – usamos a vazão de entrada como amplitude
        U = max(float(vazao_entrada), 0.1)

        # parâmetros do modelo ideal
        K = altura_max / U
        tau = 30.0  # constante de tempo (ajuste didático)

        # resposta ideal do tanque (modelo teórico)
        nivel_ideal = K * U * (1.0 - np.exp(-tempo / tau))
        nivel_ideal = np.clip(nivel_ideal, 0.0, float(altura_max))

        # ---------- MODELO DA PLANTA (REAL / ALUNO) ----------
        # planta um pouco diferente do modelo ideal
        K_planta = K * 0.95          # ganho 5% menor
        tau_planta = 35.0            # mais lenta
        nivel_planta = K_planta * U * (1.0 - np.exp(-tempo / tau_planta))

        # ruído de medição pequeno (gaussiano, média 0)
        ruido = np.random.normal(
            loc=0.0,
            scale=0.05 * float(altura_max),  # 5% da altura máxima
            size=tempo.shape,
        )
        nivel_planta = nivel_planta + ruido

        # limita à faixa física do tanque
        nivel_planta = np.clip(nivel_planta, 0.0, float(altura_max))

        # no app, chamamos o sinal da planta de "nível do aluno"
        nivel_aluno = nivel_planta

        # ---------- CÁLCULO DO ERRO ----------
        # erro instantâneo: e(t) = y_planta(t) - y_modelo(t)
        erro_instantaneo = nivel_aluno - nivel_ideal

        # passo de tempo aproximado (amostragem uniforme)
        dt = float(tempo[1] - tempo[0]) if len(tempo) > 1 else 1.0

        # IAE = Integral do Erro Absoluto ≈ soma discreta
        iae = float(np.sum(np.abs(erro_instantaneo)) * dt)

        # ISAE = Integral do Erro Quadrático Absoluto ≈ soma discreta
        isae = float(np.sum(erro_instantaneo ** 2) * dt)

        # erro médio absoluto simples (mantido por compatibilidade com o modelo)
        erro_medio = float(np.mean(np.abs(erro_instantaneo)))

        altura_maxima = float(np.max(nivel_aluno))

        resultado = ResultadoExperimento(
            tempo=tempo,
            nivel_ideal=nivel_ideal,
            nivel_aluno=nivel_aluno,
            erro_medio=erro_medio,
            altura_maxima=altura_maxima,
            tempo_total=int(tempo_total),
        )

        # OBS: se quiser salvar IAE e ISAE no banco, depois dá para estender o modelo
        # ResultadoExperimento para incluir esses campos e persistir também.

        self.repo.salvar_resultado(email_usuario, resultado)
        return resultado

    # ---------- Consulta ----------

    def obter_ultimo_resultado(self, email_usuario: str) -> Optional[ResultadoExperimento]:
        return self.repo.obter_resultado(email_usuario)

    def listar_todos_resultados(self) -> List[Dict]:
        """Encapsula o acesso ao ranking de resultados."""
        return self.repo.listar_todos_resultados()
