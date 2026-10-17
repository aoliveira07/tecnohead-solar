# Arquitetura TecnoHead Solar

## Princípios

- O App é nativo do Home Assistant OS e é instalado pelo Supervisor; não usa HACS.
- A coleta Deye é local, somente leitura, em Solarman V5/TCP. Nenhum registrador de escrita, firmware, reset ou downgrade faz parte do driver.
- O PostgreSQL do App é privado dentro do container e persistido em `/data/tecnohead_solar`. O Recorder do Home Assistant não é alterado.
- A API remota é opcional. O App continua local sem ela; quando ativada, a fila `sync_outbox` mantém leituras até ACK idempotente.
- MQTT Discovery é uma saída complementar para entidades do Home Assistant; não é o caminho primário de coleta.

## Fluxo de dados

```text
Deye logger TCP:8899
        │ leitura holding-registers 60..119
        ▼
driver local → validação/alertas → PostgreSQL privado → UI Ingress
                                      │
                                      ├─ MQTT Discovery opcional
                                      └─ outbox → API do cliente (ACK)
```

As leituras confirmadas podem ser removidas após a retenção configurada. Registros ainda pendentes de ACK não são removidos pelo job de retenção, mesmo quando são mais antigos que sete dias.

## Segurança e privacidade

IPs, seriais, tokens, senhas e capturas de uma residência ficam em configuração local e não são defaults públicos. O módulo servidor não é multi-tenant: cada cliente usa seu próprio banco/schema e seu próprio token.

