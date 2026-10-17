# TecnoHead Solar

Aplicativo nativo para Home Assistant OS que monitora microinversores Deye pela rede local, grava medições em PostgreSQL privado do próprio App e oferece uma interface TecnoHead responsiva via Ingress.

O produto funciona sem HACS, sem nuvem Deye/Solarman e sem alterar o Recorder do Home Assistant. A API externa e o PostgreSQL remoto são opcionais: quando configurados, ampliam o histórico e recebem lotes idempotentes; quando indisponíveis, a coleta local continua e a fila pendente é preservada.

> **Estado:** `experimental`. A versão só poderá ser promovida a `stable` após a homologação física documentada em [`docs/HOMOLOGACAO.md`](docs/HOMOLOGACAO.md).

## Instalação rápida

1. No Home Assistant, abra **Configurações → Apps → Instalar app → Repositórios**.
2. Adicione `https://github.com/aoliveira07/tecnohead-solar`.
3. Instale **TecnoHead Solar**, inicie o App e habilite **Mostrar na barra lateral**.
4. Abra o Ingress e conclua o assistente. Cadastre somente os loggers e entradas efetivamente presentes; uma entrada sem leitura não é convertida em zero silenciosamente.

[![Adicionar o repositório ao Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Faoliveira07%2Ftecnohead-solar)

## O que o App entrega

- Driver local Deye/Solarman V5 em TCP 8899, somente leitura, com timeout, reconexão e diagnóstico por coletor.
- Visão geral, microinversores, detalhe PV1–PV4, esquema de placas, diagnósticos, histórico, CSV/PDF e configurações.
- PostgreSQL privado do App em `/data`, migrações idempotentes, retenção normal de sete dias e outbox durável para pendências antigas.
- Previsão teórica offline de céu limpo, explicitamente separada de uma previsão meteorológica.
- MQTT Discovery opcional com IDs estáveis, disponibilidade e sensores de energia.
- Alertas de baixo desempenho somente com leituras válidas e janela configurável; nenhuma notificação é criada para API offline.
- Módulo opcional `server/` para API e banco isolados por cliente.

## Documentação

- [`tecnohead_solar/DOCS.md`](tecnohead_solar/DOCS.md) — opções e operação do App.
- [`docs/MANUAL_IMPLANTACAO_CLIENTE.md`](docs/MANUAL_IMPLANTACAO_CLIENTE.md) — implantação reproduzível.
- [`docs/INSTALL_HAOS.md`](docs/INSTALL_HAOS.md) — HAOS, Ingress, backup e atualização.
- [`docs/INSTALL_SERVER.md`](docs/INSTALL_SERVER.md) — API/PostgreSQL opcional em servidor próprio.
- [`docs/ADMIN_POSTGRES_WINDOWS.md`](docs/ADMIN_POSTGRES_WINDOWS.md) — administração do banco com pgAdmin/DBeaver.
- [`docs/OPERACAO_E_DIAGNOSTICO.md`](docs/OPERACAO_E_DIAGNOSTICO.md) — testes, falhas e evidências.
- [`docs/HOMOLOGACAO.md`](docs/HOMOLOGACAO.md) — checklist executado, bloqueado ou não realizado.
- [`docs/screenshots/README.md`](docs/screenshots/README.md) — galeria sanitizada de capturas reais.

## Referências técnicas auditadas

- [Home Assistant Apps](https://contributors.home-assistant.io/apps/), incluindo [Ingress](https://contributors.home-assistant.io/apps/guides/ingress/), [imagem](https://contributors.home-assistant.io/apps/guides/dockerfile/), [S6](https://contributors.home-assistant.io/apps/guides/s6-overlay/) e [configuração](https://contributors.home-assistant.io/apps/reference/configuration/).
- [pysolarmanv5](https://github.com/jmccrohan/pysolarmanv5) — MIT, usado como dependência fixada para o enquadramento Solarman V5.
- [deye-inverter-mqtt](https://github.com/kbialek/deye-inverter-mqtt) — Apache-2.0, consultado para compatibilidade e documentação do perfil micro.
- [home_assistant_solarman](https://github.com/StephanJoubert/home_assistant_solarman) — consultado como referência de compatibilidade.
- [pvlib](https://github.com/pvlib/pvlib-python) — consultado para modelos solares; o cálculo offline deste App é independente e não promete previsão meteorológica.

## Privacidade e segurança

IPs, seriais, tokens, senhas, dumps e capturas privadas não são defaults nem fazem parte do histórico público. As capturas publicadas devem ser sanitizadas. O App não abre a porta do PostgreSQL para a LAN e o módulo remoto nunca é um banco multi-cliente.
