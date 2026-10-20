"""Saída legível no terminal e CSV compatível com Excel pt-BR."""

from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from comparador.dto.diferenca import DiferencaDTO


COLUNAS_CSV = ("tabela", "campo", "diferenca", "local", "remoto_ssh")


def imprimir_resultado(diferencas: Iterable[DiferencaDTO], qtd_local: int, qtd_remoto: int) -> None:
    dados = list(diferencas)
    print(f"\nTabelas locais: {qtd_local} | Tabelas remotas: {qtd_remoto}")
    print(f"Diferenças encontradas: {len(dados)}")
    for diferenca in dados:
        print(
            f"[{diferenca.tabela}.{diferenca.campo or '*'}] {diferenca.diferenca}: "
            f"local={diferenca.local!r} | remoto={diferenca.remoto_ssh!r}"
        )
    if not dados:
        print("Nenhuma diferença encontrada nas tabelas comparadas.")


def exportar_csv(diferencas: Iterable[DiferencaDTO], saida: Path) -> Path:
    """Sempre sobrescreve o CSV: evita uso acidental de relatório antigo."""
    caminho = saida.expanduser().resolve()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_CSV, delimiter=";")
        escritor.writeheader()
        for item in diferencas:
            escritor.writerow(asdict(item))
    return caminho
