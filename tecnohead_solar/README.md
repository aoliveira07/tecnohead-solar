# TecnoHead Solar

App nativo do Home Assistant OS para monitoramento local de microinversores Deye. A interface usa Ingress e não pede um segundo login.

O PostgreSQL é iniciado e mantido no volume privado `/data/tecnohead_solar`. A API externa é opcional; o funcionamento local, os diagnósticos e o histórico recente não dependem dela.
