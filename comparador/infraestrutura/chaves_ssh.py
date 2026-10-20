"""Validação e conversão da chave pública do servidor SSH.

O sshtunnel 0.4.0 encaminha ssh_host_key ao
paramiko.Transport.connect(hostkey=...), que espera uma instância PKey.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from paramiko import PKey


def converter_chave_publica_host(valor: str, host: str, port: int) -> PKey:
    """Transforma uma chave pública do servidor SSH em paramiko.PKey.

    Aceita "ssh-ed25519 AAAA...", "host ssh-ed25519 AAAA..." e
    "[host]:2222 ssh-ed25519 AAAA...". Também aceita chaves RSA e ECDSA.
    A chave privada de login SSH e fingerprints SHA256 não são aceitos aqui.
    """
    import paramiko

    partes = valor.strip().split()
    if not partes:
        raise ValueError("SSH_HOST_KEY está vazio.")

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
        nomes_permitidos = {host, f"[{host}]:{port}"}
        if not any(nome in nomes_permitidos for nome in hosts.split(",")):
            raise ValueError(
                f"SSH_HOST_KEY indica outro host ({hosts!r}); esperado {host!r} na porta {port}."
            )
        linha = f"{hosts} {tipo} {dados}"
    else:
        raise ValueError(
            "SSH_HOST_KEY inválida: use 'ssh-ed25519 AAAA...' ou "
            "'host ssh-ed25519 AAAA...' do known_hosts. "
            "Fingerprint SHA256 e caminho de chave privada não são aceitos."
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
