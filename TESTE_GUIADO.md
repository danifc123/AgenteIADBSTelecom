# Teste guiado — DBS TELECOM

Este documento existe pra você conseguir instalar e testar o sistema por conta própria, do início ao
fim, sem precisar adivinhar nada nem depender de mais ninguém pra tirar dúvida. Os passos abaixo
assumem que é a primeira vez que você roda um projeto assim — cada comando e cada arquivo mencionado
são explicados.

Existem dois jeitos de testar, e os dois exigem o backend (o "cérebro" do sistema, que fala com a
IXC e com a IA) rodando na sua máquina — isso é sempre necessário, não tem como testar sem ele:

- **Caminho rápido — instalar o `.apk`**: se você recebeu um arquivo `.apk`, instale no Android
  normalmente e aponte o app pro endereço do seu backend numa telinha de configuração dentro do
  próprio app (Passo 5A). Não precisa instalar Node.js nem mexer com Expo.
- **Caminho completo — rodar tudo a partir do código-fonte**: ideal se você não recebeu o `.apk`,
  ou quer ver o app rodando direto do código. Usa o app **Expo Go** pra abrir o projeto (Passo 5B).

Nos dois casos, os Passos 1 a 4 abaixo são os mesmos — eles ligam o backend, que é a parte que não
muda independente de como você for abrir o app.

---

## 0. Antes de começar

### Passo 1 — O que instalar no computador

| Programa | Pra que serve | Onde baixar |
|---|---|---|
| **Python 3.12 ou mais novo** | Roda o backend (o "cérebro" do sistema) — necessário nos dois caminhos | https://www.python.org/downloads/ — **na instalação, marque a caixinha "Add Python to PATH"** antes de clicar em instalar, é fácil esquecer e é importante |
| **Node.js 20 ou mais novo** (versão "LTS") | Roda o app mobile em modo de desenvolvimento — **só necessário no caminho completo** (Passo 5B, via Expo Go); se for usar o `.apk` (Passo 5A), pode pular esse item | https://nodejs.org/ |
| **Git** (opcional — só se preferir baixar o código assim em vez de ZIP) | Baixa o código do GitHub | https://git-scm.com/downloads |

Depois de instalar Python e Node, **feche todos os terminais abertos e abra um novo** — isso garante
que o sistema reconhece os comandos novos.

Pra confirmar que instalou certo, abra um terminal (no Windows, procure por "PowerShell" no menu
iniciar) e digite, um comando por vez:
```powershell
python --version
node --version
```
Se aparecer um número de versão em cada um (ex: `Python 3.12.4`, `v20.11.0`), está tudo certo. Se
aparecer erro dizendo que o comando não é reconhecido, revise a instalação (veja a tabela de
problemas comuns no fim desta seção).

### Passo 2 — Baixando o código do projeto

**Opção mais simples (sem precisar instalar Git):**
1. Acesse https://github.com/danifc123/AgenteIADBSTelecom
2. Clique no botão verde **"Code"** → **"Download ZIP"**
3. Extraia o `.zip` baixado numa pasta de fácil acesso (ex: `C:\Projetos\DBSTelecomAgenteIA`) —
   no Windows, clique com o botão direito no `.zip` → "Extrair tudo"

**Opção com Git**, pelo terminal:
```powershell
git clone https://github.com/danifc123/AgenteIADBSTelecom.git
cd AgenteIADBSTelecom
```

A partir daqui, todo comando abaixo assume que o terminal está **dentro da pasta do projeto** que
você acabou de baixar/extrair (use `cd caminho\da\pasta` pra entrar nela).

### Passo 3 — Ligando o backend (o "servidor" do sistema)

Copie e cole os comandos abaixo no terminal, um de cada vez, apertando Enter depois de cada linha:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

A instalação demora um ou dois minutos na primeira vez — é normal, está baixando as peças
necessárias. Quando o terminal voltar a mostrar o cursor piscando (sem mais texto rolando), terminou.

Agora crie o arquivo de configuração:
```powershell
copy .env.example .env
```

Abra o arquivo `.env` que acabou de aparecer dentro da pasta `backend` — pode usar o Bloco de Notas
mesmo (botão direito no arquivo → Abrir com → Bloco de Notas). Preencha duas informações nele:

1. **`IXC_TOKEN`** — cole o token que a DBS TELECOM já forneceu nos materiais do desafio (arquivo
   "IXC.pdf" enviado ao candidato):
   ```
   IXC_TOKEN=105:1c0e2d764be841d9b88b02414337d7bbc2dd4e1bb940295343b36d31cbaa9f98
   ```
2. **Ollama Cloud** (o serviço de IA, gratuito) — troque estas três linhas no arquivo:
   ```
   OLLAMA_BASE_URL=https://ollama.com
   OLLAMA_MODEL=nemotron-3-nano:30b-cloud
   OLLAMA_API_KEY=coloque_sua_chave_aqui
   ```
   Pra conseguir a chave (`OLLAMA_API_KEY`), leva menos de 2 minutos:
   1. Acesse https://ollama.com/settings/keys
   2. Crie uma conta gratuita (ou entre, se já tiver)
   3. Clique em "Create API Key" e copie o valor gerado
   4. Cole no lugar de `coloque_sua_chave_aqui`

Salve o arquivo (Ctrl+S) e feche o Bloco de Notas.

Agora, de volta ao terminal, ligue o backend:
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Como saber que funcionou:** o terminal vai mostrar várias linhas e terminar em algo parecido com
`Uvicorn running on http://0.0.0.0:8000`. **Deixe essa janela do terminal aberta** — ela é o "motor"
do sistema rodando; fechar essa janela desliga o backend.

Pra confirmar de outro jeito, abra o navegador (Chrome, Edge, etc.) e acesse:
```
http://localhost:8000/health
```
Deve aparecer `{"status":"ok"}` na tela.

### Passo 4 — Descobrindo o IP da sua máquina (pro celular conseguir se conectar)

O celular não entende "localhost" (isso significa "esse mesmo aparelho" — no celular apontaria pra
ele mesmo, não pro computador). Ele precisa do endereço do computador na rede Wi-Fi.

Abra **outro terminal novo** (deixe o do backend aberto, rodando) e digite:
```powershell
ipconfig
```
Procure a linha "Endereço IPv4" — geralmente parecido com `192.168.0.XX` ou `192.168.1.XX`. Anote
esse número, você vai usar no próximo passo.

### Passo 5A — Instalando e configurando o `.apk` (caminho rápido)

Use esse passo se você recebeu um arquivo `.apk` junto com a entrega.

1. Transfira o `.apk` pro celular Android (baixe direto no navegador do celular, a partir do link
   que você recebeu, ou copie o arquivo por cabo/e-mail/drive — qualquer forma funciona).
2. Toque no arquivo `.apk` baixado pra instalar. O Android costuma pedir permissão pra "instalar
   apps de fontes desconhecidas" — é esperado nesse tipo de instalação fora da Play Store, pode
   autorizar.
3. Abra o app instalado. Na tela inicial (com o botão **"Falar com a DBS"**), toque no ícone de
   **engrenagem** ao lado do botão.
4. No campo que aparece, digite o endereço do backend usando o IP que você anotou no Passo 4,
   sempre no formato `http://SEU-IP:8000`. Exemplo, se o IP for `192.168.0.42`:
   ```
   http://192.168.0.42:8000
   ```
5. Toque em **"Testar conexão"**. Se aparecer "Conexão OK" em verde, está tudo certo — toque em
   **Salvar** e pule pro Passo 6. Se der erro, confira: a janela do backend (Passo 3) continua
   aberta sem erro? O celular está na mesma rede Wi-Fi do computador?

Essa configuração fica guardada no próprio celular — não precisa repetir isso da próxima vez que
abrir o app, mesmo que feche e abra de novo. Se quiser trocar de backend depois, é só voltar nessa
mesma tela.

### Passo 5B — Rodando pelo Expo Go (caminho completo, direto do código-fonte)

Use esse passo se você não recebeu o `.apk`, ou prefere rodar o app a partir do código.

Abra mais um terminal (o terceiro agora), entre na pasta do projeto e depois:
```powershell
cd mobile
npm install
```
Também demora um pouco na primeira vez.

Crie o arquivo de configuração do app:
```powershell
copy .env.example .env
```
Abra o arquivo `mobile\.env` (Bloco de Notas) e troque o IP pelo que você anotou no passo 4,
mantendo `:8000` no final. Exemplo, se o seu IP for `192.168.0.42`:
```
EXPO_PUBLIC_API_URL=http://192.168.0.42:8000
```
Salve e feche.

Agora ligue o app:
```powershell
npx expo start
```
Vai aparecer um **QR code** desenhado com blocos no terminal.

No seu celular:
1. Instale o app **"Expo Go"** — é gratuito, procure na Play Store (Android) ou App Store (iPhone)
2. Confirme que o celular está **na mesma rede Wi-Fi** do computador — esse é o detalhe que mais
   costuma dar problema; se o celular estiver usando dados móveis (4G/5G) em vez do Wi-Fi, não vai
   funcionar
3. Abra o Expo Go e toque em "Scan QR code" (ou, no iPhone, aponte a câmera nativa pro código)

O app abre direto na tela inicial da DBS TELECOM, já configurado com o IP do `mobile\.env` — se
quiser mudar o endereço depois sem editar o arquivo de novo, a mesma tela de "Configurar servidor"
do Passo 5A (ícone de engrenagem na Home) também funciona aqui.

### Passo 6 — Checklist final antes de testar

| Componente | Como confirmar que está ligado |
|---|---|
| Backend | `http://localhost:8000/health` no navegador do computador → `{"status":"ok"}` |
| App mobile | Abriu (pelo `.apk` ou pelo Expo Go) mostrando a tela Home da DBS TELECOM, e o teste de conexão da tela de configuração deu "Conexão OK" |

Se os dois estão de pé, siga pro roteiro de teste a partir da seção 1, logo abaixo.

### Problemas comuns

| Sintoma | Causa provável | Como resolver |
|---|---|---|
| Tela "Testar conexão" dá erro (vermelho) | Backend não está rodando, IP digitado errado, ou celular numa rede diferente | Confira se a janela do backend (Passo 3) continua aberta sem erro; confira se o IP digitado bate com o do `ipconfig` mais recente (o IP pode mudar se o Wi-Fi foi reconectado); confirme que o celular está na mesma rede Wi-Fi do computador (não em dados móveis) |
| App no celular (via Expo Go) não carrega / fica preso no QR code | Celular e computador em redes Wi-Fi diferentes | Conecte os dois na mesma rede Wi-Fi (desligue os dados móveis do celular pra garantir) |
| Android bloqueia a instalação do `.apk` | Segurança padrão do Android pra apps fora da Play Store | Ao instalar, toque em "Instalar mesmo assim" / autorize "fontes desconhecidas" quando o Android perguntar |
| Chat não responde / aparece "não conseguimos falar com o servidor" já dentro do chat | O backend caiu ou travou depois que você já tinha conectado | Volte na tela de configuração (engrenagem) e toque em "Testar conexão" de novo pra confirmar; se falhar, confira a janela do terminal do backend |
| `python` ou `node` "não é reconhecido como comando" | Instalação não adicionou ao PATH, ou terminal não foi reaberto depois de instalar | Feche todas as janelas de terminal e abra uma nova; se continuar, reinstale marcando a opção de adicionar ao PATH |
| Primeira mensagem do chat demora bastante ou dá timeout | Normal — o modelo de IA "acorda" na nuvem na primeira chamada | Aguarde até 1 minuto na primeira mensagem; as seguintes costumam ser bem mais rápidas |
| `pip install` ou `npm install` dá erro | Geralmente falta de conexão com a internet no momento, ou versão de Python/Node desatualizada | Confira a internet; confira que `python --version`/`node --version` batem com os mínimos pedidos (3.12+ / 20+) |

---

Você vai precisar de um **contato de teste real** do ambiente demo da IXC. Use:

```
Telefone: 54996656569
Cliente:  Everaldo
```

(Esse é um cadastro real do ambiente `demo.ixcsoft.com.br` — os dados retornados, como boleto e
plano, são os que existirem de fato lá no momento do teste.)

---

## 1. Identificação

1. Abra o app → tela Home → toque em iniciar atendimento
2. Digite `54996656569` no campo (a máscara formata sozinha)
3. Toque em **Continuar**

**✅ Esperado:** abre o chat com a saudação "Olá, Everaldo!" (ou o nome que a IXC retornar).

**Teste negativo (opcional):** tente identificar com um número que não existe, ex. `11999999999`.
Deve informar que não encontrou o cadastro, sem travar o app.

---

## 2. Comercial

> A partir daqui, **use uma sessão nova pra cada seção** (volte à tela inicial e identifique de
> novo) — testar vários assuntos na mesma conversa contínua é válido, mas pode deixar o histórico
> mais confuso de acompanhar num teste guiado.

Digite: **"quero saber os planos disponíveis"**

**✅ Esperado:**
- Classifica como Comercial
- Resposta em português, tom natural, sem tabela em markdown, com emoji
- Lista alguns planos reais (não todos de uma vez) com preço e benefício prático

Continue a conversa: **"tenho uns 5 aparelhos conectados, uso bastante streaming"** — veja se a
recomendação se ajusta ao que você descreveu.

---

## 3. Financeiro

Sessão nova. Identifique-se com **`03824222000117`** (CNPJ — este cliente de teste tem boletos com
código de barras real cadastrado, diferente do Everaldo). Digite: **"tenho algum boleto em aberto?"**

**✅ Esperado:**
- Classifica como Financeiro
- Retorna valor e vencimento reais de um boleto, e o **código de barras (linha digitável) real**
  pra pagar — isso cobre o requisito do desafio de "disponibilizar o boleto para acesso/download"
- Se testar com o Everaldo (`54996656569`) em vez disso: o boleto dele não tem código de barras
  cadastrado na IXC demo, então a IA deve dizer isso com transparência, **nunca** inventar um link
  ou código

---

## 4. Suporte — caminho resolvido (N1, sem escalar)

Sessão nova. Digite: **"minha internet está lenta"**

O sistema faz uma pergunta por vez, na ordem — responda cada uma antes de ver a próxima:

| # | Pergunta esperada | O que responder |
|---|---|---|
| 1 | Se o problema é em vários aparelhos ou só um | "só nesse aqui" |
| 2 | Se os cabos estão bem conectados | "sim, estão ok" |
| 3 | Pra desligar da tomada, esperar 30s e religar | "já fiz, reiniciei" |
| 4 | Se resolveu | **"sim, resolveu"** |

**✅ Esperado no final:** a IA comemora a resolução e, na sequência, consulta o plano atual do
cliente e — só se fizer sentido (plano baixo, ou nenhum contrato encontrado) — sugere um plano
melhor de forma leve, sem empurrar venda. Não deve abrir nenhum chamado.

---

## 5. Suporte — caminho não resolvido (escalona N1)

Sessão nova, repita as 4 perguntas da seção 4, mas na última responda **"não, continua lenta"**.

**✅ Esperado:** abre um chamado real na IXC e retorna um número de protocolo.

---

## 6. Suporte — dano físico (vai direto pra N2)

Sessão nova. Digite: **"minha internet caiu e acho que o cabo foi cortado"**

**✅ Esperado:**
- Pula direto pro agendamento de visita técnica — **não** faz as 4 perguntas de N1 (não faria
  sentido pedir pra reiniciar um equipamento com o cabo rompido)
- Retorna um protocolo real de visita técnica agendada na IXC

**Variação:** teste também mencionar o dano físico **no meio** do fluxo N1 (ex: responder "ah, na
verdade percebi que o cabo está cortado" na pergunta dos cabos) — deve pular pra N2 do mesmo jeito,
de qualquer estágio em que estiver.

---

## 7. Robustez (opcional, mas recomendado)

- Gíria/erro de digitação: **"blz vlw pfvr quero pagar minha fatura"** → ainda deve classificar
  como Financeiro corretamente
- Pedido ambíguo: **"oi"** ou **"preciso de ajuda"** → a IA deve pedir esclarecimento sobre qual
  departamento (Comercial/Suporte/Financeiro), sem travar nem alucinar uma resposta
- Deixe o app sem uso por alguns minutos e volte a mandar mensagem → a sessão deve continuar
  funcionando (estado em memória, não expira sozinho durante o teste)

---

## 8. Testes automatizados (sem precisar do app)

```bash
cd backend
pytest -v                                                        # 29 testes, mockados
RUN_LIVE_IXC_TESTS=1 pytest tests/test_ixc_client_live.py -v     # opcional, contra a IXC real
```

No PowerShell, a variável de ambiente da segunda linha é definida assim:

```powershell
$env:RUN_LIVE_IXC_TESTS = "1"
pytest tests/test_ixc_client_live.py -v
```

---

## O que fazer se algo sair diferente do esperado

Anote **a mensagem exata** que apareceu (print ou copiar o texto) e em qual passo do roteiro — isso
é o suficiente pra rastrear se foi um problema de classificação, de uma ferramenta específica (IXC)
ou do modelo de IA. Consulte também a seção "Limitações conhecidas" no [README.md](README.md).
