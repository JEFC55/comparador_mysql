"""DTOs imutáveis para a estrutura lida do information_schema."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ColunaDTO:
    """Descrição de uma coluna; não armazena dados de linhas do negócio.

    A comparação abrange o tipo, nulidade, padrão, atributo extra, chaves,
    conjunto de caracteres, collation, expressão gerada, comentário e ordem.
    """

    nome: str
    tipo: str
    aceita_nulo: str
    valor_padrao: Any
    extra: str
    chave: str
    charset: str | None
    collation: str | None
    expressao_gerada: str
    comentario: str
    posicao: int

    @classmethod
    def da_consulta(cls, linha: Mapping[str, Any]) -> ColunaDTO:
        """Traduz o resultado do SELECT SQL para um DTO tipado."""
        return cls(
            nome=linha["COLUMN_NAME"],
            tipo=linha["COLUMN_TYPE"],
            aceita_nulo=linha["IS_NULLABLE"],
            valor_padrao=linha["COLUMN_DEFAULT"],
            extra=linha["EXTRA"],
            chave=linha["COLUMN_KEY"],
            charset=linha["CHARACTER_SET_NAME"],
            collation=linha["COLLATION_NAME"],
            expressao_gerada=linha["GENERATION_EXPRESSION"],
            comentario=linha["COLUMN_COMMENT"],
            posicao=linha["ORDINAL_POSITION"],
        )


@dataclass(frozen=True, slots=True)
class TabelaDTO:
    """Tabela física com suas colunas indexadas pelo nome."""

    nome: str
    colunas: dict[str, ColunaDTO]


@dataclass(frozen=True, slots=True)
class EstruturaBancoDTO:
    """Representa os metadados de um schema em uma conexão específica."""

    schema: str
    tabelas: dict[str, TabelaDTO]
