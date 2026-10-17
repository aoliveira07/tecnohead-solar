# Capturas reais sanitizadas

As imagens abaixo foram capturadas da instalação real no Home Assistant OS em 17/10/2026, após a atualização para 0.1.13. IPs, seriais de logger/inversor, coordenadas, identificador do host, endpoint privado e payload JSON foram cobertos; os estados, contagens e medições de operação continuam sendo evidência real.

| Tela | Evidência |
|---|---|
| Instalação no Supervisor | ![Instalação real no Supervisor](installation-0.1.13.png) |
| Modal de atualização | ![Atualização real do App](installation-update-0.1.13.png) |
| Visão geral | ![Visão geral real](overview-0.1.13.png) |
| Microinversores | ![Cinco coletores reais](collectors-0.1.13.png) |
| Esquema técnico das placas | ![Esquema real das 19 entradas habilitadas](map-0.1.13.png) |
| Diagnósticos e alertas | ![Diagnóstico real sanitizado](diagnostics-0.1.13.png) |
| Histórico e relatórios | ![Histórico real](history-0.1.13.png) |
| Configurações | ![Configurações reais sanitizadas](settings-0.1.13.png) |

Os arquivos-fonte das capturas permanecem fora do repositório. O script [`scripts/sanitize_screenshots.py`](../../scripts/sanitize_screenshots.py) reproduz a camada de sanitização a partir dos arquivos temporários locais sem inserir credenciais ou dados residenciais no GitHub.
