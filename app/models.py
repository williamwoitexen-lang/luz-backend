from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json

class SearchResultItem(BaseModel):
    title: str
    version_number: int
    chunk_index: int
    content: str
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResultItem]


# ==== Models para Conversas ====

class QuestionRequest(BaseModel):
    """Requisição de pergunta do usuário ao LLM Server."""
    chat_id: str
    question: str
    user_id: str
    name: str
    email: str
    country: str = "Brazil"
    city: str = ""
    street: str = Field(
        default="",
        description="Endereço/rua (será convertido em location_id via tabela dim_electrolux_locations)"
    )
    role_id: int = 1
    department: str = ""
    job_title: str = ""
    collar: str = ""
    unit: str = ""
    agent_id: int = Field(
        default=1,
        description="ID do agente/IA a usar. 1=LUZ (padrão), 2=IGP, 3=SMART"
    )
    memory_preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Preferências de memória do usuário (se não fornecidas, será buscadas automaticamente na primeira msg)"
    )
    memory: Optional[str] = Field(
        default=None,
        description="Descrição textual de memory para o LLM (ex: 'Preferir respostas concisas')"
    )
    memory_version: int = Field(
        default=1,
        description="Versão do memory (padrão: 1)"
    )
    language: str = Field(
        default="",
        description="Idioma da conversa (ex: pt, en, es). Vazio se não especificado"
    )
    location_id: Optional[Union[str, int]] = Field(
        default=None,
        description="ID da localização (será convertido para int no backend)"
    )
    
    @field_validator('memory_preferences', mode='before')
    def validate_memory_preferences(cls, v):
        """Converte string vazia em None, valida tipo como dict ou None"""
        if v == "" or v == "{}" or v == "[]":
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v) if v else None
                return parsed if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, TypeError):
                return None
        if isinstance(v, dict):
            return v if v else None
        return None


class ConversationMessageResponse(BaseModel):
    """Resposta de uma mensagem de conversa."""
    message_id: str
    conversation_id: str
    role: str  # 'user' ou 'assistant'
    content: str
    model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    created_at: datetime


class QuestionResponse(BaseModel):
    """Resposta completa da pergunta ao LLM Server."""
    conversation_id: str
    answer: str
    source_documents: List[Dict[str, Any]] = []
    num_documents: int = 0
    classification: Optional[Dict[str, Any]] = None
    retrieval_time: float = 0.0
    llm_time: float = 0.0
    total_time: float = 0.0
    total_time_ms: int = 0
    message_id: str
    provider: str = "azure_openai"
    model: str = "gpt-4o-mini"
    generated_at: datetime
    rbac_filter_applied: Optional[str] = None
    documents_returned: int = 0
    documents_filtered: int = 0
    top_sources: List[str] = []
    agente: str = "general"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    node_path: Optional[List[str]] = None


class ChatMessage(BaseModel):
    """Mensagem de conversa a ser salva."""
    conversation_id: str
    user_id: str
    role: str  # 'user' ou 'assistant'
    content: str
    model: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class ConversationCreate(BaseModel):
    """Criação de nova conversa."""
    user_id: str
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Resposta de uma conversa."""
    conversation_id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    message_count: int = 0


class ConversationDetail(BaseModel):
    """Detalhe completo de uma conversa com mensagens."""
    conversation_id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    rating: Optional[float] = None  # 0.0 a 5.0
    rating_timestamp: Optional[datetime] = None
    messages: List[ConversationMessageResponse] = []


class RatingRequest(BaseModel):
    """Requisição para avaliar uma conversa."""
    rating: float  # 0.0 a 5.0 (com meia: 0.0, 0.5, 1.0, 1.5, ...)
    comment: Optional[str] = Field(
        None,
        max_length=2000,
        description="Comentário/feedback. OBRIGATÓRIO quando rating=1.0"
    )
    
    @field_validator('comment')
    @classmethod
    def validate_comment(cls, v: Optional[str], info) -> Optional[str]:
        """Validar que comentário é obrigatório quando rating=1.0"""
        rating = info.data.get('rating')
        
        # Se rating for 1.0, comentário é obrigatório
        if rating == 1.0:
            if not v or not v.strip():
                raise ValueError("Comentário é obrigatório quando rating é 1.0 (muito insatisfeito)")
            if len(v.strip()) < 10:
                raise ValueError("Comentário deve ter no mínimo 10 caracteres")
        
        # Se houver comentário, limpar espaços extras
        if v:
            return v.strip()
        return None
    
    class Config:
        json_schema_extra = {
            "example": {
                "rating": 4.5,
                "comment": "Resposta muito útil e bem estruturada"
            },
            "example_low_rating": {
                "rating": 1.0,
                "comment": "A resposta não foi relevante para minha pergunta sobre benefícios de saúde"
            }
        }


class RatingResponse(BaseModel):
    """Resposta simples de sucesso da avaliação."""
    conversation_id: str
    rating: float
    comment: Optional[str] = None
    message: str = "Avaliação salva com sucesso"


# ==== Models para Admins ====

class FeatureDetail(BaseModel):
    """Detalhes de uma feature"""
    feature_id: int = Field(..., description="ID da feature")
    agente: str = Field(..., description="Agente/tipo de ferramenta")
    code: str = Field(..., description="Código da feature")
    name: str = Field(..., description="Nome da feature")
    description: Optional[str] = Field(None, description="Descrição da feature")
    is_active: bool = Field(default=True, description="Se feature está ativa")
    created_at: datetime = Field(..., description="Data de criação")


class AdminBase(BaseModel):
    """Base model para admin"""
    email: str = Field(..., description="Email do admin")
    name: Optional[str] = Field(None, description="Nome completo do colaborador")
    job_title: Optional[str] = Field(None, description="Cargo do colaborador")
    city: Optional[str] = Field(None, description="Cidade para desambiguar colaboradores com mesmo nome")
    agent_id: int = Field(default=1, description="ID do agente (1=LUZ, 2=IGP, 3=SMART)")
    feature_ids: List[int] = Field(default=[], description="IDs das features permitidas")


class AdminCreate(AdminBase):
    """Request para criar admin"""
    pass


class AdminUpdate(BaseModel):
    """Request para atualizar admin"""
    name: Optional[str] = Field(None, description="Nome completo do colaborador")
    job_title: Optional[str] = Field(None, description="Cargo do colaborador")
    city: Optional[str] = Field(None, description="Cidade do colaborador")
    agent_id: Optional[int] = Field(None, description="ID do agente (1=LUZ, 2=IGP, 3=SMART)")
    feature_ids: Optional[List[int]] = Field(None, description="IDs das features permitidas")


class AdminResponse(BaseModel):
    """Response de admin com features detalhadas"""
    admin_id: str = Field(..., description="ID único do admin")
    email: str = Field(..., description="Email do admin")
    name: Optional[str] = Field(None, description="Nome completo do colaborador")
    job_title: Optional[str] = Field(None, description="Cargo do colaborador")
    city: Optional[str] = Field(None, description="Cidade para desambiguar")
    agent_id: int = Field(..., description="ID do agente (1=LUZ, 2=IGP, 3=SMART)")
    agent_name: str = Field(..., description="Nome do agente (LUZ, IGP, SMART)")
    is_active: bool = Field(default=True, description="Se admin está ativo")
    features: List[FeatureDetail] = Field(default=[], description="Features que o admin tem acesso")
    created_at: datetime = Field(..., description="Data de criação")
    created_by: Optional[str] = Field(None, description="Nome do usuário que criou")
    updated_at: Optional[datetime] = Field(None, description="Data de atualização")
    updated_by: Optional[str] = Field(None, description="Nome do usuário que atualizou")
    
    class Config:
        from_attributes = True


class AdminAuditLogEntry(BaseModel):
    """Entrada de um log de auditoria de admin"""
    log_id: int = Field(..., description="ID único do registro de auditoria")
    admin_id: str = Field(..., description="ID do admin alterado")
    action: str = Field(..., description="CREATE, UPDATE ou DELETE")
    changed_fields: List[str] = Field(default=[], description="Lista de campos que mudaram")
    old_values: Dict[str, Any] = Field(default={}, description="Valores antigos (antes da alteração)")
    new_values: Dict[str, Any] = Field(..., description="Valores novos (depois da alteração)")
    changed_by: str = Field(..., description="Nome do usuário que fez a alteração")
    changed_at: datetime = Field(..., description="Data e hora da alteração")
    ip_address: Optional[str] = Field(None, description="IP do cliente")
    details: Optional[str] = Field(None, description="Descrição adicional da alteração")


class AdminAuditLogResponse(BaseModel):
    """Response com histórico de auditoria de um admin"""
    admin_id: str = Field(..., description="ID do admin")
    logs: List[AdminAuditLogEntry] = Field(default=[], description="Lista de registros de auditoria")
    total: int = Field(..., description="Total de registros de auditoria")


class AdminListResponse(BaseModel):
    """Response de lista de admins"""
    admins: List[AdminResponse]
    total: int = Field(..., description="Total de admins")


# ==== Models para Prompts ====

class AgenteDetail(BaseModel):
    """Detalhes de um agente permitido"""
    agent_id: int = Field(..., description="ID do agente")
    code: str = Field(..., description="Código do agente (LUZ, IGP, SMART)")
    name: str = Field(..., description="Nome do agente")
    description: Optional[str] = Field(None, description="Descrição do agente")
    is_active: bool = Field(default=True, description="Se agente está ativo")


class PromptBase(BaseModel):
    """Base para Prompt"""
    system_prompt: str = Field(..., description="Texto do system prompt para o LLM")


class PromptCreate(PromptBase):
    """Request de criação de prompt"""
    agente: str = Field(..., description="Agente (luz, agua, energia, etc)")


class PromptUpdate(PromptBase):
    """Request de atualização de prompt"""
    pass


class PromptResponse(PromptBase):
    """Response de prompt"""
    prompt_id: int = Field(..., description="ID do prompt")
    agente: str = Field(..., description="Agente")
    version: int = Field(default=1, description="Versão do prompt")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: Optional[datetime] = Field(None, description="Data de atualização")
    
    class Config:
        from_attributes = True