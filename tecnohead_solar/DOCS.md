# Documentação do App

## Instalação

Adicione o repositório público à loja de Apps, instale TecnoHead Solar, inicie-o e abra **Open Web UI**. Em seguida habilite **Mostrar na barra lateral**. A autenticação é a sessão do Home Assistant via Ingress.

## Primeiro acesso

O assistente cria a instalação, os coletores e as entradas PV. Para cada coletor informe IP, `logger_serial` e, se disponível, `inverter_serial` separadamente. O App usa TCP 8899/Solarman V5 no perfil `deye_micro_v1` e só executa funções de leitura. Uma entrada sem placa deve ser desabilitada após confirmação por leitura repetida e identificação física.

## PostgreSQL local

O cluster é exclusivo do App e fica em `/data/tecnohead_solar/postgres`. O Recorder do Home Assistant não é alterado. Leituras confirmadas respeitam a retenção normal configurada; leituras pendentes da API continuam na fila mesmo quando ultrapassam esse período. O backup do App é `cold`, para que a cópia do cluster seja consistente.

## API externa

Ative-a somente para um endpoint do servidor do próprio cliente. O App envia lotes autenticados e idempotentes; não abre conexão direta ao PostgreSQL remoto. `Online`, `Offline`, `Sincronizando` e `Desabilitada` são estados de operação, não notificações. Tokens não são exibidos pela interface nem escritos no log.

## MQTT

Quando o broker estiver disponível, o App publica Discovery com IDs derivados da instalação, logger e canal lógico. Energia usa `kWh`, `state_class: total_increasing` e disponibilidade do coletor. MQTT é complemento: a coleta e o dashboard próprio continuam funcionando sem ele.

## Limitações honestas

- O perfil de registradores é o `deye_micro_v1`; outros modelos podem exigir um perfil cadastrado e validado.
- Métrica não exposta pelo firmware é marcada como não suportada, nunca como zero.
- A previsão offline é potencial teórico de céu limpo. Ela não é previsão meteorológica sem fonte de clima.
- A entrada física sem placa precisa ser confirmada pelo técnico; o App não inventa a posição de painéis.
