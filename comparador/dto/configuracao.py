"""DTOs de configuração.

Os valores padrão pertencem aos DTOs. Todos os campos podem ser ajustados
no arquivo config.py; as variáveis de ambiente opcionais têm precedência.
Senhas e passphrases devem ser informadas via .env ou prompt, nunca versionadas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True, kw_only=True)
class MySQLConfigDTO:
    """Conexão de um servidor MySQL (local ou alcançado pelo túnel).

    host: endereço visto a partir do cliente. No remoto, é visto pelo SSH.
    port: porta TCP do MySQL, normalmente 3306.
    user: usuário do MySQL (não confundir com usuário SSH).
    password: senha do MySQL; None significa solicitar no terminal.
    schema: banco que será comparado (padrão: dev_infinity).
    connection_timeout: tempo máximo de conexão em segundos.
    """

    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str | None = field(default=None, repr=False)
    schema: str = "dev_infinity"
    connection_timeout: int = 15

    def validar(self, origem: str) -> None:
        if not self.host.strip() or not self.user.strip() or not self.schema.strip():
            raise ValueError(f"Host, usuário e schema MySQL são obrigatórios ({origem}).")
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Porta MySQL inválida na conexão {origem}: {self.port}.")
        if self.connection_timeout < 1:
            raise ValueError("connection_timeout deve ser maior que zero.")


@dataclass(frozen=True, slots=True, kw_only=True)
class SSHConfigDTO:
    """Configuração do túnel SSH usado somente para o MySQL remoto.

    host: IP ou DNS do servidor SSH; obrigatório.
    port: porta SSH, normalmente 22.
    user: login no SSH (pode diferir do usuário MySQL).
    password: senha SSH; opcional se usar chave privada ou ssh-agent.
    key_path: caminho da chave privada, como ~/.ssh/id_ed25519.
              None procura automaticamente ~/.ssh/id_ed25519; sem chave,
              a biblioteca pode usar o agente SSH ou senha configurada.
    key_passphrase: frase secreta da chave privada, NÃO é senha do MySQL.
    host_key: chave pública SSH esperada no formato da biblioteca sshtunnel;
              defina-a para fixar a identidade do host (recomendado).
    """

    host: str = ""
    port: int = 22
    user: str = ""
    password: str | None = field(default=None, repr=False)
    key_path: Path | None = None
    key_passphrase: str | None = field(default=None, repr=False)
    host_key: str | None = None

    def validar(self) -> None:
        if not self.host.strip() or not self.user.strip():
            raise ValueError("Configure SSH_HOST e SSH_USER no .env ou em config.py.")
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Porta SSH inválida: {self.port}.")
        if self.key_path is not None and not self.key_path.expanduser().is_file():
            raise ValueError(f"Chave SSH não encontrada: {self.key_path}")

    def chave_privada(self) -> Path | None:
        """Usa a chave indicada ou ~/.ssh/id_ed25519, caso exista."""
        if self.key_path is not None:
            return self.key_path.expanduser()
        padrao = Path.home() / ".ssh" / "id_ed25519"
        return padrao if padrao.is_file() else None


@dataclass(frozen=True, slots=True, kw_only=True)
class ComparacaoConfigDTO:
    """Configuração principal e padrões globais do comparador.

    local: MySQL da máquina em que o script é executado.
    remoto: MySQL visto de dentro do servidor SSH; não use a porta local
            3307 aqui se o túnel for criado automaticamente.
    ssh: credenciais SSH do servidor que dá acesso ao banco remoto.
    saida_csv: arquivo de saída. O CSV é recriado mesmo sem diferenças,
               evitando confundir relatórios antigos com o resultado atual.
    """

    local: MySQLConfigDTO = field(default_factory=MySQLConfigDTO)
    remoto: MySQLConfigDTO = field(default_factory=MySQLConfigDTO)
    ssh: SSHConfigDTO = field(default_factory=SSHConfigDTO)
    saida_csv: Path = Path("diferencas_dev_infinity.csv")

    def validar(self) -> None:
        self.local.validar("local")
        self.remoto.validar("remota")
        self.ssh.validar()
