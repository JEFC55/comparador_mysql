"""Testes unitários da lógica de comparação, sem MySQL/SSH real."""

from dataclasses import replace

import pytest

from comparador.dto.estrutura import ColunaDTO, EstruturaBancoDTO, TabelaDTO
from comparador.servicos.comparacao import comparar_estruturas


def coluna(nome="id", tipo="bigint", **atualizacoes):
    padrao = ColunaDTO(
        nome=nome,
        tipo=tipo,
        aceita_nulo="NO",
        valor_padrao=None,
        extra="",
        chave="PRI",
        charset=None,
        collation=None,
        expressao_gerada="",
        comentario="",
        posicao=1,
    )
    return replace(padrao, **atualizacoes)


def banco(**tabelas):
    return EstruturaBancoDTO(
        schema="dev_infinity",
        tabelas={
            tabela: TabelaDTO(tabela, {col.nome: col for col in colunas})
            for tabela, colunas in tabelas.items()
        },
    )


def test_estruturas_identicas_nao_geram_diferencas():
    local = banco(tb_produto=[coluna()])
    remoto = banco(tb_produto=[coluna()])
    assert comparar_estruturas(local, remoto) == []


def test_detecta_tabelas_ausentes_dos_dois_lados():
    local = banco(tb_so_local=[coluna()])
    remoto = banco(tb_so_remoto=[coluna()])
    diferencas = comparar_estruturas(local, remoto)
    assert [(d.tabela, d.diferenca) for d in diferencas] == [
        ("tb_so_local", "TABELA_AUSENTE_REMOTO"),
        ("tb_so_remoto", "TABELA_AUSENTE_LOCAL"),
    ]


def test_detecta_colunas_ausentes_dos_dois_lados():
    local = banco(tb_cliente=[coluna("id"), coluna("cpf", "varchar(11)")])
    remoto = banco(tb_cliente=[coluna("id"), coluna("cnpj", "varchar(14)")])
    diferencas = comparar_estruturas(local, remoto)
    assert [(d.campo, d.diferenca) for d in diferencas] == [
        ("cnpj", "COLUNA_AUSENTE_LOCAL"),
        ("cpf", "COLUNA_AUSENTE_REMOTO"),
    ]


def test_compara_tipo_nulidade_default_e_ordem():
    local = banco(tb_os=[coluna("numero", "int", aceita_nulo="NO", valor_padrao=0)])
    remoto = banco(tb_os=[coluna("numero", "bigint", aceita_nulo="YES", valor_padrao=1, posicao=2)])
    diferencas = comparar_estruturas(local, remoto)
    assert [d.diferenca for d in diferencas] == [
        "COLUMN_TYPE", "IS_NULLABLE", "COLUMN_DEFAULT", "ORDINAL_POSITION"
    ]


def test_filtro_de_tabela_preserva_ausencia():
    local = banco(tb_produto=[coluna()])
    remoto = banco()
    diferencas = comparar_estruturas(local, remoto, "tb_produto")
    assert len(diferencas) == 1
    assert diferencas[0].diferenca == "TABELA_AUSENTE_REMOTO"


def test_erro_tabela_ausente_nos_dois_bancos():
    with pytest.raises(ValueError, match="ausente nas duas"):
        comparar_estruturas(banco(), banco(), "tb_inexistente")
