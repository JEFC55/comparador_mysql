"""Validação e conversão da chave pública do servidor SSH.

O sshtunnel 0.4.0 encaminha ssh_host_key ao
paramiko.Transport.connect(hostkey=...), que espera uma instância PKey.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paramiko import PKey


def _ler_known_hosts(caminho: Path, host: str, port: int) -> PKey:
    """Obtém uma chave pública previamente registrada e confiada no OpenSSH."""
    import paramiko

    if not caminho.is_file():
        raise ValueError(
            f"SSH_HOST_KEY: arquivo known_hosts não encontrado: {caminho}. "
            "Confirme a identidade do servidor antes de confiar em uma chave nova."
        )
    try:
        chaves = paramiko.HostKeys()
        chaves.load(str(caminho))
    except (OSError, paramiko.SSHException, ValueError) as exc:
        raise ValueError(
            f"SSH_HOST_KEY: não foi possível ler o arquivo known_hosts: {caminho}."
        ) from exc

    nome_host = host if port == 22 else f"[{host}]:{port}"
    confiadas = chaves.lookup(nome_host)
    if not confiadas:
        raise ValueError(
            f"SSH_HOST_KEY: o host {nome_host!r} não está registrado em {caminho}. "
            "Confira a chave pública por canal confiável antes de adicioná-la."
        )

    # sshtunnel aceita uma única PKey. Prefere ED25519 quando houver várias;
    # caso o servidor escolha outra identidade, a conexão falha fechada.
    for algoritmo in (
        "ssh-ed25519",
        "ecdsa-sha2-nistp256",
        "ecdsa-sha2-nistp384",
        "ecdsa-sha2-nistp521",
        "ssh-rsa",
    ):
        if algoritmo in confiadas:
            return confiadas[algoritmo]
    return next(iter(confiadas.values()))


def converter_chave_publica_host(valor: str, host: str, port: int) -> PKey:
    """Transforma uma chave pública do servidor SSH em paramiko.PKey.

    Aceita "ssh-ed25519 AAAA...", "host ssh-ed25519 AAAA..." e
    "[host]:2222 ssh-ed25519 AAAA...". Também aceita chaves RSA e ECDSA.
    Também aceita "known_hosts" ou caminho para esse arquivo confiado.
    Chaves privadas de login e fingerprints SHA256 não são aceitos aqui.
    """
    import paramiko

    texto = valor.strip()
    if not texto:
        raise ValueError("SSH_HOST_KEY está vazio.")
    if texto.lower() == "known_hosts":
        return _ler_known_hosts(Path.home() / ".ssh" / "known_hosts", host, port)
    if texto.startswith("SHA256:"):
        raise ValueError(
            "SSH_HOST_KEY contém um fingerprint SHA256, não uma chave pública. "
            "Use SSH_HOST_KEY=known_hosts se o servidor já está registrado no "
            "OpenSSH, ou informe sua chave pública completa."
        )

    # Identifica caminhos antes de quebrar espaços (Windows aceita pastas com espaços).
    nome = texto.replace("\\\\", "/").rsplit("/", 1)[-1].lower()
    if nome.startswith("id_") or nome.endswith(".pub"):
        raise ValueError(
            "SSH_HOST_KEY recebeu caminho de chave de usuário. "
            "Use SSH_KEY_PATH para a chave privada e SSH_HOST_KEY=known_hosts "
            "para a chave pública confiada do servidor."
        )
    if "/" in texto or "\\\\" in texto:
        return _ler_known_hosts(Path(os.path.expandvars(texto)).expanduser(), host, port)

    partes = texto.split()

    tipos_validos = ("ssh-", "ecdsa-")
    if partes[0].startswith(tipos_validos):
        if len(partes) < 2:
            raise ValueError(
                "SSH_HOST_KEY precisa do tipo e do conteúdo Base64 da chave pública."
            )
        tipo, dados = partes[:2]
        linha = f"{host} {tipo} {dados}"
    elif len(partes) >= 3 and partes[1].startswith(tipos_validos):
        hosts, tipo, dados = partes[:3]
        nomes_permitidos = {host, f"[{host}]:22"} if port == 22 else {f"[{host}]:{port}"}
        if not any(nome in nomes_permitidos for nome in hosts.split(",")):
            raise ValueError(
                f"SSH_HOST_KEY indica outro host ({hosts!r}); esperado {host!r} na porta {port}."
            )
        linha = f"{hosts} {tipo} {dados}"
    else:
        raise ValueError(
            "SSH_HOST_KEY inválida: use SSH_HOST_KEY=known_hosts para carregar "
            "a chave confiada pelo OpenSSH, um caminho para known_hosts, "
            "ou a chave pública completa (ssh-ed25519 AAAA...)."
        )

    try:
        entrada = paramiko.hostkeys.HostKeyEntry.from_line(linha)
    except (paramiko.SSHException, paramiko.hostkeys.InvalidHostKey, ValueError) as exc:
        raise ValueError("SSH_HOST_KEY: chave pública malformada ou incompatível.") from exc

    if entrada is None or entrada.key is None:
        raise ValueError("SSH_HOST_KEY: algoritmo SSH desconhecido ou chave pública inválida.")
    if entrada.key.get_name() != tipo:
        raise ValueError("SSH_HOST_KEY: tipo de chave não corresponde ao conteúdo Base64.")
    return entrada.key
