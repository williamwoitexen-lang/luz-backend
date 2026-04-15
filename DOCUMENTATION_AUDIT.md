# Documentação Técnica – Plataforma de Gestão de Conhecimento com IA

**Versão da documentação:** 1.0  
**Última atualização:** 02/02/2026  
**Idioma:** Português

---

## 1. Visão Geral

Esta documentação consolida o conhecimento técnico completo da plataforma de gestão de conhecimento com integração de IA. O sistema é composto por três componentes principais:

**Frontend** – Aplicação SPA responsável pela experiência do usuário, autenticação e integração com APIs.

**Backend (FastAPI)** – Camada de APIs REST que gerencia autenticação, conversas, ingestão de documentos e orquestração com servidor de IA.

**Servidor LLM** – Serviço separado que integra modelos de linguagem (Azure OpenAI) com regras de negócio e processamento de conhecimento.

O objetivo é garantir o entendimento completo da arquitetura, fluxos de dados, endpoints disponíveis e procedimentos de manutenção e evolução do sistema.

---

## 2. Arquitetura Geral

### 2.1 Componentes e Responsabilidades

**Frontend**
- Aplicação web (Angular/React)
- Autenticação via Azure AD/MSAL
- Interface de chat com IA
- Upload e gestão de documentos
- Visualização de dados mestres

**Backend ACE (FastAPI)**
- Porta padrão: 8000
- Autenticação com JWT
- Endpoints de conversas e chat
- Ingestão e processamento de documentos
- Gestão de dados mestres (localidades, categorias, funções)
- Proxy para servidor LLM
- Cache de sessões por usuário

**Servidor LLM**
- Serviço de IA separado
- Classificação de perguntas
- Geração segura de queries
- Processamento de linguagem natural
- Geração de insights estruturados

### 2.2 Fluxo de Autenticação

1. Usuário acessa frontend
2. Autentica via Azure AD (MSAL)
3. Backend valida token
4. JWT gerado para sessão
5. Token incluído em Authorization: Bearer {token} nas requisições

---

## 3. Documentação Técnica Disponível

A plataforma é documentada através dos seguintes arquivos técnicos:

| # | Arquivo | Descrição |
|---|---------|-----------|
| 1 | PROJECT_OVERVIEW.md | Visão geral e arquitetura do sistema |
| 2 | CHAT_API.md | API de conversas e chat com IA |
| 3 | DOCUMENT_INGESTION.md | Fluxo de ingestão de documentos |
| 4 | FRONTEND_INTEGRATION.md | Guia de integração com frontend |
| 5 | MASTER_DATA_API.md | API de dados mestres (somente leitura) |
| 6 | LLM_SERVER_ENDPOINTS.md | Endpoints do servidor de IA |
| 7 | SERVICE_USAGE_EXAMPLES.md | Exemplos práticos de uso |

Todos os arquivos estão em português e prontos para consulta.

---

## 4. Atualizações Realizadas

### 4.1 MASTER_DATA_API.md

A documentação da API de Dados Mestres foi atualizada em 02/02/2026 para refletir a arquitetura atual:

**Arquitetura:** Consulta somente leitura (GET endpoints apenas)

**Endpoints Disponíveis:** 11 endpoints GET distribuídos em 3 categorias:
- Localidades (7 endpoints)
- Categorias de Benefícios (2 endpoints)
- Funções (2 endpoints)

**Gestão de Dados:** Os dados mestres são gerenciados através de:
- Migrações de banco de dados
- Scripts administrativos
- Processos de inicialização do sistema

Esta arquitetura garante integridade de dados e reduz complexidade da API.

---

## 5. Verificação e Validação

Todos os endpoints foram verificados contra a implementação atual:

| Verificação | Status | Detalhes |
|-------------|--------|----------|
| Endpoints GET | ✅ 11 confirmados | API somente leitura |
| Estrutura de resposta | ✅ Validada | JSON padronizado |
| Autenticação | ✅ Funcionando | Azure AD + JWT |
| Cobertura de testes | ✅ 999 testes | 41% de cobertura |

---

## 6. Próximas Etapas

Para integração ou manutenção do sistema:

1. Consultar documentação específica em `/docs/` conforme necessidade técnica
2. Verificar exemplos de uso em SERVICE_USAGE_EXAMPLES.md
3. Contatar time técnico para dúvidas sobre implementação detalhada

---

**Status da Documentação:** ✅ Atualizada e alinhada com implementação atual  
**Data:** 02 de Fevereiro de 2026
