# Limitações conhecidas

- O driver implementa o perfil de holding registers validado para microinversores Deye/Solarman V5. Modelos com mapa diferente devem permanecer experimentais até nova evidência.
- O forecast embutido é geometria solar de céu limpo, não previsão de nuvens, chuva ou temperatura.
- `systemd --user` sem linger não garante inicialização após reboot; a política do servidor deve resolver isso.
- O App não cria automaticamente role/database/proxy reverso no servidor remoto; essa separação exige privilégio e decisão do administrador.
- O estágio deve permanecer `experimental` até que testes físicos, persistência, API offline/retorno, MQTT, backup/restore e telas tenham evidência anexada.

