"""Interface de linha de comando e orquestração do comparador."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from config import carregar_configuracao
from comparador.apresentacao.relatorios import exportar_csv, imprimir_resultado
from comparador.infraestrutura.metadados import obter_estrutura, verificar_schema
from comparador.servicos.comparacao import comparar_estruturas


def executar(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compara estruturas MySQL: dev_infinity local x remoto via SSH."
    )
    parser.add_argument("--tabela", help="Compara somente esta tabela (ex.: tb_produto)")
    parser.add_argument("--saida", type=Path, help="Caminho do relatório CSV")
    parser.add_argument("--env", type=Path, help="Arquivo .env alternativo")
    args = parser.parse_args(argumentos)

    try:
        from comparador.infraestrutura.conexoes import abrir_conexoes

        config = carregar_configuracao(args.env)
        if args.saida is not None:
            config = replace(config, saida_csv=args.saida)

        with abrir_conexoes(config) as (local_conn, remoto_conn):
            verificar_schema(local_conn, config.local.schema, "local")
            verificar_schema(remoto_conn, config.remoto.schema, "remota")
            local = obter_estrutura(local_conn, config.local.schema)
            remoto = obter_estrutura(remoto_conn, config.remoto.schema)

        diferencas = comparar_estruturas(local, remoto, args.tabela)
        imprimir_resultado(diferencas, len(local.tabelas), len(remoto.tabelas))
        caminho = exportar_csv(diferencas, config.saida_csv)
        print(f"\nRelatório CSV: {caminho}")
        return 0
    except (ValueError, OSError, ImportError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # Exceções próprias do driver MySQL ou da biblioteca de túnel SSH.
        print(f"Erro de conexão ou de consulta: {exc}", file=sys.stderr)
        return 1
