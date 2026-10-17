# Primeiro acesso e configuração

1. Abra o App pelo menu lateral do Home Assistant.
2. Informe a instalação e o fuso; latitude/longitude habilitam o potencial teórico de céu limpo.
3. Cadastre cada logger com IP, serial e, quando disponível, serial do inversor.
4. Para cada coletor, confirme PV1–PV4, nome e local físico. Desabilite uma entrada somente com evidência de que ela não está ocupada.
5. Salve e execute **Diagnósticos e alertas → Executar agora**.
6. Confira o histórico local, o timestamp e a origem `local_deye`.
7. Configure MQTT Discovery se desejado.
8. Configure a API somente depois de validar a coleta local. O token nunca é exibido pela UI.

O forecast da tela é uma estimativa geométrica local de céu limpo. Ele não é previsão meteorológica.

