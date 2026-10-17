# Módulo opcional de API e PostgreSQL

Este diretório contém um servidor por cliente. Ele não é SaaS multi-tenant e não contém endereço, serial, token ou senha da residência TecnoHead.

O instalador usa `SOLAR_DATABASE_URL`, `SOLAR_API_TOKEN`, `SOLAR_DB_SCHEMA`, `SOLAR_BIND_HOST` e `SOLAR_PORT`. Por padrão, a aplicação cria somente o schema configurado e não cria usuários, bancos, regras de firewall ou proxy reverso. Isso permite uso seguro em um banco já administrado pelo cliente quando a conta não tem `CREATEDB`/`CREATEROLE`; para uma instalação dedicada, forneça um banco e usuário exclusivos.

Antes de rodar migrações em um servidor existente, faça um backup e confirme o schema. `backup.sh` exporta somente o schema TecnoHead selecionado. `restore.sh` exige `SOLAR_ALLOW_RESTORE=YES`.

O serviço de exemplo é `systemd --user`. Em produção, habilite linger ou use uma unidade system-wide administrada pelo cliente quando a política operacional exigir disponibilidade após logout/reboot.

