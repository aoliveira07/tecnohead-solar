# Instalação da API e PostgreSQL opcional

O módulo é por cliente e pode usar um banco dedicado ou um schema isolado em um banco administrado. Não há endereço residencial, credencial ou dependência fixa no instalador.

## Instalação padrão

No servidor do cliente, com uma conta de serviço:

```bash
export SOLAR_DATABASE_URL='postgresql://usuario:senha@127.0.0.1:5432/banco_do_cliente'
export SOLAR_API_TOKEN="$(openssl rand -hex 32)"
export SOLAR_DB_SCHEMA=solar
export SOLAR_BIND_HOST=127.0.0.1
export SOLAR_PORT=18081
bash server/install.sh --check-only
bash server/install.sh
```

O instalador cria um virtualenv, copia apenas o módulo, grava `server.env` com permissão 0600 e instala um serviço `systemd --user`. Ele cria somente o schema configurado. Para acesso por outra máquina, use o proxy reverso e TLS administrados pelo cliente ou defina explicitamente `SOLAR_BIND_HOST=0.0.0.0` junto com firewall apropriado.

## Banco dedicado

Quando o administrador puder criar role e database, crie um usuário exclusivo, restrinja-o ao banco do cliente e use a URL desse banco. O instalador não executa comandos de criação de role/database para não modificar outros projetos.

## Banco compartilhado com schema isolado

Quando não houver `CREATEDB`/`CREATEROLE`, o usuário pode receber apenas `CREATE` no banco e schema próprio. Confirme o backup, use `SOLAR_DB_SCHEMA=solar` e verifique que as tabelas criadas estão somente nesse schema.

## Backup, atualização e restauração

```bash
export SOLAR_DATABASE_URL='...'
export SOLAR_DB_SCHEMA=solar
bash server/backup.sh
bash server/upgrade.sh
export SOLAR_BACKUP_FILE=/caminho/backup.dump
export SOLAR_ALLOW_RESTORE=YES
bash server/restore.sh
bash server/check.sh
```

`restore.sh` é deliberadamente bloqueado sem a variável explícita. A operação de restore afeta somente o schema indicado.

## Persistência após reboot

O serviço de usuário precisa de sessão persistente. Em uma instalação Linux administrada, habilite linger para a conta de serviço ou instale a unidade system-wide equivalente com autorização do administrador. Sem isso, o processo pode funcionar durante uma sessão ativa e não iniciar após reboot.

