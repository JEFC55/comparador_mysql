"""Regressões para a validação e conversão de SSH_HOST_KEY."""

import sys
from types import ModuleType, SimpleNamespace

import pytest

from comparador.dto.configuracao import ComparacaoConfigDTO, MySQLConfigDTO, SSHConfigDTO
from comparador.infraestrutura.chaves_ssh import converter_chave_publica_host


@pytest.fixture
def paramiko_falso(monkeypatch):
    fake = ModuleType("paramiko")

    class SSHException(Exception):
        pass

    class InvalidHostKey(Exception):
        pass

    class PKeyFake:
        def __init__(self, algoritmo):
            self.algoritmo = algoritmo

        def get_name(self):
            return self.algoritmo

    class HostKeyEntry:
        @classmethod
        def from_line(cls, linha):
            campos = linha.split()
            if len(campos) != 3 or campos[2] == "INVALIDO":
                raise InvalidHostKey("malformado")
            return SimpleNamespace(key=PKeyFake(campos[1]))

    fake.SSHException = SSHException
    fake.hostkeys = SimpleNamespace(HostKeyEntry=HostKeyEntry, InvalidHostKey=InvalidHostKey)
    monkeypatch.setitem(sys.modules, "paramiko", fake)
    return fake


def test_chave_publica_simples_convertida_em_objeto(paramiko_falso):
    chave = converter_chave_publica_host("ssh-ed25519 AAAAEXEMPLO comentario", "host.exemplo", 22)
    assert chave.get_name() == "ssh-ed25519"
    assert not isinstance(chave, str)


def test_linha_known_hosts_convertida_em_objeto(paramiko_falso):
    chave = converter_chave_publica_host("host.exemplo ssh-rsa AAAAEXEMPLO", "host.exemplo", 22)
    assert chave.get_name() == "ssh-rsa"


def test_linha_known_hosts_porta_diferente(paramiko_falso):
    chave = converter_chave_publica_host(
        "[host.exemplo]:2222 ssh-ed25519 AAAAEXEMPLO", "host.exemplo", 2222
    )
    assert chave.get_name() == "ssh-ed25519"


def test_rejeita_chave_de_outro_servidor(paramiko_falso):
    with pytest.raises(ValueError, match="outro host"):
        converter_chave_publica_host(
            "estranho.exemplo ssh-ed25519 AAAAEXEMPLO", "host.exemplo", 22
        )


@pytest.mark.parametrize(
    "valor", ["SHA256:abc", "C:/Users/User/.ssh/id_ed25519", "ssh-ed25519", ""]
)
def test_rejeita_fingerprint_caminho_e_valor_incompleto(paramiko_falso, valor):
    with pytest.raises(ValueError, match="SSH_HOST_KEY"):
        converter_chave_publica_host(valor, "host.exemplo", 22)


def test_rejeita_chave_malformada(paramiko_falso):
    with pytest.raises(ValueError, match="malformada"):
        converter_chave_publica_host("ssh-ed25519 INVALIDO", "host.exemplo", 22)


def test_tunel_recebe_objeto_e_nao_string(paramiko_falso, monkeypatch):
    import comparador.infraestrutura.conexoes as conexoes

    tunnel_module = ModuleType("sshtunnel")
    recebido = {}

    class ForwarderFake:
        local_bind_port = 52001

        def __init__(self, addr, **kwargs):
            recebido.update(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class ConnFake:
        def close(self):
            pass

    tunnel_module.SSHTunnelForwarder = ForwarderFake
    monkeypatch.setitem(sys.modules, "sshtunnel", tunnel_module)
    monkeypatch.setattr(conexoes, "_conectar_mysql", lambda *args, **kwargs: ConnFake())
    monkeypatch.setattr(SSHConfigDTO, "chave_privada", lambda self: None)

    config = ComparacaoConfigDTO(
        local=MySQLConfigDTO(password="local"),
        remoto=MySQLConfigDTO(password="remota"),
        ssh=SSHConfigDTO(
            host="host.exemplo", user="joao", host_key="ssh-ed25519 AAAAEXEMPLO"
        ),
    )
    with conexoes.abrir_conexoes(config) as (local, remoto):
        assert local is not remoto

    assert recebido["ssh_host_key"].get_name() == "ssh-ed25519"
    assert not isinstance(recebido["ssh_host_key"], str)
    assert recebido["remote_bind_address"] == ("127.0.0.1", 3306)


def test_sem_host_key_mantem_configuracao_original(paramiko_falso, monkeypatch):
    import comparador.infraestrutura.conexoes as conexoes

    tunnel_module = ModuleType("sshtunnel")
    recebido = {}

    class ForwarderFake:
        local_bind_port = 52001

        def __init__(self, addr, **kwargs):
            recebido.update(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class ConnFake:
        def close(self):
            pass

    tunnel_module.SSHTunnelForwarder = ForwarderFake
    monkeypatch.setitem(sys.modules, "sshtunnel", tunnel_module)
    monkeypatch.setattr(conexoes, "_conectar_mysql", lambda *args, **kwargs: ConnFake())
    monkeypatch.setattr(SSHConfigDTO, "chave_privada", lambda self: None)
    config = ComparacaoConfigDTO(
        local=MySQLConfigDTO(password="local"),
        remoto=MySQLConfigDTO(password="remota"),
        ssh=SSHConfigDTO(host="host.exemplo", user="joao"),
    )
    with conexoes.abrir_conexoes(config):
        pass
    assert "ssh_host_key" not in recebido
