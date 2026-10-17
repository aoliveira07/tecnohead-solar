# Instalação no Home Assistant OS

## Pré-requisitos

1. Home Assistant OS com Supervisor/Apps habilitados.
2. Backup do Home Assistant confirmado antes de adicionar ou atualizar o App.
3. Rota IP entre o HAOS e cada logger Deye em TCP 8899.
4. MQTT opcional instalado e funcionando quando Discovery for desejado.

## Instalação

1. Abra **Configurações → Apps → Instalar app → Repositórios**.
2. Adicione o endereço do repositório publicado no README.
3. Escolha **TecnoHead Solar**, confirme a versão publicada e instale.
4. Inicie o App e habilite **Mostrar na barra lateral**.
5. Abra o Ingress e conclua o assistente. Use endereço e serial reais do cliente; não use placeholders.

O App usa `ingress: true`, porta interna 8099 e URLs relativas. A imagem multiarch é publicada no GHCR com tag imutável por versão. A configuração segue a referência oficial de Apps do Home Assistant: [Apps](https://developers.home-assistant.io/docs/add-ons), [Ingress](https://developers.home-assistant.io/docs/add-ons/communication), [Dockerfile](https://developers.home-assistant.io/docs/add-ons/configuration), [S6](https://developers.home-assistant.io/docs/add-ons/configuration#startup).

## Atualização e rollback

Faça um backup antes de atualizar. Instale a nova tag pelo Supervisor, reinicie o App e execute o diagnóstico. Para rollback, selecione uma versão anterior publicada e preserve o volume `/data`.

## Verificações pós-instalação

- O menu lateral identifica **TecnoHead Solar**.
- `/health` responde internamente e o Ingress abre a interface.
- O primeiro diagnóstico de cada logger é somente leitura.
- O PostgreSQL não está exposto para a LAN.
- A configuração mostra API, MQTT, retenção e estado da fila sem revelar segredos.

