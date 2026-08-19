# DBS TELECOM — Assistente Virtual (Desafio Técnico)

MVP de aplicativo mobile com chat inteligente para a DBS TELECOM: identifica o cliente na IXC, entende o pedido via linguagem natural e encaminha automaticamente para **Comercial**, **Suporte** ou **Financeiro**.

- **App mobile**: React Native + Expo
- **Backend**: Python + FastAPI, arquitetura em camadas
- **IA**: Ollama (modelo local, gratuito), com tool-calling via um servidor **MCP** próprio que expõe a IXC como ferramentas

> Este branch (`main`) contém só a estrutura inicial do projeto (scaffold), sem a implementação das regras de negócio. A implementação completa — integração com a IXC, servidor MCP, orquestração com Ollama, telas do app, testes automatizados — está no branch `dev`.

## Estrutura

```
DBSTelecomAgenteIA/
  backend/
    app/
      core/       # config, logging (transversal)
      domain/      # modelos de domínio
      api/         # rotas FastAPI (só /health por enquanto)
      services/    # camada de aplicação/orquestração
      integrations/ # integrações externas (IXC, MCP)
    requirements.txt
    Dockerfile
    .env.example
  mobile/          # app Expo (scaffold padrão)
  docker-compose.yml
```

## Como rodar (scaffold)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # Windows
python -m uvicorn app.main:app --reload
```

Testar: `curl http://localhost:8000/health` → `{"status":"ok"}`

### Mobile

```bash
cd mobile
npm install
npx expo start
```
