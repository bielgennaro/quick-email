# Quick Email

API e frontend para análise, classificação e resposta automática de e-mails, com suporte a anexos (PDF/TXT) e integração com modelos de IA.

## Funcionalidades

- **Classificação automática de e-mails**: Produtivo ou Improdutivo, com confiança.
- **Sugestão de resposta automática** baseada na categoria e confiança.
- **Processamento de texto**: Remoção de stopwords, lematização, tokenização.
- **Suporte a anexos**: Extração de texto de arquivos PDF e TXT.
- **Armazenamento MongoDB**: Persistência dos e-mails analisados.
- **Documentação embutida**: Endpoint `/docs` com informações da API.
- **Frontend React**: Interface moderna para interação com a API.

## Estrutura do Projeto

```
quick-email/
├── api/         # Backend Flask + IA
│   ├── main.py  # Endpoints, lógica de classificação e resposta
│   └── utils/   # Serviços auxiliares (IA, config, MongoDB)
├── web/         # Frontend React + Vite
│   └── package.json
```

## Principais Endpoints

- `GET /health`  
  Verifica saúde da aplicação.

- `POST /analyzis`  
  Analisa e classifica e-mail (texto + anexo opcional).  
  Parâmetros: `email`, `subject`, `content`, `file` (PDF/TXT)

- `GET /list`  
  Lista e-mails analisados, com paginação.

- `GET /docs`  
  Documentação da API.

## Como rodar

### Backend

1. Instale dependências:
    ```sh
    pip install -r requirements.txt
    ```
2. Configure variáveis de ambiente (MongoDB, etc).
3. Inicie a API:
    ```sh
    python api/main.py
    ```

### Frontend

1. Instale dependências:
    ```sh
    cd web
    npm install
    ```
2. Inicie o frontend:
    ```sh
    npm run dev
    ```

## Requisitos

- Python 3.10+
- Node.js 18+
- MongoDB

## Observações

- O modelo de IA pode ser ajustado via [api/utils/finetune_email_model.py](api/utils/finetune_email_model.py).
- O processamento de texto utiliza NLTK (stopwords, lematização).
- O projeto está preparado para português.