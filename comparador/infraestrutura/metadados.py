"""Consultas SOMENTE-LEITURA ao information_schema do MySQL 8."""

from __future__ import annotations

from typing import Any

from comparador.dto.estrutura import ColunaDTO, EstruturaBancoDTO, TabelaDTO


def verificar_schema(conexao: Any, schema: str, origem: str) -> None:
    """Impede comparações enganosas se o schema estiver ausente."""
    cursor = conexao.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
            (schema,),
        )
        if cursor.fetchone()[0] == 0:
            raise ValueError(f"Schema {schema!r} não encontrado na conexão {origem}.")
    finally:
        cursor.close()


def obter_estrutura(conexao: Any, schema: str) -> EstruturaBancoDTO:
    """Lê tabelas físicas e metadados; não lê nenhuma linha de negócio."""
    cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT TABLE_NAME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
            """,
            (schema,),
        )
        colunas_por_tabela: dict[str, dict[str, ColunaDTO]] = {
            linha["TABLE_NAME"]: {} for linha in cursor.fetchall()
        }

        cursor.execute(
            """
            SELECT c.TABLE_NAME, c.COLUMN_NAME, c.COLUMN_TYPE,
                   c.IS_NULLABLE, c.COLUMN_DEFAULT, c.EXTRA, c.COLUMN_KEY,
                   c.CHARACTER_SET_NAME, c.COLLATION_NAME,
                   c.GENERATION_EXPRESSION, c.COLUMN_COMMENT, c.ORDINAL_POSITION
            FROM information_schema.COLUMNS AS c
            INNER JOIN information_schema.TABLES AS t
                ON t.TABLE_SCHEMA = c.TABLE_SCHEMA
               AND t.TABLE_NAME = c.TABLE_NAME
               AND t.TABLE_TYPE = 'BASE TABLE'
            WHERE c.TABLE_SCHEMA = %s
            ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
            """,
            (schema,),
        )
        for linha in cursor.fetchall():
            tabela = linha["TABLE_NAME"]
            coluna = ColunaDTO.da_consulta(linha)
            colunas_por_tabela[tabela][coluna.nome] = coluna

        return EstruturaBancoDTO(
            schema=schema,
            tabelas={
                nome: TabelaDTO(nome=nome, colunas=colunas)
                for nome, colunas in colunas_por_tabela.items()
            },
        )
    finally:
        cursor.close()
