-- ============================================================
-- SQL SERVER SCHEMA - COMPLETO E ATUALIZADO
-- Consolidação de schema_sqlserver.sql + todas as migrações
-- Baseado em export do banco real + migrations
-- Data: 2026-03-13
-- ============================================================

-- ============================================================
-- TABELA: documents
-- Inclui todas as colunas (originais + migrações)
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[documents](
	[document_id] [nvarchar](36) NOT NULL,
	[title] [nvarchar](255) NOT NULL,
	[user_id] [nvarchar](255) NOT NULL,
	[min_role_level] [int] NULL,
	[allowed_countries] [nvarchar](max) NULL,
	[allowed_cities] [nvarchar](max) NULL,
	[collar] [nvarchar](255) NULL,
	[plant_code] [nvarchar](255) NULL,
	[is_active] [bit] NULL,
	[created_at] [datetime2](7) NULL,
	[updated_at] [datetime2](7) NULL,
	[category_id] [int] NULL,
	[allowed_roles] [nvarchar](max) NULL,
	[file_type] [nvarchar](10) NULL,
	[summary] [nvarchar](max) NULL,
	[user_name_masked] [nvarchar](max) NULL,
	[location_ids] [nvarchar](max) NULL,
	[addresses] [nvarchar](max) NULL,
PRIMARY KEY CLUSTERED 
(
	[document_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[documents] ADD  DEFAULT ((0)) FOR [min_role_level]
GO
ALTER TABLE [dbo].[documents] ADD  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[documents] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[documents] ADD  DEFAULT (getutcdate()) FOR [updated_at]
GO
ALTER TABLE [dbo].[documents] ADD  CONSTRAINT [DF_documents_allowed_roles]  DEFAULT (NULL) FOR [allowed_roles]
GO

-- Índices para documents
CREATE NONCLUSTERED INDEX [idx_created_at] ON [dbo].[documents]
(
	[created_at] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_documents_category] ON [dbo].[documents]
(
	[category_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_documents_user_active] ON [dbo].[documents]
(
	[user_id] ASC,
	[is_active] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_documents_user_id] ON [dbo].[documents]
(
	[user_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_file_type] ON [dbo].[documents]
(
	[file_type] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Foreign key para category
ALTER TABLE [dbo].[documents]  WITH CHECK ADD  CONSTRAINT [FK_documents_category] FOREIGN KEY([category_id])
REFERENCES [dbo].[dim_categories] ([category_id])
GO
ALTER TABLE [dbo].[documents] CHECK CONSTRAINT [FK_documents_category]
GO

PRINT 'Tabela documents criada com sucesso'
GO


-- ============================================================
-- TABELA: versions
-- Inclui todas as colunas (originais + migrações)
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[versions](
	[version_id] [nvarchar](36) NOT NULL,
	[document_id] [nvarchar](36) NOT NULL,
	[version_number] [int] NOT NULL,
	[blob_path] [nvarchar](max) NOT NULL,
	[is_active] [bit] NULL,
	[created_at] [datetime2](7) NULL,
	[file_type] [nvarchar](10) NULL,
	[filename] [nvarchar](255) NULL,
	[updated_by] [nvarchar](255) NULL,
	[updated_by_name_masked] [nvarchar](max) NULL,
PRIMARY KEY CLUSTERED 
(
	[version_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[document_id] ASC,
	[version_number] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[versions] ADD  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[versions] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO

-- Índices para versions
CREATE NONCLUSTERED INDEX [idx_active] ON [dbo].[versions]
(
	[is_active] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_document_id] ON [dbo].[versions]
(
	[document_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_versions_document_active] ON [dbo].[versions]
(
	[document_id] ASC,
	[is_active] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_versions_updated_by] ON [dbo].[versions]
(
	[updated_by] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Foreign key para document
ALTER TABLE [dbo].[versions]  WITH CHECK ADD FOREIGN KEY([document_id])
REFERENCES [dbo].[documents] ([document_id])
GO

PRINT 'Tabela versions criada com sucesso'
GO


-- ============================================================
-- TABELA: permissions
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[permissions](
	[permission_id] [nvarchar](36) NOT NULL,
	[document_id] [nvarchar](36) NOT NULL,
	[user_id] [nvarchar](255) NOT NULL,
	[can_read] [bit] NULL,
	[can_update] [bit] NULL,
	[can_delete] [bit] NULL,
	[created_at] [datetime2](7) NULL,
PRIMARY KEY CLUSTERED 
(
	[permission_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[document_id] ASC,
	[user_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[permissions] ADD  DEFAULT ((1)) FOR [can_read]
GO
ALTER TABLE [dbo].[permissions] ADD  DEFAULT ((0)) FOR [can_update]
GO
ALTER TABLE [dbo].[permissions] ADD  DEFAULT ((0)) FOR [can_delete]
GO
ALTER TABLE [dbo].[permissions] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO

-- Índices para permissions
CREATE NONCLUSTERED INDEX [idx_user_doc] ON [dbo].[permissions]
(
	[user_id] ASC,
	[document_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Foreign key para document
ALTER TABLE [dbo].[permissions]  WITH CHECK ADD FOREIGN KEY([document_id])
REFERENCES [dbo].[documents] ([document_id])
GO

PRINT 'Tabela permissions criada com sucesso'
GO


-- ============================================================
-- TABELA: temp_uploads
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[temp_uploads](
	[temp_id] [nvarchar](36) NOT NULL,
	[filename] [nvarchar](255) NOT NULL,
	[blob_path] [nvarchar](max) NOT NULL,
	[file_size_bytes] [int] NULL,
	[created_at] [datetime2](7) NULL,
	[expires_at] [datetime2](7) NULL,
	[is_confirmed] [bit] NULL,
	[user_id] [nvarchar](255) NULL,
PRIMARY KEY CLUSTERED 
(
	[temp_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[temp_uploads] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[temp_uploads] ADD  DEFAULT ((0)) FOR [is_confirmed]
GO

-- Índices para temp_uploads
CREATE NONCLUSTERED INDEX [idx_created_at] ON [dbo].[temp_uploads]
(
	[created_at] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_expires_at] ON [dbo].[temp_uploads]
(
	[expires_at] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_user_id] ON [dbo].[temp_uploads]
(
	[user_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

PRINT 'Tabela temp_uploads criada com sucesso'
GO


-- ============================================================
-- TABELA: conversations
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[conversations](
	[conversation_id] [nvarchar](36) NOT NULL,
	[user_id] [nvarchar](255) NOT NULL,
	[document_id] [int] NULL,
	[title] [nvarchar](max) NULL,
	[created_at] [datetime2](7) NULL,
	[updated_at] [datetime2](7) NULL,
	[is_active] [bit] NULL,
	[rating] [decimal](2, 1) NULL,
	[rating_timestamp] [datetime2](7) NULL,
	[rating_comment] [nvarchar](max) NULL,
	[document_category_id] [int] NULL,
PRIMARY KEY CLUSTERED 
(
	[conversation_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[conversations] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[conversations] ADD  DEFAULT (getutcdate()) FOR [updated_at]
GO
ALTER TABLE [dbo].[conversations] ADD  DEFAULT ((1)) FOR [is_active]
GO

-- Índices para conversations
CREATE NONCLUSTERED INDEX [idx_created_at] ON [dbo].[conversations]
(
	[created_at] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_document_id] ON [dbo].[conversations]
(
	[document_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_user_id] ON [dbo].[conversations]
(
	[user_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [IX_conversations_document_category_id] ON [dbo].[conversations]
(
	[document_category_id] ASC,
	[is_active] ASC
)
WHERE ([document_category_id] IS NOT NULL AND [is_active]=(1))
WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [IX_conversations_rating_comment] ON [dbo].[conversations]
(
	[rating] ASC,
	[is_active] ASC
)
WHERE ([rating] IS NOT NULL AND [rating_comment] IS NOT NULL)
WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

PRINT 'Tabela conversations criada com sucesso'
GO


-- ============================================================
-- TABELA: conversation_messages
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[conversation_messages](
	[message_id] [nvarchar](36) NOT NULL,
	[conversation_id] [nvarchar](36) NOT NULL,
	[user_id] [nvarchar](255) NOT NULL,
	[role] [nvarchar](50) NOT NULL,
	[content] [nvarchar](max) NOT NULL,
	[tokens_used] [int] NULL,
	[model] [nvarchar](100) NULL,
	[created_at] [datetime2](7) NULL,
	[retrieval_time] [float] NULL,
	[llm_time] [float] NULL,
	[total_time] [float] NULL,
	[document_categories_used] [nvarchar](max) NULL,
PRIMARY KEY CLUSTERED 
(
	[message_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[conversation_messages] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO

-- Índices para conversation_messages
CREATE NONCLUSTERED INDEX [idx_conversation_id] ON [dbo].[conversation_messages]
(
	[conversation_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_created_at] ON [dbo].[conversation_messages]
(
	[created_at] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_user_id] ON [dbo].[conversation_messages]
(
	[user_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_assistant_messages_categories] ON [dbo].[conversation_messages]
(
	[role] ASC,
	[created_at] ASC
)
WHERE ([role]='assistant' AND [document_categories_used] IS NOT NULL)
WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Foreign key para conversation
ALTER TABLE [dbo].[conversation_messages]  WITH CHECK ADD FOREIGN KEY([conversation_id])
REFERENCES [dbo].[conversations] ([conversation_id])
GO

PRINT 'Tabela conversation_messages criada com sucesso'
GO


-- ============================================================
-- TABELA: user_preferences
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[user_preferences](
	[user_id] [nvarchar](36) NOT NULL,
	[preferred_language] [nvarchar](10) NULL,
	[created_at] [datetime2](7) NULL,
	[updated_at] [datetime2](7) NULL,
	[memory_preferences] [nvarchar](max) NULL,
PRIMARY KEY CLUSTERED 
(
	[user_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

PRINT 'Tabela user_preferences criada com sucesso'
GO


-- ============================================================
-- TABELA: dim_categories
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[dim_categories](
	[category_id] [int] IDENTITY(1,1) NOT NULL,
	[category_name] [nvarchar](120) NOT NULL,
	[description] [nvarchar](500) NULL,
	[is_active] [bit] NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
	[updated_at] [datetime2](7) NOT NULL,
	[translations] [nvarchar](max) NULL,
PRIMARY KEY CLUSTERED 
(
	[category_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[dim_categories] ADD  CONSTRAINT [DF_dim_categories_is_active]  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[dim_categories] ADD  CONSTRAINT [DF_dim_categories_created_at]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[dim_categories] ADD  CONSTRAINT [DF_dim_categories_updated_at]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[dim_categories] ADD  DEFAULT ('{}') FOR [translations]
GO

CREATE UNIQUE NONCLUSTERED INDEX [UX_dim_categories_category_name] ON [dbo].[dim_categories]
(
	[category_name] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

PRINT 'Tabela dim_categories criada com sucesso'
GO


-- ============================================================
-- TABELA: dim_roles
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[dim_roles](
	[role_id] [int] IDENTITY(1,1) NOT NULL,
	[role_name] [nvarchar](120) NOT NULL,
	[is_active] [bit] NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
	[updated_at] [datetime2](7) NOT NULL,
	[translations] [nvarchar](max) NULL,
PRIMARY KEY CLUSTERED 
(
	[role_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[dim_roles] ADD  CONSTRAINT [DF_dim_roles_is_active]  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[dim_roles] ADD  CONSTRAINT [DF_dim_roles_created_at]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[dim_roles] ADD  CONSTRAINT [DF_dim_roles_updated_at]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[dim_roles] ADD  DEFAULT ('{}') FOR [translations]
GO

CREATE UNIQUE NONCLUSTERED INDEX [UX_dim_roles_role_name] ON [dbo].[dim_roles]
(
	[role_name] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

PRINT 'Tabela dim_roles criada com sucesso'
GO


-- ============================================================
-- TABELA: admins
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[admins](
	[admin_id] [nvarchar](36) NOT NULL,
	[email] [nvarchar](255) NOT NULL,
	[is_active] [bit] NULL,
	[created_at] [datetime2](7) NULL,
	[updated_at] [datetime2](7) NULL,
	[agent_id] [int] NULL,
	[name] [varchar](255) NULL,
	[job_title] [varchar](255) NULL,
	[city] [varchar](255) NULL,
	[created_by] [nvarchar](255) NULL,
	[updated_by] [nvarchar](255) NULL,
PRIMARY KEY CLUSTERED 
(
	[admin_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_admins_email_agent] UNIQUE NONCLUSTERED 
(
	[email] ASC,
	[agent_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[admins] ADD  DEFAULT (newid()) FOR [admin_id]
GO
ALTER TABLE [dbo].[admins] ADD  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[admins] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[admins] ADD  DEFAULT (getutcdate()) FOR [updated_at]
GO
ALTER TABLE [dbo].[admins] ADD  DEFAULT ((1)) FOR [agent_id]
GO

-- Índices para admins
CREATE NONCLUSTERED INDEX [idx_created_at] ON [dbo].[admins]
(
	[created_at] DESC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_email] ON [dbo].[admins]
(
	[email] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_is_active] ON [dbo].[admins]
(
	[is_active] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [IX_admins_agent_id] ON [dbo].[admins]
(
	[agent_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE UNIQUE NONCLUSTERED INDEX [UQ_admins_email_agent_active] ON [dbo].[admins]
(
	[email] ASC,
	[agent_id] ASC
)
WHERE ([is_active]=(1))
WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Foreign key para allowed_agents
ALTER TABLE [dbo].[admins]  WITH CHECK ADD  CONSTRAINT [FK_admins_agent_id] FOREIGN KEY([agent_id])
REFERENCES [dbo].[allowed_agents] ([agent_id])
GO
ALTER TABLE [dbo].[admins] CHECK CONSTRAINT [FK_admins_agent_id]
GO

PRINT 'Tabela admins criada com sucesso'
GO


-- ============================================================
-- TABELA: features
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[features](
	[feature_id] [int] IDENTITY(1,1) NOT NULL,
	[code] [nvarchar](100) NOT NULL,
	[name] [nvarchar](200) NOT NULL,
	[description] [nvarchar](500) NULL,
	[is_active] [bit] NULL,
	[created_at] [datetime2](7) NULL,
	[agente] [nvarchar](50) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[feature_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[code] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_features_agente_code] UNIQUE NONCLUSTERED 
(
	[agente] ASC,
	[code] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[features] ADD  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[features] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[features] ADD  DEFAULT ('luz') FOR [agente]
GO

PRINT 'Tabela features criada com sucesso'
GO


-- ============================================================
-- TABELA: admin_features
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[admin_features](
	[admin_id] [nvarchar](36) NOT NULL,
	[feature_id] [int] NOT NULL,
	[created_at] [datetime2](7) NULL,
PRIMARY KEY CLUSTERED 
(
	[admin_id] ASC,
	[feature_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[admin_features] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO

-- Foreign keys para admin_features
ALTER TABLE [dbo].[admin_features]  WITH CHECK ADD FOREIGN KEY([admin_id])
REFERENCES [dbo].[admins] ([admin_id])
GO

ALTER TABLE [dbo].[admin_features]  WITH CHECK ADD FOREIGN KEY([feature_id])
REFERENCES [dbo].[features] ([feature_id])
GO

PRINT 'Tabela admin_features criada com sucesso'
GO


-- ============================================================
-- TABELA: prompts
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[prompts](
	[prompt_id] [int] IDENTITY(1,1) NOT NULL,
	[agente] [nvarchar](50) NOT NULL,
	[system_prompt] [nvarchar](max) NOT NULL,
	[version] [int] NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
	[updated_at] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[prompt_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[agente] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[prompts] ADD  DEFAULT ((1)) FOR [version]
GO
ALTER TABLE [dbo].[prompts] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[prompts] ADD  DEFAULT (getutcdate()) FOR [updated_at]
GO

-- Índices para prompts
CREATE NONCLUSTERED INDEX [idx_prompts_agente] ON [dbo].[prompts]
(
	[agente] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

PRINT 'Tabela prompts criada com sucesso'
GO


-- ============================================================
-- TABELA: allowed_agents
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[allowed_agents](
	[agent_id] [int] IDENTITY(1,1) NOT NULL,
	[code] [nvarchar](50) NOT NULL,
	[name] [nvarchar](255) NOT NULL,
	[description] [nvarchar](max) NULL,
	[is_active] [bit] NULL,
	[created_at] [datetime2](7) NULL,
PRIMARY KEY CLUSTERED 
(
	[agent_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[code] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[allowed_agents] ADD  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[allowed_agents] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO

-- Inserir agentes padrão
SET IDENTITY_INSERT [dbo].[allowed_agents] ON
INSERT INTO [dbo].[allowed_agents] ([agent_id], [code], [name], [description], [is_active], [created_at])
SELECT 1, 'LUZ', 'RH e Assuntos Gerais', 'Gerenciador de assuntos de RH, dúvidas gerais e relacionamento', 1, GETUTCDATE()
WHERE NOT EXISTS (SELECT 1 FROM [dbo].[allowed_agents] WHERE [code] = 'LUZ');

INSERT INTO [dbo].[allowed_agents] ([agent_id], [code], [name], [description], [is_active], [created_at])
SELECT 2, 'IGP', 'IGP', 'Gerenciador IGP (a ser definido)', 1, GETUTCDATE()
WHERE NOT EXISTS (SELECT 1 FROM [dbo].[allowed_agents] WHERE [code] = 'IGP');

INSERT INTO [dbo].[allowed_agents] ([agent_id], [code], [name], [description], [is_active], [created_at])
SELECT 3, 'SMART', 'Smart', 'Gerenciador Smart (a ser definido)', 1, GETUTCDATE()
WHERE NOT EXISTS (SELECT 1 FROM [dbo].[allowed_agents] WHERE [code] = 'SMART');

SET IDENTITY_INSERT [dbo].[allowed_agents] OFF
GO

PRINT 'Tabela allowed_agents criada com sucesso'
GO


-- ============================================================
-- TABELA: admin_audit_log
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[admin_audit_log](
	[log_id] [bigint] IDENTITY(1,1) NOT NULL,
	[admin_id] [nvarchar](36) NOT NULL,
	[action] [nvarchar](50) NOT NULL,
	[changed_fields] [nvarchar](max) NULL,
	[old_values] [nvarchar](max) NULL,
	[new_values] [nvarchar](max) NOT NULL,
	[changed_by] [nvarchar](255) NOT NULL,
	[changed_at] [datetime2](7) NULL,
	[ip_address] [nvarchar](45) NULL,
	[details] [nvarchar](max) NULL,
PRIMARY KEY CLUSTERED 
(
	[log_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[admin_audit_log] ADD  DEFAULT (getutcdate()) FOR [changed_at]
GO

-- Índices para admin_audit_log
CREATE NONCLUSTERED INDEX [idx_action] ON [dbo].[admin_audit_log]
(
	[action] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_admin_audit_log_composite] ON [dbo].[admin_audit_log]
(
	[admin_id] ASC,
	[changed_at] DESC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_admin_id] ON [dbo].[admin_audit_log]
(
	[admin_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_changed_at] ON [dbo].[admin_audit_log]
(
	[changed_at] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Foreign key para admin
ALTER TABLE [dbo].[admin_audit_log]  WITH CHECK ADD FOREIGN KEY([admin_id])
REFERENCES [dbo].[admins] ([admin_id])
GO

ALTER TABLE [dbo].[admin_audit_log]  WITH CHECK ADD  CONSTRAINT [FK_admin_aud_admin_preserve] FOREIGN KEY([admin_id])
REFERENCES [dbo].[admins] ([admin_id])
GO
ALTER TABLE [dbo].[admin_audit_log] CHECK CONSTRAINT [FK_admin_aud_admin_preserve]
GO

PRINT 'Tabela admin_audit_log criada com sucesso'
GO


-- ============================================================
-- TABELA: dim_job_title_roles
-- ============================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[dim_job_title_roles](
	[job_title_role_id] [int] IDENTITY(1,1) NOT NULL,
	[job_title] [nvarchar](255) NOT NULL,
	[role] [nvarchar](100) NOT NULL,
	[is_active] [bit] NULL,
	[created_at] [datetime2](7) NULL,
	[updated_at] [datetime2](7) NULL,
	[role_id] [int] NULL,
PRIMARY KEY CLUSTERED 
(
	[job_title_role_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[job_title] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[dim_job_title_roles] ADD  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[dim_job_title_roles] ADD  DEFAULT (getutcdate()) FOR [created_at]
GO
ALTER TABLE [dbo].[dim_job_title_roles] ADD  DEFAULT (getutcdate()) FOR [updated_at]
GO

-- Índices para dim_job_title_roles
CREATE NONCLUSTERED INDEX [idx_job_title] ON [dbo].[dim_job_title_roles]
(
	[job_title] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

CREATE NONCLUSTERED INDEX [idx_role] ON [dbo].[dim_job_title_roles]
(
	[role] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Foreign key para dim_roles (quando role_id estiver preenchido)
ALTER TABLE [dbo].[dim_job_title_roles]  WITH NOCHECK ADD  CONSTRAINT [FK_job_title_roles_dim_roles] FOREIGN KEY([role_id])
REFERENCES [dbo].[dim_roles] ([role_id])
GO
ALTER TABLE [dbo].[dim_job_title_roles] CHECK CONSTRAINT [FK_job_title_roles_dim_roles]
GO

-- Inserir dados padrão
SET IDENTITY_INSERT [dbo].[dim_job_title_roles] ON
INSERT INTO [dbo].[dim_job_title_roles] ([job_title_role_id], [job_title], [role], [is_active], [created_at], [updated_at])
SELECT 1, 'SVP Corporate Communications', 'Vice-Presidente', 1, GETUTCDATE(), GETUTCDATE()
WHERE NOT EXISTS (SELECT 1 FROM [dbo].[dim_job_title_roles] WHERE [job_title] = 'SVP Corporate Communications');

INSERT INTO [dbo].[dim_job_title_roles] ([job_title_role_id], [job_title], [role], [is_active], [created_at], [updated_at])
SELECT 2, 'SVP Global Product Line Care', 'Vice-Presidente', 1, GETUTCDATE(), GETUTCDATE()
WHERE NOT EXISTS (SELECT 1 FROM [dbo].[dim_job_title_roles] WHERE [job_title] = 'SVP Global Product Line Care');

INSERT INTO [dbo].[dim_job_title_roles] ([job_title_role_id], [job_title], [role], [is_active], [created_at], [updated_at])
SELECT 3, 'SVP, Global Retail Sales', 'Vice-Presidente', 1, GETUTCDATE(), GETUTCDATE()
WHERE NOT EXISTS (SELECT 1 FROM [dbo].[dim_job_title_roles] WHERE [job_title] = 'SVP, Global Retail Sales');

INSERT INTO [dbo].[dim_job_title_roles] ([job_title_role_id], [job_title], [role], [is_active], [created_at], [updated_at])
SELECT 4, 'SVP, Marketing & CDI', 'Vice-Presidente', 1, GETUTCDATE(), GETUTCDATE()
WHERE NOT EXISTS (SELECT 1 FROM [dbo].[dim_job_title_roles] WHERE [job_title] = 'SVP, Marketing & CDI');

INSERT INTO [dbo].[dim_job_title_roles] ([job_title_role_id], [job_title], [role], [is_active], [created_at], [updated_at])
SELECT 5, 'SVP, Sales BA North America', 'Vice-Presidente', 1, GETUTCDATE(), GETUTCDATE()
WHERE NOT EXISTS (SELECT 1 FROM [dbo].[dim_job_title_roles] WHERE [job_title] = 'SVP, Sales BA North America');

INSERT INTO [dbo].[dim_job_title_roles] ([job_title_role_id], [job_title], [role], [is_active], [created_at], [updated_at])
SELECT 6, 'VP & General Counsel', 'Vice-Presidente', 1, GETUTCDATE(), GETUTCDATE()
WHERE NOT EXISTS (SELECT 1 FROM [dbo].[dim_job_title_roles] WHERE [job_title] = 'VP & General Counsel');

INSERT INTO [dbo].[dim_job_title_roles] ([job_title_role_id], [job_title], [role], [is_active], [created_at], [updated_at])
SELECT 7, 'VP Brand & Consumer Insights', 'Vice-Presidente', 1, GETUTCDATE(), GETUTCDATE()
WHERE NOT EXISTS (SELECT 1 FROM [dbo].[dim_job_title_roles] WHERE [job_title] = 'VP Brand & Consumer Insights');
SET IDENTITY_INSERT [dbo].[dim_job_title_roles] OFF
GO

PRINT 'Tabela dim_job_title_roles criada com sucesso'
GO

-- ============================================================
-- RESUMO FINAL
-- ============================================================
PRINT '';
PRINT '========================================================';
PRINT 'SCHEMA SQLSERVER COMPLETO E ATUALIZADO!';
PRINT '========================================================';
PRINT '';
PRINT 'Tabelas de Documentos:';
PRINT '  ✓ documents (principais registros de documentos)';
PRINT '  ✓ versions (histórico de versões de documentos)';
PRINT '  ✓ permissions (controle de acesso)';
PRINT '  ✓ temp_uploads (upload temporário)';
PRINT '';
PRINT 'Tabelas de Conversas:';
PRINT '  ✓ conversations (conversas com IA)';
PRINT '  ✓ conversation_messages (mensagens individuais)';
PRINT '';
PRINT 'Tabelas de Configuração:';
PRINT '  ✓ dim_categories (categorias de documentos)';
PRINT '  ✓ dim_roles (papéis/funções de acesso)';
PRINT '  ✓ dim_job_title_roles (mapeamento JobTitle→Role)';
PRINT '  ✓ user_preferences (preferências do usuário)';
PRINT '  ✓ allowed_agents (agentes/IAs: LUZ, IGP, SMART)';
PRINT '';
PRINT 'Tabelas de Administração:';
PRINT '  ✓ admins (usuários administradores)';
PRINT '  ✓ admin_features (features habilitadas por admin)';
PRINT '  ✓ features (features disponíveis do sistema)';
PRINT '  ✓ admin_audit_log (auditoria de alterações)';
PRINT '  ✓ prompts (prompts do sistema por agente)';
PRINT '';
PRINT 'Colunas Consolidadas de Todas as Migrações:';
PRINT '  - documents: location_ids, summary, allowed_roles, addresses, user_name_masked, file_type, category_id';
PRINT '  - versions: filename, updated_by, updated_by_name_masked, file_type';
PRINT '  - conversations: rating_comment, document_category_id';
PRINT '  - conversation_messages: retrieval_time, llm_time, total_time, document_categories_used';
PRINT '  - user_preferences: memory_preferences, updated_at';
PRINT '';
PRINT 'Índices Otimizados Para Performance:';
PRINT '  - Índices compostos para queries principais';
PRINT '  - Índices filtrados para is_active = 1';
PRINT '  - Índices únicos para integridade de dados';
PRINT '';
PRINT '✅ Schema pronto para PRODUÇÃO!';
PRINT '========================================================';
PRINT '';
GO
