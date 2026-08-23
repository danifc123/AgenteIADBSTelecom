# DBS TELECOM — Assistente Virtual (Desafio Técnico)

MVP de aplicativo mobile com chat inteligente para a DBS TELECOM: identifica o cliente na IXC, entende o pedido via linguagem natural e encaminha automaticamente para **Comercial**, **Suporte** ou **Financeiro** — com pré-diagnóstico real no Suporte (não só roteamento cego) e consulta de boleto de verdade no Financeiro.

- **App mobile**: React Native + Expo
- **Backend**: Python + FastAPI, arquitetura em camadas
- **IA**: Ollama (modelo local, gratuito), com tool-calling via um **servidor MCP** próprio que expõe a IXC como ferramentas
- **Integração**: API webservice da IXC (validada contra o ambiente demo real, não só simulada)

---

## Sumário

- [Arquitetura](#arquitetura)
- [Tecnologias e justificativa](#tecnologias-e-justificativa)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Como rodar](#como-rodar)
- [Teste guiado](#teste-guiado)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Ollama: host vs Docker vs nuvem](#ollama-host-vs-docker-vs-nuvem)
- [Integração com a IXC](#integração-com-a-ixc)
- [Fluxos implementados](#fluxos-implementados)
- [Segurança](#segurança)
- [Testes](#testes)
- [Limitações conhecidas](#limitações-conhecidas)

---

## Arquitetura

```
[App Mobile RN/Expo] --HTTPS/JSON--> [Backend FastAPI]
                                          |
                                          |-- services/ (camada de aplicação — loop de tool-calling)
                                          |     |--> Ollama (/api/chat, tools=[...])
                                          |     |--> Cliente MCP (stdio) --> Servidor MCP (subprocess)
                                          |                                       |
                                          |                                       '--> integrations/ixc (httpx) --> IXC API
                                          |
                                          '-- core/session_store (em memória, por session_id)
```

O app mobile **nunca** fala diretamente com a IXC — só com o backend próprio. O token da IXC só existe dentro do container/processo do backend (variável de ambiente).

**Backend em camadas** (o `api` só traduz HTTP, `services` decide o que fazer, `integrations` fala com o mundo externo, `domain` é só os modelos — dependência sempre numa direção: `api → services → integrations/domain`):

```
backend/app/
  core/           # config, log, estado de sessão (transversal)
  domain/         # modelos e enums (Customer, Department, SupportStage...)
  api/            # rotas FastAPI — POST /api/identify, POST /api/chat, GET /health
  services/       # orquestração: classificação, loop Ollama, máquina de estados de Suporte
  integrations/
    mcp_server/   # servidor MCP (FastMCP) — expõe a IXC como tools
    ixc/          # cliente HTTP da IXC + normalização de dados
```

Isso **não é uma arquitetura RAG** — não há busca semântica/vetorial em documentos. É tool-calling: o Ollama chama ferramentas estruturadas (via MCP) que consultam a IXC diretamente. RAG faria sentido se, no futuro, o assistente precisasse responder perguntas livres buscando numa base de artigos/FAQ — não é o caso aqui, os dados são registros transacionais estruturados (cliente, boleto, plano).

---

## Tecnologias e justificativa

| Camada | Tecnologia | Por quê |
|---|---|---|
| Mobile | React Native + Expo | Framework real de app mobile (gera APK/iOS de verdade), grande ecossistema de bibliotecas, componentização natural |
| UI | React Native Paper | Componentes Material prontos e acessíveis, tema customizável com a paleta da marca sem gastar tempo montando design system do zero |
| Backend | Python + FastAPI | Assíncrono nativo (bom para orquestrar chamadas a IXC/Ollama em paralelo), tipagem com Pydantic, gera OpenAPI automaticamente |
| IA | Ollama (`qwen2.5:7b`) | Modelo local, gratuito, com suporte a tool-calling — atende o requisito de usar IA sem depender de API paga |
| Protocolo de ferramentas | MCP (Model Context Protocol) | Pedido explícito do desafio — abstrai a IXC como um servidor de ferramentas reutilizável, desacoplado do backend |
| Integração IXC | httpx assíncrono | Cliente HTTP moderno, mesma stack assíncrona do FastAPI |

---

## Estrutura de pastas

```
DBSTelecomAgenteIA/
  backend/
    app/                    # ver "Arquitetura" acima
    tests/                  # 27 testes automatizados (pytest)
    requirements.txt
    Dockerfile
    .env.example
  mobile/
    src/
      screens/               # Home, Identification, Chat
      components/            # ChatBubble, DepartmentBadge, QuickReplyButtons, TypingIndicator, DbsLogo
      services/               # única camada que fala HTTP com o backend
      domain/types.ts
      theme/                  # paleta DBS + tema do Paper
      context/                # sessão do atendimento
      navigation/
    App.tsx
    eas.json                 # perfis de build do EAS (gerar APK)
  docker-compose.yml
```

---

## Como rodar

### Pré-requisitos

- Python 3.12+
- Node.js 20+
- Uma forma de rodar o Ollama — **não precisa instalar nada localmente** se for usar o Ollama Cloud (padrão do projeto, ver [Ollama: host vs Docker vs nuvem](#ollama-host-vs-docker-vs-nuvem)); se preferir local, [instale o Ollama](https://ollama.com) e baixe o modelo: `ollama pull qwen2.5:7b`
- Docker (opcional — ver seção [Ollama: host vs Docker vs nuvem](#ollama-host-vs-docker-vs-nuvem))
- Expo Go instalado no celular (mais rápido para ver o app rodando) **ou** Android Studio com emulador configurado

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt

copy .env.example .env          # Windows
# cp .env.example .env          # Linux/Mac
# edite o .env com o IXC_TOKEN real e, se for usar Ollama Cloud, o OLLAMA_API_KEY

python -m uvicorn app.main:app --reload
```

Testar: `curl http://localhost:8000/health` → `{"status":"ok"}`

### 2. Backend via Docker (alternativa)

```bash
docker compose up --build
```

Por padrão sobe só o container `api`, apontando para o Ollama do **host** (ver próxima seção). Requer `backend/.env` preenchido antes.

### 3. Mobile

```bash
cd mobile
npm install
copy .env.example .env          # Windows — edite EXPO_PUBLIC_API_URL com o IP da sua máquina na rede local
npx expo start
```

Escaneie o QR code com o app **Expo Go** no celular (mesma rede Wi-Fi do computador). **Importante**: `EXPO_PUBLIC_API_URL` precisa ser o IP da máquina na rede local (ex: `http://192.168.0.10:8000`), nunca `localhost` — o celular não entende "localhost" como sendo o computador.

### 4. Gerar o APK

O projeto já vem configurado (`mobile/eas.json`) para build via [EAS](https://docs.expo.dev/build/introduction/) — só falta autenticar, o que exige uma conta Expo (gratuita) e login interativo, por isso não é algo que dá pra automatizar sem a sua conta:

```bash
cd mobile
npx eas-cli login          # abre o navegador pra login na conta Expo
npx eas-cli build --platform android --profile preview   # gera o .apk (build na nuvem, gratuito)
```

Alternativa sem depender da nuvem da Expo: build local, mas exige Android SDK + **JDK 17+** instalados na máquina (não tínhamos JDK 17+ disponível neste ambiente ao testar):

```bash
npx expo run:android --variant release
```

### 5. Testes automatizados

```bash
cd backend
pytest                                    # 27 testes, mockados, não tocam rede
RUN_LIVE_IXC_TESTS=1 pytest tests/test_ixc_client_live.py -v   # opcional: valida contra a IXC real
```

---

## Teste guiado

Depois de rodar o backend e o app, veja o [TESTE_GUIADO.md](TESTE_GUIADO.md) — um roteiro passo a
passo (identificação, Comercial, Financeiro, Suporte nos três desfechos N1/N2, casos de robustez)
com um contato de teste real e o que esperar em cada etapa.

---

## Variáveis de ambiente

### `backend/.env` (ver `.env.example` completo)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `IXC_TOKEN` | ✅ | Token da API da IXC. **Nunca commitar** — só em `.env`, que está no `.gitignore`. |
| `IXC_BASE_URL` | | URL base da API webservice da IXC |
| `OLLAMA_BASE_URL` | | Ver [Ollama: host vs Docker vs nuvem](#ollama-host-vs-docker-vs-nuvem) |
| `OLLAMA_MODEL` | | Modelo usado (`nemotron-3-nano:30b-cloud` por padrão, via Ollama Cloud) |
| `OLLAMA_API_KEY` | Só p/ Ollama Cloud | Chave grátis gerada em [ollama.com/settings/keys](https://ollama.com/settings/keys). Deixe em branco rodando localmente. |
| `OLLAMA_TIMEOUT_SECONDS` | | 180s por padrão — dá folga pro "cold start" do modelo |

### `mobile/.env`

| Variável | Descrição |
|---|---|
| `EXPO_PUBLIC_API_URL` | URL do backend. IP da LAN para testar em dispositivo físico, nunca `localhost`. |

---

## Ollama: host vs Docker vs nuvem

**Testamos as três formas de verdade, não só na teoria — e há diferenças reais de performance e de requisito de hardware:**

- **Ollama rodando no host** (fora do Docker): usa a aceleração disponível na máquina (GPU, se houver). Nos nossos testes, respostas do chat chegaram em poucos segundos.
- **Ollama rodando dentro do Docker Desktop** (`--profile containerized-ollama`): sem passagem de GPU configurada, a inferência cai para **CPU-only**. Medimos ~21 tokens/segundo de processamento de prompt, contra uma sessão de chat que já acumula ~1400 tokens de contexto — o suficiente para, em alguns casos, passar de 1 minuto por resposta e esbarrar em timeout.
- **Ollama Cloud** (`https://ollama.com`, sem instalar nada localmente): a alternativa para quem não tem GPU/RAM suficiente na máquina para carregar o modelo (encontramos isso na prática: `qwen2.5:7b` local precisa de ~2,5 GB de RAM livre só pra carregar, e nem sempre isso está disponível). Tier gratuito, "uso leve" (rate limited, mas suficiente pro MVP). Requer uma chave grátis em [ollama.com/settings/keys](https://ollama.com/settings/keys).

**Configuração usada por padrão neste projeto**: Ollama Cloud, com o modelo `nemotron-3-nano:30b-cloud` — gratuito ("uso leve", mesmo tier do `gpt-oss:20b`), com tool-calling confiável e português mais limpo. Comparamos os dois modelos gratuitos rodando o mesmo roteiro de teste (Comercial/Suporte/Financeiro): o `gpt-oss:20b` ocasionalmente misturava inglês no meio da resposta e inventou um desconto que não existia no catálogo; o `nemotron-3-nano:30b-cloud` não repetiu nenhum dos dois problemas nos testes — por isso é o padrão atual (`gpt-oss:20b` continua funcional como alternativa). `qwen3.5:cloud` também foi testado e **exige plano pago** (confirmado direto na API, apesar de alguma documentação de terceiros sugerir o contrário).

Se preferir rodar localmente (sem depender de internet/nuvem), troque no `.env`:

```bash
# Local, backend fora do Docker
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_API_KEY=

# Local, backend em Docker, Ollama no host
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_API_KEY=
```

Ou tudo 100% dentro do Docker (sem precisar instalar Ollama na máquina):

```bash
docker compose --profile containerized-ollama up
```

Nesse caso, troque `OLLAMA_BASE_URL` no `.env` para `http://ollama:11434` (o `.env.example` documenta os quatro cenários possíveis, com os prós/contras de cada um).

---

## Integração com a IXC

Toda a integração fica isolada em `backend/app/integrations/ixc/` — é a única parte do sistema que conhece a URL/token da IXC.

**Autenticação**: `Authorization: Basic base64(<token>)` — o token da IXC já contém as duas partes (não é `usuario:senha`), então se faz `base64` só do token puro.

**Padrão de consulta**: POST para `/webservice/v1/<tabela>`, header `ixcsoft: listar`, corpo `{"qtype": "<tabela>.<campo>", "query": "<valor>", "oper": "=", ...}`.

**Descoberta importante, confirmada testando contra o ambiente demo real**: a IXC guarda telefone e CPF/CNPJ **formatados** (`(64) 99823-4471`, `024.403.310-23`), não como dígitos puros — uma busca só com dígitos retorna zero resultados. O cliente normaliza a entrada do usuário para o formato brasileiro padrão antes de consultar (`app/integrations/ixc/client.py`, funções `_format_telefone`/`_format_cpf_cnpj`).

### Operações implementadas

| Operação | Tabela IXC | Observação |
|---|---|---|
| Identificar cliente (telefone/CPF) | `cliente` | ✅ Validado com dado real |
| Consultar boleto em aberto | `fn_areceber` | ✅ Validado — filtra `status == "A"` no lado do cliente |
| Consultar contratos/plano ativo | `cliente_contrato` | Implementado, não exercitado no fluxo principal |
| Abrir chamado de Suporte (N1) | `su_oss_chamado` | ✅ Validado com um insert de teste real (protocolo 13600/13601 no ambiente demo, marcados `[TESTE]`) |
| Agendar visita técnica (N2) | `su_oss_chamado` | ✅ Mesma tabela, `id_assunto` diferente ("VISTORIA TECNICA (OS)") |

**Campos obrigatórios do `su_oss_chamado`** (descobertos por tentativa/erro guiado pelas mensagens de validação da própria IXC, e confirmados olhando o formulário real no painel admin): `id_cliente`, `id_filial`, `id_assunto`, `id_setor`, `mensagem`, `tipo`, `prioridade`, `status`, `origem_endereco`, `endereco`. Os IDs de `id_assunto` usados (6 = "Lentidão", 22 = "VISTORIA TECNICA (OS)") são específicos do catálogo de assuntos **desse ambiente demo** — numa instalação diferente da IXC, precisam ser reconferidos em Suporte > Assuntos no painel admin.

### Tratamento de erros

Toda chamada à IXC pode falhar de formas diferentes, todas tratadas com exceções tipadas (`app/integrations/ixc/client.py`):

- `IXCUnavailableError` — timeout/rede/erro 5xx
- `IXCAuthError` — token rejeitado
- `IXCNotFoundError` — consulta OK, zero resultados
- `IXCMalformedResponseError` — resposta em formato inesperado
- `IXCValidationError` — a IXC recusou a criação de um registro por campo obrigatório ausente (descoberta real: a IXC responde HTTP 200 mesmo quando rejeita a criação — o corpo da resposta é que indica o erro)

As tools do MCP capturam todas essas exceções e devolvem um payload estruturado de erro para o modelo, que responde de forma conversacional ("não consegui acessar seus dados agora") em vez de travar o atendimento.

---

## Fluxos implementados

### 1. Identificação
`POST /api/identify {contact}` → IXC localiza o cliente por telefone ou CPF → cria a sessão e já devolve a saudação personalizada.

### 2. Comercial
Classificação → loop de tool-calling do Ollama com acesso a `list_plans` (catálogo estático, `data/plans.json`) e `get_customer_plan` (plano atual do cliente na IXC).

### 3. Suporte (com pré-diagnóstico real)
Não escalona direto. Roda uma máquina de estados determinística (`services/support_flow.py`) com o roteiro fixo exigido:

```
Múltiplos aparelhos? → Cabos conectados? → Reiniciar equipamento → Resolveu?
                                                                        |
                              ┌─────────────────────────────────────────┤
                              ▼                                         ▼
                     Resolvido (encerra)              Não resolveu → escalona N1
```

**Desfecho N1 vs N2**: se em qualquer etapa o cliente mencionar sinal de dano físico ("cabo cortado", "sem luz no equipamento"), o fluxo pula direto para o agendamento de visita técnica (N2) em vez de insistir em passos remotos que não resolveriam. Se os passos remotos não resolverem sem sinal de dano físico, escalona para a fila de Suporte (N1). As perguntas em si são fixas (não dependem do modelo "lembrar" de perguntar tudo) — só a interpretação da resposta do cliente usa heurística de palavra-chave.

### 4. Financeiro
Classificação → tool `get_boleto` consulta a IXC e retorna valor/vencimento reais. Instrução explícita no prompt para nunca inventar link/código de barras quando o campo vem vazio (bug real encontrado e corrigido durante os testes).

---

## Segurança

- Token da IXC só existe em `backend/.env` (gitignored) — nunca hardcoded, nunca exposto ao app mobile
- `app/integrations/ixc/` é o único código que conhece a URL/token da IXC
- Transporte MCP é stdio (subprocess local, não expõe porta de rede)
- Logs redigem automaticamente qualquer campo `authorization`/`token` (`app/core/logging_config.py`)
- `customer_id` **nunca** é decidido pelo modelo de IA — o backend injeta o id do cliente já identificado na sessão antes de qualquer chamada de ferramenta que dependa dele (evita o modelo alucinar ou vazar dado de outro cliente)

---

## Testes

```bash
cd backend && pytest -v
```

27 testes cobrindo: cliente IXC (sucesso, não encontrado, timeout, resposta malformada, formato do header de auth), classificador por palavra-chave, máquina de estados de Suporte (ordem não pode ser pulada, "não resolveu" não pode ser confundido com "resolveu", sinal de dano físico pula pra N2), store de sessão.

Mais 2 testes de integração real contra a IXC (não rodam por padrão, exigem `RUN_LIVE_IXC_TESTS=1` e um `.env` válido).

---

## Limitações conhecidas

- **Emulador Android**: não foi possível validar num emulador local nesta máquina (faltava JDK 17+, não instalado para não fazer uma mudança grande no sistema sem confirmar antes). O app foi validado por outros meios: `tsc --noEmit` sem erros e `expo export` empacotando com sucesso (1144 módulos). Recomendado testar via Expo Go num celular real (`npx expo start` + escanear o QR code) ou instalar um JDK 17+ para rodar o emulador.
- **`id_assunto`/`id_setor` do chamado de Suporte** são específicos do catálogo deste ambiente demo — reconferir numa instalação de produção.
- **Sessão em memória**: reinicia zerada se o backend reiniciar (sem banco de dados — decisão deliberada para manter o MVP simples dentro do prazo).
