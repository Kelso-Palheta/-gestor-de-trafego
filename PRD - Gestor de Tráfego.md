# Documento de Requisitos do Produto (PRD): Ecossistema Autônomo de Tráfego Pago

**Versão:** 2.0  
**Data:** 08/03/2026  
**Autor:** Kelso Palheta  

---

## 1. Visão Geral

- **Objetivo:** Desenvolver, testar e hospedar um sistema autônomo em Python que utiliza agentes de IA para criar, monitorar e otimizar campanhas na Meta Ads, eliminando o erro humano e maximizando o Retorno Sobre o Investimento (ROI).
- **Risco Principal Mitigado:** Gasto acidental e descontrolado de orçamento. O sistema operará com limites diários e de campanha estritos, codificados diretamente nas requisições da API.

---

## 2. Arquitetura e Stack Tecnológico

- **Orquestrador de Desenvolvimento:** Google Antigravity (IDE). Será usado para coordenar os agentes na escrita do código, gerando *Artifacts* para a sua validação antes de qualquer execução.
- **Motor Lógico e NLP:** Claude Code operando no terminal para analisar as métricas retornadas pela API e tomar decisões de negócio.
- **Integração com a Meta:** Biblioteca oficial `facebook-business` (Python). Autenticação rigorosa via OAuth 2.0 (App ID, App Secret e Access Token de longa duração).
- **Banco de Dados:** PostgreSQL para persistência de dados históricos de campanhas, métricas, logs de ações e configurações. Migrations gerenciadas via Alembic.
- **Cache e Filas:** Redis para cache de métricas frequentes e como broker de filas para tarefas agendadas via Celery.
- **Hospedagem e Execução:** Servidor Virtual (VPS) no Google Cloud com ambiente isolado via Docker. As rotinas de verificação serão agendadas via Celery Beat (produção) ou Cron (desenvolvimento).
- **Versionamento:** Git + GitHub com branches protegidas (`main`, `staging`).
- **CI/CD:** GitHub Actions para testes automatizados, linting e deploy contínuo.

---

## 3. Casos de Uso e Escopo de Atuação

O ecossistema será construído com módulos modulares para atender às frentes específicas do seu portfólio:

### 3.1 Módulo de Negócios Locais

- **Batata Palheta Brutal:** Gestão de campanhas de alcance. O agente do Claude poderá criar testes A/B dinâmicos, garantindo que o posicionamento *"Duvido você encarar sozinho."* esteja sempre otimizado para o público de Vigia, pausando criativos que não gerem cliques.
- **Palheta EstétiCar Pro:** O sistema ajustará os lances (bids) de acordo com o fluxo de clientes, podendo pausar anúncios de conversão se a agenda da estética estiver cheia ou fora do horário comercial.

### 3.2 Módulo de Escala (SaaS)

- **SimuladoApp:** Monitoramento cirúrgico de conversão. O script avaliará o Custo por Aquisição (CPA) em tempo real. Se uma campanha de cadastro de alunos ou escolas ultrapassar o teto estipulado, o status do *AdSet* será alterado para `PAUSED` via API instantaneamente.

### 3.3 Módulo de Marketing Inteligente *(NOVO)*

- **Testes A/B Avançados:** Criação automática de múltiplas variações de copy e criativos, com rotação inteligente baseada em performance estatística (significância mínima de 95%).
- **Geração de Públicos:** Criação automática de Lookalike Audiences baseados nos melhores clientes (1%, 3%, 5% de semelhança).
- **Retargeting Automatizado:** Regras para criar campanhas de retargeting para quem interagiu (curtiu, comentou, visitou) mas não converteu — com janelas configuráveis (3, 7, 14 dias).
- **UTM Tracking:** Geração automática de UTM parameters em todos os links para rastreamento preciso no Google Analytics.
- **Calendário de Campanhas:** Planejamento e agendamento de campanhas sazonais (Dia dos Namorados, Black Friday, datas locais).
- **Arquitetura Multi-Plataforma:** Abstração do módulo de ads para suportar futuramente Google Ads e TikTok Ads via interface unificada.

---

## 4. Travas de Segurança Financeira (Prevenção de Erros)

Para garantir risco zero de vazamento de caixa, o código deverá conter as seguintes regras:

### 4.1 Travas Operacionais (originais)

1. **Modo "Dry-Run" (Obrigatório):** Durante os primeiros 15 dias, os scripts rodarão apenas em modo de simulação (somente leitura). Eles gerarão logs no terminal dizendo *"Eu pausaria a campanha X agora por ineficiência"*, mas sem enviar o comando POST para a Meta. Apenas após a sua validação de que a IA tomou a decisão correta, a permissão de escrita será ativada.
2. **Hard Limit de Campanha:** O script será bloqueado de criar qualquer campanha que não tenha o parâmetro `spend_cap` (limite máximo de gastos) preenchido e travado.
3. **Wasted Spend Finder:** Um script de varredura rodará a cada 3 horas. Qualquer anúncio com gasto superior a R$ 30,00 e zero conversões registradas terá sua veiculação interrompida na hora.

### 4.2 Controle Financeiro Profundo *(NOVO)*

4. **Orçamento Global Mensal:** Teto de gasto total mensal configurável (ex: R$ 2.000,00). Ao atingir esse valor, **todas** as campanhas são pausadas automaticamente, independente dos limites individuais.
5. **Alertas por Faixa de Gasto:**
   - 🟢 50% do orçamento mensal → Notificação informativa
   - 🟡 75% do orçamento mensal → Alerta de atenção
   - 🔴 90% do orçamento mensal → Alerta crítico + revisão automática de campanhas de baixo ROI
6. **Relatório P&L (Profit & Loss):** Receita gerada vs. gasto em ads por campanha, por negócio e total. Integração com Pixel da Meta e/ou com sistemas internos (ex: Batatas Fritas) para medir receita real.
7. **Histórico Financeiro:** Persistência em banco de dados de todo gasto, por dia, campanha e negócio, permitindo análise de tendências e comparação mês a mês.

---

## 5. Segurança de Aplicação *(NOVO)*

### 5.1 Gestão de Credenciais

- **Secrets Manager:** Todas as chaves (App ID, App Secret, Access Token) serão armazenadas no **Google Secret Manager** — nunca em `.env` em produção.
- **Rotação Automática de Tokens:** Implementação de fluxo para renovação automática do Access Token da Meta via System User Token de longa duração, com alerta 7 dias antes da expiração.
- **`.env` apenas para desenvolvimento local**, com `.env.example` versionado (sem valores reais) e `.env` no `.gitignore`.

### 5.2 Controle de Acesso (RBAC)

- **Roles definidos:**
  - `admin` — Pode ativar modo produção, alterar limites, visualizar tudo
  - `operator` — Pode visualizar métricas e relatórios
  - `readonly` — Somente visualização de dashboards
- **Ativação do modo produção** requer confirmação do `admin` via autenticação em dois fatores.

### 5.3 Auditoria e Logging

- **Log imutável de ações:** Toda ação executada pela IA (criar, pausar, alterar, excluir campanha) será registrada no banco com timestamp, ação, motivo, e resultado.
- **Retenção:** Logs mantidos por no mínimo 12 meses.
- **Formato:** JSON estruturado para facilitar consultas e integração com ferramentas de observabilidade.

### 5.4 Rate Limiting e Proteção

- **Controle de rate limit da Meta API:** Implementar backoff exponencial para respeitar os limites de requisições da Meta e evitar bloqueios silenciosos.
- **Circuit Breaker:** Se a API da Meta retornar erros consecutivos (5xx), o sistema entra em modo de espera e notifica o admin, sem tomar novas decisões até estabilizar.

---

## 6. Estatísticas e Analytics *(NOVO)*

### 6.1 KPIs Obrigatórios por Campanha

| Métrica | Descrição |
|---|---|
| **CTR** | Taxa de cliques (Click-Through Rate) |
| **CPC** | Custo por clique |
| **CPM** | Custo por mil impressões |
| **CPA** | Custo por aquisição/conversão |
| **ROAS** | Retorno sobre investimento em ads |
| **Frequência** | Média de vezes que cada pessoa viu o anúncio |
| **Alcance** | Número de pessoas únicas alcançadas |
| **Conversões** | Ações completadas (compra, cadastro, etc.) |

### 6.2 Análises Avançadas

- **Segmentação de métricas:** Quebra de performance por público, horário, dispositivo e posicionamento (Feed, Stories, Reels).
- **Heatmap de horários:** Mapa visual identificando os melhores horários e dias para veiculação.
- **Análise de funil:** Impressão → Clique → Landing Page → Conversão, com taxa de queda em cada etapa.
- **Benchmarking interno:** Comparação automática de desempenho entre campanhas ao longo do tempo.
- **Detecção de anomalias:** Alertas automáticos quando uma métrica desvia >2 desvios-padrão do histórico recente (ex: CPC subiu 300% repentinamente).

### 6.3 Relatórios Automáticos

- **Relatório diário:** Resumo de gastos, conversões e KPIs principais — enviado via Telegram.
- **Relatório semanal:** Análise completa com comparação semana anterior, top/bottom performers — enviado via Telegram + e-mail.
- **Relatório mensal:** P&L completo, tendências, recomendações da IA para o próximo mês.

---

## 7. IA Generativa *(NOVO)*

### 7.1 Geração de Conteúdo

- **Copies para Anúncios:** Geração automática de múltiplas variações de texto (headline, body, CTA) usando LLM, adaptadas ao tom de cada negócio (ex: tom desafiador para Batata Palheta, tom profissional para EstétiCar).
- **Sugestões de Criativos:** Briefings automáticos para criação de imagens/vídeos baseados em performance de campanhas anteriores.

### 7.2 Inteligência Preditiva

- **Previsão de Performance:** Modelos de ML que estimam CPA e ROAS prováveis antes de ativar uma campanha, baseados em dados históricos.
- **Otimização de Lances via ML:** Modelos que aprendam os melhores lances por horário, público e posicionamento, ajustando automaticamente ao longo do tempo.
- **Score de Fadiga de Criativo:** Detecção automática de quando um criativo começa a perder performance por saturação do público.

### 7.3 Resumos e Insights

- **Resumo Executivo Semanal:** Relatório em linguagem natural explicando o que aconteceu na semana, por que, e o que o sistema recomenda fazer.
- **Sugestões Proativas:** A IA sugere novas campanhas baseadas em tendências observadas, sazonalidades e oportunidades de mercado.
- **Análise de Sentimento:** Monitoramento dos comentários nos anúncios e alerta sobre negatividade ou tendências preocupantes.

---

## 8. Notificações e Comunicação *(NOVO)*

### 8.1 Canais

| Canal | Uso |
|---|---|
| **Telegram Bot** | Alertas em tempo real, relatórios diários, interação rápida com o sistema |
| **E-mail** | Relatórios semanais/mensais detalhados |
| **Dashboard Web** | Visualização de métricas em tempo real (fase futura) |

### 8.2 Níveis de Alerta

| Nível | Cor | Quando | Exemplo |
|---|---|---|---|
| **Info** | 🟢 | Relatório rotineiro | "Relatório diário: R$ 45,00 gastos, 12 conversões" |
| **Warning** | 🟡 | Atenção necessária | "Campanha X atingiu 75% do budget mensal" |
| **Critical** | 🔴 | Ação tomada pela IA | "Campanha Y pausada: CPA 3x acima do target" |
| **Emergency** | 🚨 | Falha de sistema | "Autenticação Meta falhou — sistema em modo seguro" |

### 8.3 Interação via Telegram

- Comandos rápidos: `/status`, `/gastos`, `/pausar [campanha]`, `/resumo`
- Confirmação de ações críticas: IA envia "Desejo pausar campanha X por ineficiência. Confirma? ✅/❌"

---

## 9. Infraestrutura e Resiliência *(EXPANDIDO)*

### 9.1 Stack de Infraestrutura

```
┌────────────────────────────────────────────┐
│             Google Cloud VPS               │
│  ┌──────────────────────────────────────┐  │
│  │            Docker Compose            │  │
│  │  ┌──────────┐  ┌──────────────────┐  │  │
│  │  │  App     │  │  PostgreSQL      │  │  │
│  │  │  Python  │  │  (dados/logs)    │  │  │
│  │  └──────────┘  └──────────────────┘  │  │
│  │  ┌──────────┐  ┌──────────────────┐  │  │
│  │  │  Celery  │  │  Redis           │  │  │
│  │  │  Worker  │  │  (cache/filas)   │  │  │
│  │  └──────────┘  └──────────────────┘  │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

### 9.2 Monitoramento

- **Health Checks:** Endpoint `/health` verificado a cada 1 minuto. Falha por 3 minutos → alerta no Telegram.
- **Heartbeat de Cron/Celery:** Cada tarefa agendada envia sinal de vida. Se o heartbeat falhar, alerta é disparado.
- **Métricas de sistema:** CPU, memória, disco monitorados via Prometheus + Grafana (ou solução leve equivalente).

### 9.3 Resiliência

- **Circuit Breaker:** Falhas consecutivas na API da Meta → modo de espera automático.
- **Retry com backoff exponencial:** Requisições falhadas são reprocessadas com espera crescente (1s, 2s, 4s, 8s...).
- **Fallback seguro:** Se o sistema não conseguir tomar uma decisão, **não faz nada** e notifica o admin. Nunca toma decisões em estado de incerteza.
- **Backup automatizado:** Dump diário do PostgreSQL para Google Cloud Storage com retenção de 30 dias.

### 9.4 Testes

- **Testes unitários:** Para toda lógica de decisão (pausar, ativar, ajustar lances).
- **Testes de integração:** Mock da API da Meta para validar fluxos end-to-end.
- **Testes de segurança financeira:** Cenários de boundary testing para validar que as travas funcionam (ex: tentar criar campanha sem `spend_cap`).
- **Cobertura mínima:** 80% de code coverage.

---

## 10. Plano de Implementação *(EXPANDIDO)*

| Fase | Ação | Resultado Esperado | Prioridade |
|---|---|---|---|
| **1. Setup e Segurança** | Criar ambiente Python com `facebook-business`, `python-dotenv`, `sqlalchemy`, `celery`. Configurar Google Secret Manager. Git + GitHub. | Projeto protegido, versionado, com CI configurado. | 🔴 Crítica |
| **2. Banco de Dados** | Modelar e criar schemas PostgreSQL para campanhas, métricas, logs de ações e configurações financeiras. | Schema pronto com migrations Alembic. | 🔴 Crítica |
| **3. Autenticação** | Criar `MetaAdsManager` com autenticação via OAuth 2.0, rotação de tokens e circuit breaker. | `auth.py` rodando, com testes de conexão e fallback. | 🔴 Crítica |
| **4. Extração de Dados** | Extrair Spend, CPA, CTR, CPC, CPM, ROAS, Conversões dos últimos 7 dias. Persistir no banco. | DataFrame Pandas + dados persistidos em PostgreSQL. | 🔴 Crítica |
| **5. Travas Financeiras** | Implementar Wasted Spend Finder, orçamento global, alertas por faixa (tudo em Dry-Run). | Scripts de otimização prontos para testes. | 🔴 Crítica |
| **6. Notificações** | Configurar Telegram Bot para alertas, relatórios e comandos interativos. | Bot funcional com `/status` e alertas automáticos. | 🟡 Alta |
| **7. Analytics** | Implementar KPIs, heatmaps, detecção de anomalias e relatórios automáticos. | Dashboard de métricas + relatórios diários/semanais. | 🟡 Alta |
| **8. IA Generativa** | Integrar LLM para geração de copies, resumos executivos e previsão de performance. | Módulo de IA gerando sugestões e relatórios inteligentes. | 🟡 Alta |
| **9. Marketing Avançado** | Lookalike audiences, retargeting automático, UTM tracking, calendário. | Módulo de marketing inteligente funcional. | 🟢 Média |
| **10. Infraestrutura Prod** | Dockerfile, docker-compose, Celery Beat, monitoramento, backup automatizado. | Container pronto para produção contínua no GCP. | 🔴 Crítica |

---

> **Nota:** Este documento é vivo e será atualizado conforme o desenvolvimento avança. Cada fase será validada em modo Dry-Run antes de qualquer ação real na Meta Ads.
