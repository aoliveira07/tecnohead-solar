# Manual de implantação para novos clientes

## 1. Levantamento

Registre modelo do HAOS, versão do Supervisor, broker MQTT, rede dos loggers, localização/fuso, potência nominal de cada placa e o mapeamento físico PV1–PV4. Identifique entradas ausentes por inspeção e por leituras repetidas; não transforme ausência em zero.

## 2. Preparação

Faça backup do HAOS. No servidor opcional, confirme capacidade, PostgreSQL, método de backup, conta de serviço e se haverá banco dedicado ou schema exclusivo. Defina um token aleatório e mantenha-o fora do GitHub.

## 3. App HAOS

Adicione o repositório, instale a tag aprovada, inicie o App e abra o Ingress. Configure nome da instalação, fuso, latitude/longitude, cinco ou a quantidade real de coletores e até quatro PV por coletor.

## 4. Deye

Teste cada logger em TCP 8899 antes de cadastrar. A primeira leitura usa apenas holding registers. Compare tensão, corrente, potência AC/DC e energia do equipamento. Só depois de repetição e confirmação física habilite ou desabilite uma entrada PV.

## 5. MQTT

Instale/configure o broker pelo Supervisor. Habilite Discovery no App, teste a publicação e confira entidades com IDs estáveis. MQTT não substitui o PostgreSQL local.

## 6. API opcional

Faça backup, instale o módulo com `server/install.sh`, confira `/api/v1/solar/health` com Bearer token e configure no App. Simule API indisponível; a coleta deve continuar e a fila deve aumentar. Restaure a conexão e confirme ACK/baixa da fila.

## 7. Homologação

Execute o checklist em [`HOMOLOGACAO.md`](HOMOLOGACAO.md), anexe evidência sanitizada de cada teste e só então promova o estágio de `experimental` para `stable`.

