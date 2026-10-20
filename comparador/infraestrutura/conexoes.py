"""Abertura e fechamento seguros das duas conexões e do túnel SSH."""

from __future__ import annotations

from contextlib import contextmanager, closing
from dataclasses import replace
from getpass import getpass
from typing import Iterator, TYPE_CHECKING

from comparador.dto.configuracao import ComparacaoConfigDTO, MySQLConfigDTO
from comparador.infraestrutura.chaves_ssh import converter_chave_publica_host

if TYPE_CHECKING:
    from mysql.connector.connection import MySQLConnection


def preencher_senha_mysql(config: MySQLConfigDTO, rotulo: str) -> MySQLConfigDTO:
    """Obtém a senha pelo prompt somente se não estiver configurada.

    A chave SSH jamais é passada como senha do banco de dados.
    """
    if config.password is not None:
        return config
    return replace(config, password=getpass(f"Senha MySQL ({rotulo}): "))


def _conectar_mysql(config: MySQLConfigDTO, *, porta: int | None = None):
    import mysql.connector

    return mysql.connector.connect(
        host=config.host if porta is None else "127.0.0.1",
        port=config.port if porta is None else porta,
        user=config.user,
        password=config.password,
        connection_timeout=config.connection_timeout,
    )


@contextmanager
def abrir_conexoes(config: ComparacaoConfigDTO) -> Iterator[tuple[MySQLConnection, MySQLConnection]]:
    """Garante fechamento das conexões e do túnel mesmo após uma falha."""
    from sshtunnel import SSHTunnelForwarder

    local_cfg = preencher_senha_mysql(config.local, "local")
    remoto_cfg = preencher_senha_mysql(config.remoto, "remoto via SSH")

    ssh = config.ssh
    chave = ssh.chave_privada()
    argumentos_ssh = {
        "ssh_username": ssh.user,
        "remote_bind_address": (config.remoto.host, config.remoto.port),
        "local_bind_address": ("127.0.0.1", 0),
    }
    if ssh.password:
        argumentos_ssh["ssh_password"] = ssh.password
    if chave:
        argumentos_ssh["ssh_pkey"] = str(chave)
        if ssh.key_passphrase:
            argumentos_ssh["ssh_private_key_password"] = ssh.key_passphrase
    if ssh.host_key:
        argumentos_ssh["ssh_host_key"] = converter_chave_publica_host(
            ssh.host_key, ssh.host, ssh.port
        )

    print(f"Conectando ao MySQL local ({local_cfg.schema})...")
    with closing(_conectar_mysql(local_cfg)) as local:
        print(f"Abrindo túnel SSH com {ssh.user}@{ssh.host}:{ssh.port}...")
        with SSHTunnelForwarder((ssh.host, ssh.port), **argumentos_ssh) as tunel:
            print(f"Conectando ao MySQL remoto ({remoto_cfg.schema})...")
            with closing(_conectar_mysql(remoto_cfg, porta=tunel.local_bind_port)) as remoto:
                yield local, remoto
