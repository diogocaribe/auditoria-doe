# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Aplicação Streamlit para auditoria humana de publicações do Diário Oficial do Estado (contexto INEMA e SEMA). O auditor compara os atos extraídos por um pipeline externo com o texto da publicação e a página original, e marca cada publicação se a separação da publicação ocorreu ded forma correta ou errada. A interface e os identificadores são em português.

O `README.md` e os metadados do `pyproject.toml` ainda descrevem um template "Hello World" (`src/`, Gunicorn) que não existe mais. Confie no código, no `Dockerfile` e nos arquivos compose.

## Comandos

Execute tudo a partir da raiz do repositório, pois o `.env` é lido relativo ao diretório atual.

```bash
# Configuração: copie .env-dist para .env e preencha as credenciais
cp .env-dist .env

# Docker (a rede externa "inema" precisa existir: docker network create inema)
docker compose up --build                                # força HOST=postgres
docker compose -f docker-compose.server.yml up -d --build  # usa o HOST do .env

# Local
poetry install --no-root
poetry run streamlit run auditoria-doe/app.py            # http://localhost:8501

# Testes
poetry run pytest tests
poetry run pytest tests/test_app.py::test_hello_world    # teste único
```

- `tests/test_app.py` está quebrado: é resquício do template, importa `auditoria_doe.app.main`, que não existe, e falha na coleta.
- Não há linter, formatador ou CI configurados.
- Para testar a interface sem banco, use `streamlit.testing.v1.AppTest.from_file("auditoria-doe/app.py")` e substitua `doe_data.queries` em `sys.modules` por um módulo falso antes de rodar. Importar o módulo real exige todas as variáveis do `.env`, e `get_engine` tenta conectar ao PostgreSQL.

## Arquitetura

- `auditoria-doe/app.py` é um script Streamlit único, sem `main()`. Ele roda do início ao fim a cada interação, e o estado mantido entre execuções é `st.session_state.index` e o seletor `filtro_auditoria`.
- `auditoria-doe/doe_data/queries.py` concentra todo o SQL, escrito à mão com `sqlalchemy.text`.
- `auditoria-doe/doe_data/acesso_bd.py` cria um engine novo a cada chamada de `get_engine()`, com `sslmode=disable`.
- `auditoria-doe/utils.py` limpa o texto dos atos e destaca trechos na publicação.

### Importações

O diretório `auditoria-doe` tem hífen e não é um pacote Python importável. Os imports `from doe_data...` e `from utils...` funcionam porque o Streamlit coloca o diretório do script no `sys.path`.

### Banco de dados

PostgreSQL com o schema mantido fora deste repositório, sem migrações aqui.

- Leitura de publicações: view `vw_publicacao`. A fila de trabalho são as linhas com `auditoria IS NULL`.
- Leitura de atos: `processing.ato`, por `publicacao_id`.
- Escrita: `processing.publicacao.auditoria`, onde `true` é correta, `false` é errada e `NULL` é não avaliada.

### Configuração

`Settings` (pydantic-settings) exige `DATABASE`, `USER_DB`, `PASSWORD_DB`, `HOST`, `PORT` e `DATABASE_URL`, e é instanciado na importação de `acesso_bd.py`. O host da conexão sempre vem de `HOST`, que substitui o host presente em `DATABASE_URL`. Variáveis de ambiente têm precedência sobre o `.env`.

### Docker

A imagem contém apenas as dependências, sem `COPY` do código. A aplicação só existe no container por causa do volume `.:/auditoria-doe` definido nos arquivos compose, portanto um `docker run` simples da imagem não funciona.

### Coluna "LINK" e HTML

A cada execução, `app.py` baixa a página original com `httpx` e `verify=False`. O conteúdo baixado e os textos do banco são renderizados com `unsafe_allow_html=True`.

### Fluxo de avaliação

Os botões "Correta" e "Errada" gravam via `on_click`, com o id da publicação exibida passado em `args`. O callback roda antes de o script buscar a fila, então a tela e os contadores já refletem a gravação. O item avaliado sai da fila e o seguinte assume o mesmo índice, portanto não incremente `index` ao avaliar. Gravar no corpo do script, depois da consulta da fila, faz a avaliação seguinte cair na publicação errada.

O seletor "Visualizar publicações" define qual status é listado e volta `index` a 0 ao mudar. Nas opções "Corretas" e "Erradas" a tela é somente leitura, com os botões de avaliação desabilitados.
