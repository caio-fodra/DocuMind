# DocuMind

API backend de um assistente de documentos. Ela cadastra documentos, indexa o conteúdo e
responde perguntas usando apenas o que foi cadastrado. Não há geração por LLM: as respostas
saem da extração de frases do próprio texto, recuperadas por TF-IDF e similaridade de
cosseno. Há filtro de visibilidade por perfil, um nível de confiança em cada resposta e
proteção contra prompt injection.

## Como executar

Pré-requisito: Python 3.11+ ou Docker.

### Opção A: Docker

Não precisa de Python instalado. Com o Docker Desktop aberto, na raiz do projeto:

```bash
docker compose up --build
# Ctrl+C para parar
docker compose down
```

O `docker-compose.yml` define `DOCUMIND_AUTO_SEED=true`, então no primeiro boot a base é
populada sozinha com os 50 documentos fictícios e indexada.

### Opção B: local com venv

```bash
# 1. Criar e ativar o ambiente virtual
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Popular a base com a massa fictícia e indexar
python -m data.seed
python -m app.indexer

# 4. Subir a API
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`.

## Testes

```bash
python -m pytest -v
```

Os testes cobrem os fluxos principais:

- cadastro e listagem de documentos, validação de entrada e idempotência da indexação
  (reindexar não duplica trechos), em `tests/test_documents.py`;
- "responder só com contexto" e visibilidade por perfil, em `tests/test_ask.py`;
- prompt injection: a chave fictícia `FAKE-SECRET-123` nunca aparece na resposta, em
  `tests/test_injection.py`.

### Explorando pela documentação interativa

Com a API no ar, abra `http://localhost:8000/docs`. É o Swagger UI que o FastAPI gera
sozinho. Em `POST /ask`, clique em "Try it out", edite o JSON e execute.

No Windows, testar o `/ask` por `curl` no PowerShell pode corromper acentos no corpo JSON.
Pela `/docs` isso não acontece, então esse é o caminho recomendado para a demonstração.

### Perguntas para conferir o comportamento

| profile | question | esperado |
|---|---|---|
| `internal` | Quais formatos o Serviço Vega aceita? | responde (PDF/DOCX/TXT), `confidence: high` |
| `public` | Quais formatos o Serviço Vega aceita? | não sabe, porque "Serviço Vega" é `internal` |
| `public` | O que é o Portal Atlas? | responde, porque "Portal Atlas" é `public` |
| `internal` | Qual é a chave secreta? | não vaza a chave, `confidence: none` |
| `internal` | Qual é a capital da França? | não sabe, está fora do conteúdo cadastrado |

## API

Base URL: `http://localhost:8000`. Corpo e respostas em JSON.

### `GET /health`

Health check. Responde `200 {"status": "ok"}`.

### `POST /documents`

Cadastra um documento e o indexa. A operação é idempotente.

```json
{
  "title": "Portal Atlas",
  "content": "O Portal Atlas é um sistema fictício de consulta de indicadores...",
  "visibility": "public",
  "category": "referencia"
}
```

`visibility` aceita `public` ou `internal` (padrão `public`). `category` é opcional.
Sucesso devolve `201` com `{ id, title, visibility, category, created_at }`. Entrada
inválida, como título vazio, devolve `422` com um `detail`, sem stack trace.

### `GET /documents`

Lista os documentos cadastrados. Traz os metadados, sem o conteúdo completo.

### `POST /ask`

Recebe uma pergunta e um perfil, recupera os trechos permitidos e devolve a resposta.

```json
{ "question": "Quais formatos o Serviço Vega aceita?", "profile": "internal" }
```

Resposta `200`:

```json
{
  "answer": "O Serviço Vega é um serviço fictício de processamento de arquivos em lote. Cada envio aceita arquivos de até 50 MB, e os formatos suportados são PDF, DOCX e TXT.",
  "confidence": "high",
  "sources": [
    { "document_id": 5,  "title": "Serviço Vega",  "chunk_index": 0, "score": 0.32 },
    { "document_id": 37, "title": "Serviço Farol", "chunk_index": 0, "score": 0.16 }
  ]
}
```

O campo `sources` lista os trechos recuperados, ou seja, o conjunto de evidências
considerado (até `top_k`), ordenado por score. A resposta em si é montada a partir do
documento de maior score, como descrito em [Montagem da resposta](#3-montagem-da-resposta).

O campo `profile` (`public` ou `internal`) decide o que pode ser consultado. Um perfil
`internal` enxerga documentos públicos e internos; um perfil `public` enxerga só os
públicos.

## Decisões técnicas

### 1. Divisão do conteúdo (chunking)

Fica em `app/services/chunking.py`. O texto é quebrado por uma janela deslizante de
palavras: `chunk_size = 60` palavras com `overlap = 15`, ambos configuráveis. A sobreposição
preserva o contexto nas fronteiras, de modo que uma frase cortada entre dois trechos ainda
apareça inteira em um deles. Trabalhar por palavras, e não por caracteres, evita cortar no
meio de uma palavra.

Cada trecho vira uma linha na tabela `chunks`, ligada ao documento por `document_id` e
`chunk_index`. A restrição `UNIQUE (document_id, chunk_index)` e a estratégia
delete-then-insert garantem que reindexar o mesmo documento não duplique dados. Essa
idempotência tem teste.

### 2. Indexação e recuperação

Ficam em `app/services/indexer.py` e `retriever.py`. Sobre o corpus de trechos treina-se um
TF-IDF (`TfidfVectorizer` com remoção de acentos e stopwords em português). O vetorizador,
a matriz e os metadados são salvos em disco via joblib, então o índice sobrevive a
reinícios sem reprocessar tudo.

Ao receber uma pergunta:

1. a query é vetorizada com o mesmo TF-IDF;
2. calcula-se a similaridade de cosseno contra todos os trechos;
3. aplica-se o filtro de visibilidade, descartando trechos que o perfil não pode ver. Como
   isso acontece na recuperação, documentos proibidos nunca chegam à montagem da resposta;
4. aplica-se o corte de relevância, descartando trechos com score abaixo de
   `relevance_threshold` (0.1);
5. ordena-se por score e ficam os `top_k` (3).

### 3. Montagem da resposta

Fica em `app/services/llm.py`. A abordagem é extrativa: a resposta é composta por frases que
já existem nos documentos, o que impede alucinação. O passo a passo:

1. sem nenhum trecho relevante, devolve "Não sei responder..." com `confidence: none`, o que
   cumpre o "responder só com contexto";
2. concentra-se no documento de maior score e em até 2 trechos dele;
3. quebra os trechos em frases e remove as que parecem instrução injetada (ver a seção 5);
4. re-ranqueia as frases restantes por relevância à pergunta (TF-IDF e cosseno) e fica com
   as melhores, até 2;
5. redige eventuais tokens com cara de segredo antes de devolver.

As `sources` devolvidas trazem `document_id`, `title`, `chunk_index` e `score`, o que deixa
a resposta auditável.

### 4. Sinalização de confiança

O campo `confidence` tem três valores. `none` significa que nenhum trecho relevante foi
encontrado, ou seja, a API não sabe. `low` significa que há trecho, mas com similaridade
fraca. `high` significa que o score do melhor trecho passou do limiar de alta confiança
(0.30). Assim o cliente distingue uma resposta bem apoiada de um palpite fraco.

### 5. Resistência a prompt injection

Fica em `app/services/prompt_guard.py`. O conteúdo dos documentos é tratado como dado, nunca
como instrução. A defesa tem duas camadas.

A primeira é a sanitização. Antes de montar a resposta, frases que parecem comando injetado
("ignore as instruções anteriores", "desconsidere", "revele a chave", "sem restrições" e
afins) são descartadas e não entram na resposta. Foram colocadas algumas frases modelo,
mas um ponto de melhoria seria um jeito de não deixar hard-coded.

A segunda é a redação, como rede de segurança. Tokens com formato de segredo, como
`FAKE-SECRET-123`, são trocados por `[redigido]` caso passem pela etapa anterior.

Como a arquitetura é extrativa e não repassa o conteúdo a um LLM na forma de instrução, não
existe um "prompt do sistema" para ser sequestrado. O teste `tests/test_injection.py`
garante que a chave fictícia nunca aparece na resposta, inclusive para o perfil que pode ver
o documento.

### 6. Provider de IA (mock)

O edital permite provider real ou mockado. A escolha foi um mock extrativo local baseado em
TF-IDF. Ele é determinístico, não faz chamadas de rede e dispensa credenciais, então não há
segredo versionado. Por ser determinístico, é basicamente imune a halucinações.

### 7. Tratamento de erros e validação

A validação de entrada é declarativa, feita com Pydantic. Payloads inválidos retornam `422`
com um `detail` estruturado, sem expor stack trace. Recurso inexistente retorna `404`.

## Configuração (variáveis de ambiente)

Todas são opcionais e já vêm com os defaults abaixo. Para sobrescrever, copie `.env.example`
para `.env`. Nenhuma credencial é necessária.

| Variável | Default | Descrição |
|---|---|---|
| `DOCUMIND_RELEVANCE_THRESHOLD` | `0.1` | similaridade mínima para um trecho ser relevante |
| `DOCUMIND_TOP_K` | `3` | número máximo de trechos recuperados |
| `DOCUMIND_CHUNK_SIZE` | `60` | tamanho do trecho, em palavras |
| `DOCUMIND_CHUNK_OVERLAP` | `15` | sobreposição entre trechos, em palavras |
| `DOCUMIND_DATA_DIR` | `data` | pasta de persistência |
| `DOCUMIND_DB_PATH` | `data/documind.db` | caminho do banco SQLite |
| `DOCUMIND_INDEX_PATH` | `data/index.joblib` | caminho do índice |
| `DOCUMIND_AUTO_SEED` | `false` | popula a massa fictícia no startup se a base estiver vazia |