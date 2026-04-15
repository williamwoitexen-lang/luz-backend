# Documentação Técnica da API

Esta pasta contém toda a documentação técnica necessária para integração e uso da plataforma.

## Arquivos de Documentação

Todos os arquivos listados abaixo devem ser salvos com a **extensão .md** (Markdown):

### 1. PROJECT_OVERVIEW.md
Visão geral da arquitetura do sistema, componentes principais e fluxos.

### 2. CHAT_API.md
Documentação completa da API de conversas e chat.
- Endpoints disponíveis
- Autenticação
- Exemplos de requisições
- Estrutura de respostas

### 3. DOCUMENT_INGESTION.md
Fluxo de ingestão de documentos no sistema.
- Endpoints de upload
- Processamento de arquivos
- Confirmação de ingestão
- Tratamento de erros

### 4. FRONTEND_INTEGRATION.md
Guia de integração com aplicações frontend.
- Configuração do cliente
- Autenticação (Azure AD/MSAL)
- Exemplos de código
- Boas práticas

### 5. MASTER_DATA_API.md
API de dados mestres (localidades, categorias, funções).
- Endpoints GET disponíveis
- Filtros e parâmetros
- Autenticação
- Exemplos de integração

### 6. LLM_SERVER_ENDPOINTS.md
Endpoints do servidor de IA/LLM.
- Disponibilidade dos endpoints
- Fluxo de processamento
- Respostas esperadas

### 7. SERVICE_USAGE_EXAMPLES.md
Exemplos práticos de uso dos serviços.
- Casos de uso
- Código de exemplo
- Integração passo a passo

---

## Documentação Técnica Detalhada (Pasta `/api/`)

Arquivos técnicos com implementação e fluxos detalhados:

### 1. CHAT_IMPLEMENTATION_SUMMARY.md
Resumo completo de implementação do Chat.
- Endpoints implementados
- Estrutura do banco de dados
- Fluxos de persistência

### 2. INGESTION_FLOW.md
Fluxo detalhado de ingestão de documentos.
- Novo documento
- Update de versões
- Documentos inativos (is_active=false)
- Estrutura SQL
- Validações

### 3. INGEST_TEXT_CLEANING_CHANGES.md
Mudanças e limpeza de texto na ingestão.
- Processamento de conteúdo
- Remoção de metadados
- Tratamento de formatos

---

## Como Usar Esta Documentação

1. **Comece pelo**: `PROJECT_OVERVIEW.md` (visão geral)
2. **Depois consulte**: Os arquivos específicos conforme sua necessidade
3. **Para integração**: Veja `FRONTEND_INTEGRATION.md`
4. **Para técnico**: Acesse a pasta `/api/` para fluxos detalhados
5. **Exemplo de uso**: Consulte `SERVICE_USAGE_EXAMPLES.md`

---

## Requisitos Técnicos

- **Autenticação**: Azure Active Directory (Azure AD) / MSAL
- **Endpoints**: Base `/api/v1/`
- **Formato**: JSON
- **Idioma**: Documentação em português

---

## Suporte

Para dúvidas sobre a documentação ou implementação técnica, consulte o time de desenvolvimento.

**Data de Atualização**: 04 de Fevereiro de 2026  
**Versão**: 1.1
