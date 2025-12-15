from dataclasses import dataclass
from typing import Literal, List
import numpy as np


TipoUsuario = Literal["Aluno", "Professor"]


@dataclass
class Usuario:
    nome: str
    email: str
    tipo: TipoUsuario


@dataclass
class ResultadoExperimento:
    tempo: np.ndarray
    nivel_ideal: np.ndarray
    nivel_aluno: np.ndarray
    erro_medio: float
    altura_maxima: float
    tempo_total: int
