"""Comparação determinística de estruturas; nenhuma dependência de MySQL/SSH."""

from __future__ import annotations

from comparador.dto.diferenca import DiferencaDTO
from comparador.dto.estrutura import EstruturaBancoDTO


# Nome do atributo do ColunaDTO -> nome técnico da propriedade no MySQL.
PROPRIEDADES = (
    ("tipo", "COLUMN_TYPE"),
    ("aceita_nulo", "IS_NULLABLE"),
    ("valor_padrao", "COLUMN_DEFAULT"),
    ("extra", "EXTRA"),
    ("chave", "COLUMN_KEY"),
    ("charset", "CHARACTER_SET_NAME"),
    ("collation", "COLLATION_NAME"),
    ("expressao_gerada", "GENERATION_EXPRESSION"),
    ("comentario", "COLUMN_COMMENT"),
    ("posicao", "ORDINAL_POSITION"),
)


def comparar_estruturas(
    local: EstruturaBancoDTO,
    remoto: EstruturaBancoDTO,
    tabela: str | None = None,
) -> list[DiferencaDTO]:
    """Retorna apenas diferenças; preserva a distinção local/remoto.

    Se --tabela apontar para uma tabela presente em apenas um banco, a
    ausência será registrada. Erra somente quando não existir em nenhum.
    """
    tabelas_local = local.tabelas
    tabelas_remoto = remoto.tabelas
    if tabela and tabela not in tabelas_local and tabela not in tabelas_remoto:
        raise ValueError(f"Tabela {tabela!r} ausente nas duas conexões.")

    nomes = {tabela} if tabela else (tabelas_local.keys() | tabelas_remoto.keys())
    diferencas: list[DiferencaDTO] = []
    for nome in sorted(nomes):
        if nome not in tabelas_local:
            diferencas.append(DiferencaDTO(nome, "", "TABELA_AUSENTE_LOCAL", "AUSENTE", "EXISTE"))
            continue
        if nome not in tabelas_remoto:
            diferencas.append(DiferencaDTO(nome, "", "TABELA_AUSENTE_REMOTO", "EXISTE", "AUSENTE"))
            continue

        colunas_local = tabelas_local[nome].colunas
        colunas_remoto = tabelas_remoto[nome].colunas
        for campo in sorted(colunas_local.keys() | colunas_remoto.keys()):
            if campo not in colunas_local:
                diferencas.append(DiferencaDTO(
                    nome, campo, "COLUNA_AUSENTE_LOCAL", "AUSENTE", colunas_remoto[campo].tipo
                ))
                continue
            if campo not in colunas_remoto:
                diferencas.append(DiferencaDTO(
                    nome, campo, "COLUNA_AUSENTE_REMOTO", colunas_local[campo].tipo, "AUSENTE"
                ))
                continue

            esquerda, direita = colunas_local[campo], colunas_remoto[campo]
            for atributo, propriedade_mysql in PROPRIEDADES:
                valor_local = getattr(esquerda, atributo)
                valor_remoto = getattr(direita, atributo)
                if valor_local != valor_remoto:
                    diferencas.append(DiferencaDTO(
                        nome, campo, propriedade_mysql, valor_local, valor_remoto
                    ))
    return diferencas
