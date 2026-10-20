"""CONFIGURAÇÃO DO PROJETO.

Edite CONFIG_PADRAO abaixo caso queira manter valores padrão nos objetos.
Opcionalmente, crie um .env copiando o .env.example: quando preenchidas,
as variáveis do .env sobrepõem os defaults deste arquivo.

Não coloque senhas aqui: use .env (ignorado pelo Git) ou o prompt seguro.
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values

from comparador.dto.configuracao import (
    ComparacaoConfigDTO,
    MySQLConfigDTO,
    SSHConfigDTO,
)


# Objetos com valores padrão editáveis e autodocumentados.
# A descrição completa de cada atributo está na docstring dos DTOs.
CONFIG_PADRAO = ComparacaoConfigDTO(
    local=MySQLConfigDTO(
        host="127.0.0.1",       # MySQL instalado na sua máquina
        port=3306,              # Porta MySQL local
        user="root",            # Usuário MySQL local
        schema="dev_infinity",  # Schema local
        # password=None,        # Solicita a senha sem exibi-la no terminal
    ),
    remoto=MySQLConfigDTO(
        host="127.0.0.1",       # Endereço do MySQL VISTO do servidor SSH
        port=3306,              # Porta real do MySQL no servidor remoto
        user="root",            # Substitua pelo usuário MySQL remoto
        schema="dev_infinity",  # Schema remoto: mesmo nome do local
        # password=None,        # Solicita a senha MySQL remota
    ),
    ssh=SSHConfigDTO(
        host="",                 # OBRIGATÓRIO: servidor SSH (IP ou domínio)
        port=22,                # Porta do SSH (não a porta MySQL)
        user="",                # OBRIGATÓRIO: usuário SSH
        key_path=None,          # None: usa ~/.ssh/id_ed25519, se existir
        # password=None,        # Senha do SSH (se não usar chave)
        # key_passphrase=None,  # Senha de proteção da chave privada
        # host_key=None,        # Chave PÚBLICA do servidor, não a privada de login
    ),
    saida_csv=Path("diferencas_dev_infinity.csv"),
)


def _texto(valores: Mapping[str, str | None], prefixo: str, campo: str, padrao: str) -> str:
    """Sobrescreve o padrão apenas se a variável estiver preenchida."""
    return valores.get(f"{prefixo}_{campo}") or padrao


def _porta(valores: Mapping[str, str | None], prefixo: str, campo: str, padrao: int) -> int:
    bruto = valores.get(f"{prefixo}_{campo}")
    if not bruto:
        return padrao
    try:
        return int(bruto)
    except ValueError as exc:
        raise ValueError(f"{prefixo}_{campo} deve ser um número inteiro.") from exc


def _senha(valores: Mapping[str, str | None], nome: str, padrao: str | None) -> str | None:
    """Vazio mantém o prompt; senha efetiva vem do ambiente ou .env."""
    return valores.get(nome) or padrao


def carregar_configuracao(arquivo_env: Path | None = None) -> ComparacaoConfigDTO:
    """Monta a configuração final: objetos padrão + .env + ambiente.

    Precedência: variável de ambiente do sistema > arquivo .env > config.py.
    A função não solicita senha nem abre conexões; isso cabe à CLI.
    """
    caminho = arquivo_env or (Path(__file__).resolve().parent / ".env")
    # Lê .env sem alterar os.environ globalmente; ambiente real tem prioridade.
    valores: dict[str, str | None] = {**dotenv_values(caminho), **os.environ}

    p = CONFIG_PADRAO
    local = replace(
        p.local,
        host=_texto(valores, "LOCAL_MYSQL", "HOST", p.local.host),
        port=_porta(valores, "LOCAL_MYSQL", "PORT", p.local.port),
        user=_texto(valores, "LOCAL_MYSQL", "USER", p.local.user),
        password=_senha(valores, "LOCAL_MYSQL_PASSWORD", p.local.password),
        schema=_texto(valores, "LOCAL_MYSQL", "SCHEMA", p.local.schema),
    )
    remoto = replace(
        p.remoto,
        host=_texto(valores, "REMOTE_MYSQL", "HOST", p.remoto.host),
        port=_porta(valores, "REMOTE_MYSQL", "PORT", p.remoto.port),
        user=_texto(valores, "REMOTE_MYSQL", "USER", p.remoto.user),
        password=_senha(valores, "REMOTE_MYSQL_PASSWORD", p.remoto.password),
        schema=_texto(valores, "REMOTE_MYSQL", "SCHEMA", p.remoto.schema),
    )
    chave = valores.get("SSH_KEY_PATH")
    ssh = replace(
        p.ssh,
        host=valores.get("SSH_HOST") or p.ssh.host,
        port=_porta(valores, "SSH", "PORT", p.ssh.port),
        user=valores.get("SSH_USER") or p.ssh.user,
        password=_senha(valores, "SSH_PASSWORD", p.ssh.password),
        key_path=Path(os.path.expandvars(chave)).expanduser() if chave else p.ssh.key_path,
        key_passphrase=_senha(valores, "SSH_KEY_PASSPHRASE", p.ssh.key_passphrase),
        host_key=valores.get("SSH_HOST_KEY") or p.ssh.host_key,
    )
    saida = valores.get("OUTPUT_CSV")
    config = replace(
        p,
        local=local,
        remoto=remoto,
        ssh=ssh,
        saida_csv=Path(saida).expanduser() if saida else p.saida_csv,
    )
    config.validar()
    return config
