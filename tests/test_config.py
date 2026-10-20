"""Testes de configuração, defaults, caminhos e isolamento de credenciais."""

from pathlib import Path

import pytest

from comparador.dto.configuracao import ComparacaoConfigDTO, MySQLConfigDTO, SSHConfigDTO
from comparador.apresentacao.relatorios import exportar_csv
from comparador.dto.diferenca import DiferencaDTO
from config import carregar_configuracao


@pytest.fixture
def ambiente_limpo(monkeypatch):
    for chave in (
        "LOCAL_MYSQL_HOST", "LOCAL_MYSQL_PORT", "LOCAL_MYSQL_USER", "LOCAL_MYSQL_PASSWORD",
        "LOCAL_MYSQL_SCHEMA", "REMOTE_MYSQL_HOST", "REMOTE_MYSQL_PORT",
        "REMOTE_MYSQL_USER", "REMOTE_MYSQL_PASSWORD", "REMOTE_MYSQL_SCHEMA",
        "SSH_HOST", "SSH_PORT", "SSH_USER", "SSH_PASSWORD", "SSH_KEY_PATH",
        "SSH_KEY_PASSPHRASE", "SSH_HOST_KEY", "OUTPUT_CSV",
    ):
        monkeypatch.delenv(chave, raising=False)
    return monkeypatch


def test_padroes_mantem_dev_infinity_nos_dois_bancos():
    cfg = ComparacaoConfigDTO()
    assert cfg.local.schema == cfg.remoto.schema == "dev_infinity"
    assert cfg.local.port == cfg.remoto.port == 3306
    assert cfg.ssh.port == 22


def test_config_carrega_variaveis_sem_alterar_defaults(ambiente_limpo, tmp_path):
    env = tmp_path / ".env"
    env.write_text(
        "SSH_HOST=example.org\nSSH_USER=deploy\nSSH_KEY_PATH=\n"
        "REMOTE_MYSQL_USER=consulta\nLOCAL_MYSQL_SCHEMA=dev_infinity\n"
        "SSH_PORT=2201\nLOCAL_MYSQL_PASSWORD=senha_teste\n",
        encoding="utf-8",
    )
    cfg = carregar_configuracao(env)
    assert cfg.ssh.host == "example.org"
    assert cfg.ssh.port == 2201
    assert cfg.local.password == "senha_teste"
    assert cfg.remoto.user == "consulta"
    assert cfg.local.schema == cfg.remoto.schema == "dev_infinity"


def test_variavel_de_ambiente_tem_prioridade_ao_env(ambiente_limpo, tmp_path):
    ambiente_limpo.setenv("SSH_HOST", "do_ambiente")
    env = tmp_path / ".env"
    env.write_text("SSH_HOST=no_arquivo\nSSH_USER=usuario\n", encoding="utf-8")
    cfg = carregar_configuracao(env)
    assert cfg.ssh.host == "do_ambiente"


def test_ssh_sem_host_falha_com_orientacao(ambiente_limpo, tmp_path):
    with pytest.raises(ValueError, match="SSH_HOST e SSH_USER"):
        carregar_configuracao(tmp_path / "ausente.env")


def test_porta_invalida_falha_com_identificacao(ambiente_limpo, tmp_path):
    ambiente_limpo.setenv("SSH_HOST", "example.org")
    ambiente_limpo.setenv("SSH_USER", "deploy")
    ambiente_limpo.setenv("LOCAL_MYSQL_PORT", "abc")
    with pytest.raises(ValueError, match="LOCAL_MYSQL_PORT"):
        carregar_configuracao(tmp_path / "ausente.env")


def test_config_nao_expoe_senha_no_repr():
    cfg = MySQLConfigDTO(password="segredo")
    ssh = SSHConfigDTO(password="segredo_ssh", key_passphrase="segredo_chave")
    assert "segredo" not in repr(cfg)
    assert "segredo_ssh" not in repr(ssh)
    assert "segredo_chave" not in repr(ssh)


def test_exportacao_csv_sem_diferencas_gera_cabecalho(tmp_path):
    path = tmp_path / "relatorios" / "diferencas.csv"
    exportar_csv([], path)
    assert path.read_text(encoding="utf-8-sig").strip() == "tabela;campo;diferenca;local;remoto_ssh"


def test_exportacao_csv_com_diferenca(tmp_path):
    path = tmp_path / "saida.csv"
    exportar_csv([DiferencaDTO("tb_os", "id", "COLUMN_TYPE", "int", "bigint")], path)
    assert "tb_os;id;COLUMN_TYPE;int;bigint" in path.read_text(encoding="utf-8-sig")
