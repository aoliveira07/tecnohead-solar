const state = { route: "overview", status: null, setup: null, readings: [], diagnostics: null };
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[char]));
const number = (value, digits = 1) => value === null || value === undefined ? "—" : Number(value).toLocaleString("pt-BR", { maximumFractionDigits: digits });
const watts = (value) => value === null || value === undefined ? "—" : `${number(value, 0)} W`;
const kwh = (value) => value === null || value === undefined ? "—" : `${number(value, 2)} kWh`;
const dateText = (value) => value ? new Date(value).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "—";

async function api(path, options = {}) {
  const response = await fetch(`api/v1/${path.replace(/^\//, "")}`, { headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
  const text = await response.text();
  let body = {};
  try { body = text ? JSON.parse(text) : {}; } catch { body = { detail: text }; }
  if (!response.ok) throw new Error(body.detail || `HTTP ${response.status}`);
  return body;
}

function toast(message, isError = false) {
  const node = $("#toast");
  node.textContent = message;
  node.className = `toast show ${isError ? "error" : ""}`;
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => { node.textContent = ""; node.className = "toast"; }, 5000);
}

function apiStatus(status) {
  const value = status?.api?.state || "disabled";
  const label = { disabled: "API desabilitada", online: "API online", offline: "API offline", syncing: "Sincronizando" }[value] || value;
  const node = $("#sidebar-api-status");
  node.className = `status-pill ${value}`;
  node.innerHTML = `<i></i>${label}`;
  return `<span class="api-light"><span class="status-dot ${value}"></span><strong>${label}</strong>${status?.api?.pending_records ? ` · ${number(status.api.pending_records, 0)} pendentes` : ""}</span>`;
}

function nav(route) {
  state.route = route;
  $$(".nav-link").forEach((button) => button.classList.toggle("active", button.dataset.route === route));
  $$(".page").forEach((page) => page.classList.toggle("active-page", page.id === `page-${route}`));
  const labels = { overview: ["Visão geral", "Produção real, potencial teórico e saúde da comunicação local."], collectors: ["Microinversores", "Leituras por coletor, idade da comunicação e entradas PV."], map: ["Esquema de placas", "Mapa lógico editável para manutenção, sem foto do telhado."], diagnostics: ["Diagnósticos e alertas", "Evidência técnica, falhas de comunicação e desempenho solar."], history: ["Histórico e relatórios", "Fonte, período e exportação sem duplicar leituras pendentes."], settings: ["Configurações", "Instalação, PV, MQTT, API opcional e retenção local."] };
  $("#page-title").textContent = labels[route][0];
  $("#page-subtitle").textContent = labels[route][1];
  render();
}

function lineChart(rows) {
  const values = rows.filter((row) => row.power_ac_w !== null && row.power_ac_w !== undefined).slice(0, 36).reverse().map((row) => Number(row.power_ac_w) || 0);
  if (!values.length) return `<div class="empty">Ainda não há leituras AC suficientes para o gráfico.</div>`;
  const max = Math.max(1, ...values);
  const points = values.map((value, index) => `${(index / Math.max(1, values.length - 1)) * 100},${100 - (value / max) * 86}`).join(" ");
  const forecast = values.map((_, index) => `${(index / Math.max(1, values.length - 1)) * 100},${100 - Math.max(0, Math.sin(index / 5)) * 72}`).join(" ");
  return `<div class="chart"><div class="chart-grid"></div><div class="chart-line"><svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Potência AC real e referência teórica"><polyline class="forecast" points="${forecast}"></polyline><polyline class="real" points="${points}"></polyline></svg></div><div class="chart-legend"><span>real</span><span class="forecast">potencial teórico</span></div></div>`;
}

function renderOverview() {
  const status = state.status || {};
  const summary = status.summary || {};
  const forecast = status.forecast || {};
  const collectorsList = status.collectors || [];
  const alerts = status.alerts || [];
  $("#page-overview").innerHTML = `
    <div class="grid metrics-grid">
      <article class="card metric-card"><span class="metric-label">Potência AC agora</span><strong class="metric-value">${watts(summary.power_ac_w)}</strong><span class="metric-note">Somente leituras locais válidas</span></article>
      <article class="card metric-card"><span class="metric-label">Energia hoje</span><strong class="metric-value">${kwh(summary.energy_today_kwh)}</strong><span class="metric-note">Soma AC reportada pelos coletores</span></article>
      <article class="card metric-card"><span class="metric-label">Coletores online</span><strong class="metric-value">${collectorsList.filter((item) => item.last_status === "online").length}/${number(summary.collectors, 0)}</strong><span class="metric-note">${summary.latest_at ? `Última ${dateText(summary.latest_at)}` : "Ainda sem leitura"}</span></article>
      <article class="card metric-card"><span class="metric-label">Placas habilitadas</span><strong class="metric-value">${number(summary.enabled_pv, 0)}</strong><span class="metric-note">O App não assume placa ausente como zero</span></article>
    </div>
    <div class="grid two-column" style="margin-top:16px">
      <article class="card"><div class="section-head"><div><span class="section-kicker">PRODUÇÃO</span><h2>Real × potencial teórico</h2><p>O traço dourado é cálculo solar local, não previsão meteorológica.</p></div>${apiStatus(status)}</div>${lineChart(state.readings)}</article>
      <article class="card"><div class="section-head"><div><span class="section-kicker">SAÚDE</span><h2>Resumo da instalação</h2></div></div><div class="list"><div class="list-row"><div><strong>API opcional</strong><small>${status.api?.last_detail || "Estado calculado por requisição normal"}</small></div>${apiStatus(status)}</div><div class="list-row"><div><strong>Potencial teórico</strong><small>${esc(forecast.label || "Configure latitude e longitude")}</small></div><strong>${forecast.watts ? watts(forecast.watts) : "—"}</strong></div><div class="list-row"><div><strong>Alertas ativos</strong><small>Baixo desempenho somente com leitura válida</small></div><strong>${number(alerts.length, 0)}</strong></div><div class="list-row"><div><strong>Fila pendente</strong><small>Preservada até ACK válido da API</small></div><strong>${number(summary.pending_records, 0)}</strong></div></div></article>
    </div>
    <div class="grid two-column" style="margin-top:16px">
      <article class="card"><div class="section-head"><div><span class="section-kicker">COLETA LOCAL</span><h2>Microinversores</h2><p>Visão rápida dos cinco/quantidade cadastrada; a lista é dinâmica.</p></div><button class="secondary-button" data-route="collectors">Abrir lista</button></div><div class="list">${collectorsList.slice(0, 6).map((item) => `<div class="list-row"><div><strong>${esc(item.name)}</strong><small>${esc(item.ip)} · logger ${esc(String(item.logger_serial))}</small></div><span class="badge ${item.last_status === "online" ? "online" : item.last_status === "offline" ? "offline" : ""}">${item.last_status === "online" ? "Online" : item.last_status === "offline" ? "Offline" : "Não testado"}</span></div>`).join("") || `<div class="empty">Conclua o primeiro acesso para cadastrar os coletores.</div>`}</div></article>
      <article class="card"><div class="section-head"><div><span class="section-kicker">PRÓXIMA AÇÃO</span><h2>Homologação</h2><p>Não declare um teste aprovado sem evidência real.</p></div></div><div class="notice">Use <strong>Diagnósticos e alertas</strong> para executar a leitura somente-leitura de cada logger. O resultado grava no PostgreSQL local antes de tentar a API.</div><div class="form-actions"><button class="primary-button" data-route="diagnostics">Executar diagnóstico</button><button class="secondary-button" data-route="history">Ver histórico</button></div></article>
    </div>`;
}

function renderCollectors() {
  const list = state.status?.collectors || [];
  $("#page-collectors").innerHTML = `<div class="section-head"><div><span class="section-kicker">DISPOSITIVOS LOCAIS</span><h2>Leituras por microinversor</h2><p>IP é apenas endereço de transporte; identidade estável usa o logger serial.</p></div><button class="primary-button" id="run-all-probes">Testar todos</button></div><div class="grid collector-grid">${list.map((item) => `<article class="card collector-card"><div class="collector-top"><div class="identity"><span class="collector-icon">☼</span><div><h3>${esc(item.name)}</h3><small class="muted">${esc(item.ip)} · logger ${esc(String(item.logger_serial))}</small></div></div><span class="badge ${item.last_status === "online" ? "online" : item.last_status === "offline" ? "offline" : ""}">${item.last_status === "online" ? "Online" : item.last_status === "offline" ? "Offline" : "Não testado"}</span></div><div class="pv-mini-grid">${[1,2,3,4].map((channel) => { const pv = state.setup?.pv_inputs?.find((entry) => entry.collector_id === item.id && entry.channel === channel); const reading = state.readings.find((entry) => entry.collector_id === item.id && entry.channel === channel); return `<div class="pv-mini ${pv?.enabled === false ? "disabled" : ""}"><strong>PV${channel} ${pv?.enabled === false ? "· desab." : ""}</strong><span>${reading ? watts(reading.power_dc_w) : "—"}</span></div>`; }).join("")}</div><div class="list-row"><div><strong>Última leitura</strong><small>${dateText(item.last_seen_at)} · ${item.last_error ? esc(item.last_error) : "sem erro registrado"}</small></div><button class="secondary-button probe-button" data-id="${item.id}">Testar</button></div></article>`).join("") || `<div class="empty">Nenhum coletor cadastrado. Abra Configurações para iniciar.</div>`}</div>`;
  $("#run-all-probes")?.addEventListener("click", async () => { await runDiagnostics(); });
  $$(".probe-button").forEach((button) => button.addEventListener("click", async () => { button.disabled = true; try { await api(`collectors/${button.dataset.id}/probe`, { method: "POST", body: "{}" }); toast("Leitura real concluída e gravada localmente."); await refresh(); } catch (error) { toast(error.message, true); } finally { button.disabled = false; } }));
}

function renderMap() {
  const items = state.setup?.pv_inputs || [];
  const panelNodes = items.map((item) => `<div class="map-panel ${item.enabled ? "" : "disabled"}" style="left:${Math.max(8, Math.min(92, Number(item.map_x || 20)))}%;top:${Math.max(14, Math.min(90, Number(item.map_y || 30)))}%"><strong>${esc(item.name || `PV${item.channel}`)}</strong><small>${esc(item.collector_name || "Coletor")} · PV${item.channel}</small></div>`).join("");
  $("#page-map").innerHTML = `<div class="section-head"><div><span class="section-kicker">MANUTENÇÃO</span><h2>Mapa esquemático dos painéis</h2><p>Arranjo lógico sem foto. Posições e locais vêm do cadastro técnico.</p></div><button class="primary-button" data-route="settings">Editar posições</button></div><div class="grid two-column"><article class="card"><div class="map-board">${panelNodes || `<div class="empty" style="position:absolute;inset:22% 8% auto">Cadastre as entradas PV para posicioná-las no esquema.</div>`}</div></article><article class="card"><div class="section-head"><div><span class="section-kicker">LEGENDA</span><h2>Entradas cadastradas</h2></div></div><div class="list">${items.map((item) => `<div class="list-row"><div><strong>${esc(item.name)}</strong><small>${esc(item.collector_name || "")}, PV${item.channel} · ${esc(item.physical_location || "local não informado")}</small></div><span class="badge ${item.enabled ? "online" : ""}">${item.enabled ? "Habilitada" : "Desabilitada"}</span></div>`).join("") || `<div class="empty">Sem entradas configuradas.</div>`}</div></article></div>`;
}

async function runDiagnostics() {
  toast("Executando testes somente-leitura nos coletores…");
  try { const result = await api("diagnostics/run", { method: "POST", body: "{}" }); toast(result.ok ? "Diagnóstico concluído: todos responderam." : "Diagnóstico concluído com pelo menos uma falha.", !result.ok); state.diagnostics = result; await refresh(); nav("diagnostics"); } catch (error) { toast(error.message, true); }
}

function renderDiagnostics() {
  const alerts = state.status?.alerts || [];
  const list = state.status?.collectors || [];
  $("#page-diagnostics").innerHTML = `<div class="grid two-column"><article class="card"><div class="section-head"><div><span class="section-kicker">TESTE DE CAMPO</span><h2>Comunicação Deye</h2><p>O teste não escreve registradores, firmware ou configuração.</p></div><button class="primary-button" id="run-diagnostics">Executar agora</button></div><div class="list">${list.map((item) => `<div class="list-row"><div><strong>${esc(item.name)}</strong><small>Serial logger ${esc(String(item.logger_serial))} · ${dateText(item.last_seen_at)}</small></div><span class="badge ${item.last_status === "online" ? "online" : item.last_status === "offline" ? "offline" : ""}">${item.last_status === "online" ? "Leitura confirmada" : item.last_status === "offline" ? esc(item.last_error || "Falha") : "Não executado"}</span></div>`).join("") || `<div class="empty">Nenhum coletor cadastrado.</div>`}</div></article><article class="card"><div class="section-head"><div><span class="section-kicker">ALERTAS SOLARES</span><h2>Casos ativos</h2><p>API offline não gera alerta; falhas de geração são tratadas separadamente.</p></div></div>${alerts.map((alert) => `<div class="alert-row"><span class="alert-severity ${alert.severity}"></span><div><strong>${esc(alert.title)}</strong><p>${esc(alert.detail)}</p><small class="muted">${dateText(alert.opened_at)}</small></div><span class="badge">${esc(alert.severity)}</span></div>`).join("") || `<div class="empty">Nenhum alerta solar ativo.</div>`}</article></div><article class="card" style="margin-top:16px"><div class="section-head"><div><span class="section-kicker">EVIDÊNCIA</span><h2>Último diagnóstico</h2></div></div><pre class="code-block">${esc(JSON.stringify(state.diagnostics || state.diagnosticsPayload || {"mensagem":"Execute o diagnóstico para registrar evidência."}, null, 2))}</pre></article>`;
  $("#run-diagnostics")?.addEventListener("click", runDiagnostics);
}

function renderHistory() {
  $("#page-history").innerHTML = `<div class="section-head"><div><span class="section-kicker">DADOS PERSISTIDOS</span><h2>Histórico e relatórios</h2><p>O período e a fonte devem ser visíveis; registros pendentes continuam locais.</p></div><div class="form-actions"><a class="secondary-button" href="api/v1/reports.csv" download>Baixar CSV</a><a class="primary-button" href="api/v1/reports.pdf" download>Baixar PDF</a></div></div><article class="card"><div class="table-wrap"><table><thead><tr><th>Horário</th><th>Coletor</th><th>Entrada</th><th>AC</th><th>DC</th><th>Energia hoje</th><th>Fonte</th></tr></thead><tbody>${state.readings.slice(0, 120).map((row) => `<tr><td>${dateText(row.captured_at)}</td><td>${esc(row.collector_name || "")}</td><td>${esc(row.pv_name || "AC")}</td><td>${watts(row.power_ac_w)}</td><td>${watts(row.power_dc_w)}</td><td>${kwh(row.energy_today_kwh)}</td><td>${esc(row.source || "local")}</td></tr>`).join("") || `<tr><td colspan="7"><div class="empty">Nenhuma leitura no período local.</div></td></tr>`}</tbody></table></div></article>`;
}

function blankCollector(index) {
  return { name: `Microinversor ${index + 1}`, ip: "", logger_serial: "", inverter_serial: "", enabled: true, pv_inputs: [1,2,3,4].map((channel) => ({ channel, name: `PV${channel}`, enabled: true, physical_location: "", wp: "", map_x: 15 + ((index * 4 + channel) % 8) * 10, map_y: 30 + Math.floor(index / 2) * 18 })) };
}

function renderSetupEditor() {
  const existing = state.setup?.collectors || [];
  const configured = existing.length ? existing.map((item) => ({ ...item, pv_inputs: state.setup.pv_inputs.filter((pv) => pv.collector_id === item.id) })) : [0,1,2,3,4].map(blankCollector);
  return configured.map((item, index) => `<div class="setup-collector" ${item.id ? `data-id="${esc(item.id)}"` : ""} data-collector-index="${index}"><div class="section-head"><div><span class="section-kicker">COLETOR ${index + 1}</span><h3>${esc(item.name || `Microinversor ${index + 1}`)}</h3></div><label class="toggle"><input type="checkbox" data-field="enabled" ${item.enabled !== false ? "checked" : ""}> Coletor ativo</label></div><div class="form-grid three"><div class="field"><label>Nome técnico</label><input data-field="name" value="${esc(item.name || `Microinversor ${index + 1}`)}" placeholder="Ex.: Fileira leste"></div><div class="field"><label>IP do logger</label><input data-field="ip" value="${esc(item.ip || "")}" placeholder="192.0.2.10"></div><div class="field"><label>Logger serial</label><input data-field="logger_serial" value="${esc(item.logger_serial || "")}" inputmode="numeric" placeholder="Número do logger"></div><div class="field"><label>Inversor serial (opcional)</label><input data-field="inverter_serial" value="${esc(item.inverter_serial || "")}" placeholder="Separado do logger"></div></div><div class="setup-pv-grid">${[1,2,3,4].map((channel) => { const pv = item.pv_inputs?.find((entry) => Number(entry.channel) === channel) || { channel, name: `PV${channel}`, enabled: true, physical_location: "", map_x: 20 * channel, map_y: 30 }; return `<div class="setup-pv" data-channel="${channel}"><label>PV${channel}</label><input data-pv="name" value="${esc(pv.name || `PV${channel}`)}" placeholder="Identificação"><input data-pv="physical_location" value="${esc(pv.physical_location || "")}" placeholder="Local físico"><input data-pv="wp" value="${esc(pv.wp || "")}" placeholder="Wp"><label class="toggle"><input type="checkbox" data-pv="enabled" ${pv.enabled !== false ? "checked" : ""}> habilitada</label></div>`; }).join("")}</div></div>`).join("");
}

function renderBlankCollectorCard(index) {
  return `<div class="setup-collector" data-collector-index="${index}"><div class="section-head"><div><span class="section-kicker">COLETOR ${index + 1}</span><h3>Microinversor ${index + 1}</h3></div><label class="toggle"><input type="checkbox" data-field="enabled" checked> Coletor ativo</label></div><div class="form-grid three"><div class="field"><label>Nome técnico</label><input data-field="name" value="Microinversor ${index + 1}"></div><div class="field"><label>IP do logger</label><input data-field="ip" placeholder="192.0.2.10"></div><div class="field"><label>Logger serial</label><input data-field="logger_serial" inputmode="numeric" placeholder="Número do logger"></div><div class="field"><label>Inversor serial (opcional)</label><input data-field="inverter_serial" placeholder="Separado do logger"></div></div><div class="setup-pv-grid">${[1,2,3,4].map((channel) => `<div class="setup-pv" data-channel="${channel}"><label>PV${channel}</label><input data-pv="name" value="PV${channel}" placeholder="Identificação"><input data-pv="physical_location" placeholder="Local físico"><input data-pv="wp" inputmode="decimal" placeholder="Wp"><label class="toggle"><input type="checkbox" data-pv="enabled" checked> habilitada</label></div>`).join("")}</div></div>`;
}

function collectSetupPayload() {
  const collectorsPayload = $$(".setup-collector").map((card) => { const get = (field) => $(`[data-field="${field}"]`, card); return { id: card.dataset.id || undefined, name: get("name").value, ip: get("ip").value.trim(), logger_serial: Number(get("logger_serial").value), inverter_serial: get("inverter_serial").value.trim() || null, enabled: get("enabled").checked, pv_inputs: $$(".setup-pv", card).map((pv) => ({ channel: Number(pv.dataset.channel), name: $(`[data-pv="name"]`, pv).value, physical_location: $(`[data-pv="physical_location"]`, pv).value, wp: Number($(`[data-pv="wp"]`, pv).value) || null, enabled: $(`[data-pv="enabled"]`, pv).checked })) }; });
  return { name: $("#installation-name").value, timezone: $("#installation-timezone").value || "UTC", latitude: Number($("#installation-latitude").value) || null, longitude: Number($("#installation-longitude").value) || null, collectors: collectorsPayload.filter((item) => item.ip && item.logger_serial) };
}

function renderSettings() {
  const setup = state.setup || { installation: {}, collectors: [], pv_inputs: [], settings: {} };
  const settings = setup.settings || {};
  $("#page-settings").innerHTML = `<div class="grid two-column"><article class="card"><div class="section-head"><div><span class="section-kicker">ASSISTENTE</span><h2>Instalação e coletores</h2><p>Os endereços abaixo são configurados por cliente e não são defaults públicos.</p></div></div><div class="form-grid three"><div class="field"><label>Nome da instalação</label><input id="installation-name" value="${esc(setup.installation?.name || "Minha instalação solar")}"></div><div class="field"><label>Fuso horário</label><input id="installation-timezone" value="${esc(setup.installation?.timezone || settings.timezone || "America/Sao_Paulo")}"></div><div class="field"><label>Latitude</label><input id="installation-latitude" value="${esc(setup.installation?.latitude || settings.latitude || "")}" inputmode="decimal"></div><div class="field"><label>Longitude</label><input id="installation-longitude" value="${esc(setup.installation?.longitude || settings.longitude || "")}" inputmode="decimal"></div></div><div id="setup-collectors">${renderSetupEditor()}</div><div class="form-actions"><button class="primary-button" id="save-setup">Salvar instalação e entradas</button><button class="secondary-button" id="add-collector">Adicionar coletor</button></div></article><div class="grid"><article class="card"><div class="section-head"><div><span class="section-kicker">API OPCIONAL</span><h2>Histórico remoto</h2><p>Sem API, o App permanece plenamente local.</p></div></div><div class="field"><label class="toggle"><input type="checkbox" id="api-enabled" ${settings.api_enabled ? "checked" : ""}> API externa habilitada</label></div><div class="field" style="margin-top:12px"><label>Endpoint base</label><input id="api-url" value="${esc(settings.api_url || "")}" placeholder="https://servidor-do-cliente/solar"></div><div class="field" style="margin-top:12px"><label>Token ${settings.api_token_configured ? "(já configurado; deixe vazio para preservar)" : ""}</label><input id="api-token" type="password" placeholder="não exibido"></div><div class="form-actions"><button class="primary-button" id="save-api">Salvar API</button><button class="secondary-button" id="test-api">Testar conexão</button></div></article><article class="card"><div class="section-head"><div><span class="section-kicker">MQTT DISCOVERY</span><h2>Broker do Home Assistant</h2><p>O broker complementa o App e não é caminho de coleta.</p></div></div><label class="toggle"><input type="checkbox" id="mqtt-enabled" ${settings.mqtt_enabled !== false ? "checked" : ""}> Publicar Discovery</label><div class="form-grid" style="margin-top:13px"><div class="field"><label>Host</label><input id="mqtt-host" value="${esc(settings.mqtt_host || "")}" placeholder="automático pelo Supervisor"></div><div class="field"><label>Porta</label><input id="mqtt-port" value="${esc(settings.mqtt_port || 1883)}" inputmode="numeric"></div><div class="field"><label>Usuário</label><input id="mqtt-username" value="${esc(settings.mqtt_username || "")}"></div><div class="field"><label>Senha</label><input id="mqtt-password" type="password" placeholder="não exibida"></div></div><div class="form-actions"><button class="primary-button" id="save-mqtt">Salvar MQTT</button></div></article></div></div>`;
  $("#save-setup")?.addEventListener("click", async () => { try { const payload = collectSetupPayload(); if (!payload.collectors.length) throw new Error("Cadastre ao menos um coletor com IP e logger serial."); const result = await api("setup", { method: "POST", body: JSON.stringify(payload) }); toast(`Configuração salva: ${result.collectors.length} coletor(es).`); await refresh(); } catch (error) { toast(error.message, true); } });
  $("#add-collector")?.addEventListener("click", () => { const holder = $("#setup-collectors"); const index = $$(".setup-collector", holder).length; holder.insertAdjacentHTML("beforeend", renderBlankCollectorCard(index)); toast("Use os campos do novo coletor e salve a instalação."); });
  $("#save-api")?.addEventListener("click", async () => { try { await api("settings/api", { method: "POST", body: JSON.stringify({ enabled: $("#api-enabled").checked, url: $("#api-url").value, token: $("#api-token").value }) }); toast("Configuração da API salva sem expor o token."); await refresh(); } catch (error) { toast(error.message, true); } });
  $("#test-api")?.addEventListener("click", async () => { try { const result = await api("settings/api/test", { method: "POST", body: "{}" }); toast(`API: ${result.state}.`, result.state === "offline"); await refresh(); } catch (error) { toast(error.message, true); } });
  $("#save-mqtt")?.addEventListener("click", async () => { try { await api("settings/mqtt", { method: "POST", body: JSON.stringify({ enabled: $("#mqtt-enabled").checked, host: $("#mqtt-host").value, port: Number($("#mqtt-port").value), username: $("#mqtt-username").value, password: $("#mqtt-password").value }) }); toast("Configuração MQTT salva."); await refresh(); } catch (error) { toast(error.message, true); } });
}

function render() {
  if (state.route === "overview") renderOverview();
  if (state.route === "collectors") renderCollectors();
  if (state.route === "map") renderMap();
  if (state.route === "diagnostics") renderDiagnostics();
  if (state.route === "history") renderHistory();
  if (state.route === "settings") renderSettings();
}

async function refresh() {
  try {
    state.status = await api("status");
    state.setup = await api("setup");
    const readingsBody = await api("readings?since_hours=24&limit=2000");
    state.readings = readingsBody.rows || [];
    $("#app-version").textContent = `TecnoHead Solar · v${state.status.app?.version || "—"}`;
    render();
  } catch (error) { toast(error.message || "Não foi possível carregar o App.", true); }
}

document.addEventListener("click", (event) => { const button = event.target.closest("[data-route]"); if (button) nav(button.dataset.route); });
$("#refresh-button").addEventListener("click", refresh);
nav("overview");
refresh();
