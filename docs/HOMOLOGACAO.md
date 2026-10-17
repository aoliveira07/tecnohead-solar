# Checklist de homologação

Este arquivo é um registro operacional. Cada item deve conter data, versão, ambiente e evidência; estados permitidos: `Aprovado`, `Falhou`, `Bloqueado` ou `Não executado`.

| Área | Critério | Estado inicial |
|---|---|---|
| Publicação | Repositório, tag e imagem multiarch acessíveis | Não executado |
| HAOS | App instalado, iniciado, Ingress e menu lateral | Não executado |
| Deye | Cinco loggers respondem em TCP 8899 somente leitura | Não executado |
| Medições | AC, tensão/corrente DC e energia por entrada conferidas | Não executado |
| Persistência | PostgreSQL privado, restart e retenção de sete dias | Não executado |
| Pendências | API fora, fila preservada além da retenção e ACK após retorno | Não executado |
| MQTT | Discovery, disponibilidade e IDs estáveis | Não executado |
| Diagnósticos | Falha de logger e baixa produção sem falso positivo | Não executado |
| Relatórios | CSV/PDF com fonte, período e qualidade | Não executado |
| Servidor | Backup, schema isolado, API autenticada e restart | Não executado |
| Interface | Capturas reais sanitizadas de todas as telas | Não executado |

Não promover o App para `stable` nem declarar homologação enquanto existir item sem evidência real.

