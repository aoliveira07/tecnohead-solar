# Administração do banco remoto no Windows

Este procedimento é opcional para clientes que administram o PostgreSQL do módulo TecnoHead Solar com pgAdmin 4 ou DBeaver. O App HAOS se conecta somente à API HTTPS; ele nunca recebe acesso direto ao PostgreSQL remoto.

## Pré-requisitos

- PostgreSQL instalado no servidor do cliente e protegido por firewall.
- Banco, usuário e schema exclusivos para aquela instalação.
- A API Solar instalada no mesmo servidor, com `SOLAR_DATABASE_URL`, `SOLAR_DB_SCHEMA` e `SOLAR_API_TOKEN` definidos no ambiente da API.
- Backup validado antes de qualquer restauração ou migração.

Não reutilize banco, usuário, schema, token ou credenciais de outro cliente. Não abra a porta do PostgreSQL para a Internet; limite o acesso ao processo da API e à rede administrativa.

## pgAdmin 4

1. Abra **Register > Server** e informe o host, a porta e o banco do cliente.
2. Use o usuário dedicado do Solar e marque **Save password** somente em um perfil local protegido.
3. Em **Schemas**, confirme a existência do schema configurado em `SOLAR_DB_SCHEMA`.
4. Verifique as tabelas criadas pela migração `server/migrations/001_initial.sql`.
5. Para inspeção, prefira consultas `SELECT` e o endpoint `/api/v1/solar/health`; não altere tabelas internas do Home Assistant ou de outros projetos.

## DBeaver

1. Crie uma conexão PostgreSQL com o host, porta, banco e usuário dedicados.
2. No editor de conexão, mantenha SSL conforme a política do cliente e desabilite exposição pública desnecessária.
3. Abra o schema Solar e confira índices, tabelas de leituras, alertas e lotes/ACK.
4. Salve a senha no cofre de credenciais do sistema operacional, não em um arquivo do repositório.

## Backup e restauração

No Linux, use os scripts do módulo:

```text
backup.sh
restore.sh arquivo.dump
```

No Windows, o equivalente é um dump customizado do schema dedicado:

```powershell
pg_dump.exe --format=custom --file=solar-backup.dump --schema=solar "$env:SOLAR_DATABASE_URL"
pg_restore.exe --clean --if-exists --schema=solar --dbname="$env:SOLAR_DATABASE_URL" solar-backup.dump
```

Faça a restauração somente em janela de manutenção, com a API parada e uma cópia adicional do estado atual. Depois, execute o healthcheck, confira o total de registros e valide a deduplicação de um lote já confirmado. Nunca use `--clean` em um banco compartilhado sem revisar o alvo exato.

## Diagnóstico seguro

- `401`: token da API ausente, incorreto ou diferente do token configurado no App.
- `404`: rota ou prefixo da API incorreto.
- `5xx`: consulte os logs da API e o estado do PostgreSQL; não exponha tokens no chamado.
- Sem leituras novas: verifique primeiro os loggers e o worker local; a API não é o caminho de coleta.

Consulte [API](API.md), [instalação do servidor](INSTALL_SERVER.md) e [operação e diagnóstico](OPERACAO_E_DIAGNOSTICO.md) para o fluxo completo.
