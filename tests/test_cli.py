"""Erros da CLI devem ser explicativos sem traceback por padrão."""

from comparador import cli


def test_cli_exibe_erro_sem_traceback(monkeypatch, capsys):
    def falha(*args, **kwargs):
        raise ValueError("falha de configuração de teste")

    monkeypatch.setattr(cli, "carregar_configuracao", falha)
    assert cli.executar([]) == 1
    erros = capsys.readouterr().err
    assert "falha de configuração de teste" in erros
    assert "Traceback" not in erros


def test_cli_debug_exibe_traceback_quando_solicitado(monkeypatch, capsys):
    def falha(*args, **kwargs):
        raise ValueError("falha de configuração de teste")

    monkeypatch.setattr(cli, "carregar_configuracao", falha)
    assert cli.executar(["--debug"]) == 1
    erros = capsys.readouterr().err
    assert "Traceback" in erros
    assert "falha de configuração de teste" in erros
