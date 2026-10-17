# Operação e diagnóstico

## Coletor offline

Confirme alimentação, IP, rota e TCP 8899. Execute o diagnóstico somente leitura. Um erro no logger não deve apagar leituras locais nem gerar alerta de API.

## PV sem corrente

Compare tensão/corrente entre amostras e confira o local físico. Entrada ociosa, noturna ou desocupada pode ser válida; o alerta de baixa produção exige leitura suportada e evita o par quase-zero.

## API offline

O App deve continuar coletando no PostgreSQL privado. A fila `sync_outbox` preserva IDs e tenta novamente com backoff. A retenção não exclui registros pendentes de ACK. A indisponibilidade da API não gera alerta solar.

## MQTT

Verifique broker, porta, credencial e publicação `homeassistant/sensor/.../config`. Se o broker estiver fora, a coleta Deye e o histórico local continuam.

## PostgreSQL local

O App mantém o PostgreSQL dentro do container, sem porta LAN. Em diagnóstico, confirme migração, tamanho do banco, última leitura, fila e status de cada coletor. O backup do App deve ser realizado pelo mecanismo de backup do Home Assistant.

## Relatórios

CSV e PDF informam período, fonte e qualidade. Antes de compartilhar, remova IP, serial, localização e tokens de qualquer captura ou exportação.

