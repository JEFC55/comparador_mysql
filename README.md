# Comparador de estruturas MySQL (local × SSH)

Compara **a estrutura** de todas as tabelas físicas do schema `dev_infinity` em dois servidores MySQL 8: um na máquina local e outro via túnel SSH (`Standard TCP/IP over SSH`, como no MySQL Workbench). Não modifica o banco de dados nem lê registros de negócio.

## Organização

```text
comparador_mysql/
├── executar.py                      # Entrada do programa
├── config.py                        # Valores padrão + sobreposição opcional do .env
├── .env.example                     # Exemplo de credenciais (não versionar .env)
├── requirements.txt
├── comparador/
│   ├── cli.py                       # Orquestração e parâmetros
│   ├── dto/
│   │   ├── configuracao.py          # DTOs documentados, validação e defaults
│   │   ├── estrutura.py             # ColunaDTO, TabelaDTO, EstruturaBancoDTO
│   │   └── diferenca.py             # DiferencaDTO
│   ├── infraestrutura/
│   │   ├── conexoes.py              # MySQL local + túnel SSH automático
│   │   └── metadados.py             # Queries ao information_schema
│   ├── servicos/
│   │   └── comparacao.py            # Comparação pura, sem acesso externo
│   └── apresentacao/
│       └── relatorios.py            # Terminal + CSV
└── tests/
    ├── test_comparacao.py
    └── test_config.py
```

## Instalação (Windows / PowerShell)

Na sua virtualenv já ativa:

```powershell
cd C:\infinity\agencia\tests\comparador_mysql
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

> É uma sugestão de pasta. Você pode extrair o projeto em outro diretório, sem depender do Django.

## Configuração por objetos

No **`config.py`**, modifique `CONFIG_PADRAO` conforme seus servidores:

```python
CONFIG_PADRAO = ComparacaoConfigDTO(
    local=MySQLConfigDTO(host="127.0.0.1", port=3306, user="root", schema="dev_infinity"),
    remoto=MySQLConfigDTO(host="127.0.0.1", port=3306, user="root", schema="dev_infinity"),
    ssh=SSHConfigDTO(host="IP_DO_SSH", port=22, user="USUARIO_SSH"),
)
```

**Observação:** a instância real em `config.py` também declara `saida_csv`, e cada atributo tem explicações no próprio código, em `dto/configuracao.py`.

Os DTOs incluem defaults seguros para host local, portas, timeout, schema e localização automática da chave SSH. Você pode usar **somente `config.py`** para ajustar host/usuários (e informar senhas interativamente) **ou** colocar as configurações no `.env`. Variáveis do sistema têm prioridade sobre `.env`, que tem prioridade sobre os defaults do código.

Se usar `.env`, **obrigatório preencher** ao menos `SSH_HOST` e `SSH_USER` (ou preenchê-los no `config.py`). As senhas MySQL em branco são solicitadas pelo prompt. Chave SSH nunca vai em `REMOTE_MYSQL_PASSWORD`.

### Chave SSH no Windows

Prefira a variável do `.env` com barras normais:

```dotenv
SSH_KEY_PATH=C:/Users/SEU_USUARIO/.ssh/id_ed25519
```

Ou mantenha `SSH_KEY_PATH=` vazio para detectar `~/.ssh/id_ed25519` automaticamente (se existir). Nunca escreva a chave em `password=`. **Não** use `"\Users\User\.ssh\id_ed25519"` em código Python: `\U` causa erro de escape Unicode.

Se usa autenticação por senha em vez de chave, deixe `SSH_KEY_PATH=` vazio e configure `SSH_PASSWORD` no `.env` (ou uma senha no DTO fora de um repositório versionado).

### Sobre host, porta e autenticação

- **LOCAL_MYSQL_HOST/PORT**: `127.0.0.1:3306` na sua máquina.
- **SSH_HOST/PORT**: IP/domínio do servidor SSH, normalmente porta `22`.
- **REMOTE_MYSQL_HOST/PORT**: onde o MySQL responde **a partir do servidor SSH** (`127.0.0.1:3306` se está no mesmo servidor). Não use `3307` aqui quando o programa cria o túnel automaticamente.
- **SSH_USER** é o login do servidor; **REMOTE_MYSQL_USER** é o login no banco.
- **SSH_HOST_KEY**: verificação explícita da identidade da máquina SSH; recomenda-se configurá-la para proteger contra MITM. Com valor ausente, a biblioteca `sshtunnel` não assegura essa verificação.

## Executar

Comparação completa:

```powershell
python executar.py
```

Uma tabela específica:

```powershell
python executar.py --tabela tb_ordem_servico
```

Arquivo CSV específico (UTF-8 com BOM, separado por ponto e vírgula):

```powershell
python executar.py --tabela tb_produto --saida saida/colunas_produto.csv
```

Arquivo `.env` fora da pasta padrão:

```powershell
python executar.py --env C:/infinity/config/compare.env
```

Ajuda:

```powershell
python executar.py --help
```

## O que é comparado

- Tabelas que existem só no MySQL local ou só no remoto;
- Colunas ausentes em um dos ambientes;
- Tipos, `NULL`, `DEFAULT`, `EXTRA`, `COLUMN_KEY`, charset, collation, expressão gerada, comentário e posição da coluna.

**Limites:** não compara os dados armazenados, índices em detalhe, constraints completas, `FOREIGN KEY`, triggers, views, procedures ou migrations do Django. O campo `COLUMN_KEY` é apenas um indicador simplificado de indexação.

O programa recria o CSV mesmo que não haja diferenças, evitando consultar por engano o resultado de uma execução anterior.

## Testes

```powershell
python -m pip install pytest
python -m pytest -q
```

Testes unitários não exigem conexão ativa ao banco de dados. O script foi projetado para consulta somente-leitura (`information_schema`).
