# API opcional

Base sugerida: `http://servidor-do-cliente:18081` ou o endereço HTTPS publicado pelo cliente.

Todos os endpoints usam `Authorization: Bearer <token>`.

- `GET /api/v1/solar/health` — saúde e contagem resumida.
- `POST /api/v1/solar/readings/batch` — lote idempotente enviado pelo App; retorna `acknowledged_reading_ids`.
- `GET /api/v1/solar/history?since_hours=24&limit=500` — histórico remoto.
- `GET /api/v1/solar/summary` — contagem e última leitura.
- `GET /api/v1/solar/alerts` — alertas persistidos no schema do cliente.

O App só considera uma leitura sincronizada depois de receber ACK contendo o ID. Reenvio do mesmo lote não duplica a chave primária. Em erro HTTP, timeout ou JSON inválido, os registros continuam pendentes.

