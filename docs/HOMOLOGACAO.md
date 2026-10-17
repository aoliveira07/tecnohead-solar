# Homologação operacional — TecnoHead Solar

Registro executado em 17/10/2026 no Home Assistant OS real, com a versão 0.1.13. Os estados usados são `Aprovado`, `Aprovado com ressalva`, `Bloqueado` e `Não executado`. Valores privados (endereços, seriais, coordenadas e token) foram omitidos deste documento e cobertos nas capturas públicas.

| Área | Critério | Estado | Evidência executada |
|---|---|---|---|
| Publicação | Repositório, tag, release e imagem multiarch | Aprovado | Repositório público, tag `0.1.13`, release e workflow de imagem concluído no GitHub. |
| HAOS | App instalado, iniciado, Ingress e menu lateral | Aprovado | Supervisor mostrou 0.1.13 instalada/em funcionamento; Ingress abriu e **TecnoHead Solar** ficou visível na barra lateral. |
| Deye | Cinco loggers respondem em TCP 8899 somente leitura | Aprovado | Cinco endpoints responderam; foram feitas duas rodadas de `read_holding_registers(60, 60)` por Solarman V5. Nenhum registrador de escrita foi chamado. |
| Medições | AC, tensão/corrente DC e energia por entrada | Aprovado com ressalva | Leituras físicas e telas confirmaram AC/PV/energia nos cinco coletores; 19 entradas estão habilitadas. PV4 do Deye 03 foi desabilitado por tensão observada de aproximadamente 0,1 V; PV1 do mesmo coletor permanece habilitado para acompanhamento, sem converter ausência em zero silencioso. |
| Persistência | PostgreSQL privado e recuperação após atualização/restart | Aprovado | O banco privado do App reiniciou junto com a atualização e as leituras/histórico permaneceram disponíveis; status, setup e leituras responderam 200 após o retorno. |
| Retenção e pendências | Sete dias e preservação de registros aguardando ACK | Não executado | O código e o schema implementam retenção com proteção da outbox, mas a residência não tinha registros pendentes nem janela vencida para executar uma prova destrutiva/temporal sem fabricar dados operacionais. |
| MQTT | Discovery, disponibilidade e IDs estáveis | Aprovado com ressalva | Supervisor entregou o serviço MQTT; o worker publicou Discovery e o estado persistido ficou `online`. A lista de entidades deve ser conferida pelo administrador após eventual troca de broker. |
| Diagnósticos | Leitura real e persistência da última execução | Aprovado | O botão executou as cinco leituras reais; a versão 0.1.12 revelou erro de serialização e retornou 500, corrigido em 0.1.13. Após atualização, a execução retornou 200 e a evidência persistiu no PostgreSQL. |
| Relatórios | CSV/PDF com fonte, período e qualidade | Aprovado com ressalva | CSV real foi baixado; os registros do App mostraram 200 no endpoint PDF. O evento de download do PDF não foi capturado pelo navegador usado para a evidência. |
| API/PostgreSQL opcional | Backup, schema isolado, autenticação e restart | Aprovado com ressalva | Backup do banco existente foi concluído antes da implantação; serviço do cliente está ativo, com `schema=solar`, autenticação Bearer, linger e health local 0.1.13. |
| Sincronização externa | HAOS alcança a API opcional pela rede | Bloqueado | A API escuta no servidor e responde localmente, mas a conexão externa à porta configurada expirou (`curl` exit 28/status 000). Não foi alterado Nginx/firewall nem declarado sync E2E. |
| Interface | Capturas reais sanitizadas de instalação, telas e alertas | Aprovado | Galeria versionada com capturas reais sanitizadas: instalação, overview, microinversores, esquema, diagnóstico, histórico, configurações e atualização. |

## Critérios que ficaram fora da aprovação completa

A coleta local, o App HAOS e a API opcional local estão operacionais. A sincronização HAOS → API não está homologada enquanto o administrador da infraestrutura não liberar a rota externa ou um proxy reverso TLS. A prova temporal de retenção/outbox também permanece pendente porque não havia registros pendentes reais e a execução não deveria fabricar ou apagar dados da residência.

## Evidências públicas

- [Galeria de capturas reais sanitizadas](screenshots/README.md)
- [Manual de implantação para novos clientes](MANUAL_IMPLANTACAO_CLIENTE.md)
- [Instalação e atualização no HAOS](INSTALL_HAOS.md)
- [Instalação da API e PostgreSQL opcional](INSTALL_SERVER.md)
- [Operação e diagnóstico](OPERACAO_E_DIAGNOSTICO.md)
