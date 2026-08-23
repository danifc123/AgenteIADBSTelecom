# Teste guiado — DBS TELECOM

Este roteiro existe pra quem for pegar o projeto (avaliador, outro dev) conseguir testar o sistema
do início ao fim sem precisar adivinhar o que fazer. Assume que você já seguiu o "Como rodar" do
[README.md](README.md).

---

## 0. Antes de começar

Checklist rápido — confirme que os 3 pontos abaixo estão de pé antes de testar:

| Componente | Como confirmar |
|---|---|
| Backend | `curl http://localhost:8000/health` → `{"status":"ok"}` |
| Ollama (host, Docker ou Cloud — ver README) | Se for local: `curl http://localhost:11434/api/tags` responde. Se for Ollama Cloud: basta o `OLLAMA_API_KEY` estar preenchido no `.env`. |
| App mobile | `npx expo start` rodando, QR code visível no terminal |

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

Sessão nova. Digite: **"tenho algum boleto em aberto?"**

**✅ Esperado:**
- Classifica como Financeiro
- Retorna valor e vencimento reais de um boleto (ou diz claramente que não há nenhum em aberto)
- **Nunca** deve inventar link ou código de barras — se vier vazio, a IA deve dizer que vai chegar
  por outro canal, não inventar uma URL

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
pytest -v                                                        # 27 testes, mockados
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
