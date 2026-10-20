"""DTO do resultado do comparador."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DiferencaDTO:
    """Uma divergência de tabela ou coluna entre a conexão local e remota.

    propriedade usa COLUMN_TYPE/IS_NULLABLE/... quando ambas as colunas
    existem ou TABELA_AUSENTE_*/COLUNA_AUSENTE_* em caso de ausência.
    """

    tabela: str
    campo: str
    diferenca: str
    local: Any
    remoto_ssh: Any
