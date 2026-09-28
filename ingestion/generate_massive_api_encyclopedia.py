#!/usr/bin/env python3
"""
generate_massive_api_encyclopedia.py
Genera una enciclopedia masiva y exhaustiva de APIs, arquitecturas de software,
patrones de sistemas y conceptos técnicos modernos, integrándolos al grafo de ~/.hermes-hub.
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
GRAPH_FILE = CONFIG_DIR / "graph.json"

APIS_DIR = HUB_ROOT / "apis"
PATTERNS_DIR = HUB_ROOT / "patterns"
CONCEPTS_DIR = HUB_ROOT / "concepts"
STRUCTURES_DIR = HUB_ROOT / "structures"

for d in [APIS_DIR, PATTERNS_DIR, CONCEPTS_DIR, STRUCTURES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------
# DEFINICIONES EXHAUSTIVAS DE APIS Y ARQUITECTURAS
# -------------------------------------------------------------

ITEMS = [
    # =========================================================
    # 1. AI & LLM APIS
    # =========================================================
    {
        "id": "api_openai_platform",
        "category": "apis/ai",
        "type": "api",
        "cluster": "cluster_ai_apis",
        "title": "OpenAI API Platform (Chat, Realtime, Assistants, Embeddings)",
        "keywords": ["openai", "chatgpt", "gpt-4o", "realtime", "assistants", "embeddings", "batch", "tokenization"],
        "content": """---
id: api_openai_platform
title: OpenAI API Platform Reference & Implementation
type: api
cluster: cluster_ai_apis
category: ai_models
keywords: [openai, chatgpt, gpt-4o, realtime, assistants, embeddings, batch, tokenization]
auth_type: Bearer Token (HTTP Authorization Header)
base_url: https://api.openai.com/v1
---

# OpenAI API Platform Reference

## 📌 Visión General
La API de OpenAI proporciona acceso a modelos de lenguaje multimodal (`gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini`), generación de embeddings vectoriales (`text-embedding-3-small/large`), procesamiento de audio en tiempo real vía WebSockets/WebRTC (Realtime API), y asistentes persistentes con recuperación de contexto (Assistants API v2).

---

## 🔐 Autenticación y Headers
```http
Authorization: Bearer YOUR_OPENAI_API_KEY
OpenAI-Organization: org-xxxxxxxxxxxxxxxx
OpenAI-Project: proj-xxxxxxxxxxxxxxxx
Content-Type: application/json
```

---

## ⚡ Endpoints Principales

### 1. Chat Completions & Structured Outputs
- **POST** `/v1/chat/completions`
- **Soporte JSON Schema Estricto (`strict: true`)** para forzar salidas que cumplan un esquema Pydantic/JSON Schema exacto.

#### Ejemplo Payload JSON:
```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "Eres un asistente técnico especializado."},
    {"role": "user", "content": "Analiza la arquitectura del sistema."}
  ],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "system_analysis",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "bottlenecks": {"type": "array", "items": {"type": "string"}},
          "latency_ms": {"type": "number"},
          "recommendation": {"type": "string"}
        },
        "required": ["bottlenecks", "latency_ms", "recommendation"],
        "additionalProperties": false
      }
    }
  },
  "temperature": 0.2
}
```

### 2. Embeddings Vectoriales
- **POST** `/v1/embeddings`
- **Modelos**: `text-embedding-3-small` (1536 dims), `text-embedding-3-large` (3072 dims con soporte para reducción dimensional `dimensions: 1024`).

### 3. Realtime API (Baja Latencia de Audio / Voz)
- Conexión vía WebSocket: `wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview`
- Eventos: `session.update`, `input_audio_buffer.append`, `response.create`.

---

## 🐍 Implementación en Python (Async Client)
```python
import os
import asyncio
from openai import AsyncOpenAI
from pydantic import BaseModel

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class AnalysisResult(BaseModel):
    summary: str
    confidence_score: float
    action_items: list[str]

async def analyze_text(prompt: str) -> AnalysisResult:
    completion = await client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "Extrae el plan de acción estructurado."},
            {"role": "user", "content": prompt}
        ],
        response_format=AnalysisResult
    )
    return completion.choices[0].message.parsed
```
"""
    },
    {
        "id": "api_anthropic_claude",
        "category": "apis/ai",
        "type": "api",
        "cluster": "cluster_ai_apis",
        "title": "Anthropic Claude API (Messages, Tool Use, Prompt Caching, Reasoning)",
        "keywords": ["anthropic", "claude", "claude-3-7-sonnet", "prompt_caching", "tool_use", "reasoning", "tokens"],
        "content": """---
id: api_anthropic_claude
title: Anthropic Claude Messages API & Prompt Caching
type: api
cluster: cluster_ai_apis
category: ai_models
keywords: [anthropic, claude, claude-3-7-sonnet, prompt_caching, tool_use, reasoning, tokens]
auth_type: X-Api-Key Header
base_url: https://api.anthropic.com/v1
---

# Anthropic Claude API Reference

## 📌 Visión General
La API de Anthropic Messages (`/v1/messages`) ofrece soporte de ventana de contexto de 200k tokens, **Prompt Caching** (reducción del 90% de coste y 80% de latencia en prefijos repetidos), **Tool Use / Function Calling** con esquemas de validación estricta y capacidad de razonamiento profundo continuo (*Extended Thinking* en Claude 3.7 Sonnet).

---

## 🔐 Headers Obligatorios
```http
x-api-key: YOUR_ANTHROPIC_API_KEY
anthropic-version: 2023-06-01
anthropic-beta: prompt-caching-2024-07-31,output-128k-2025-02-19
Content-Type: application/json
```

---

## ⚡ Prompt Caching & Tool Use Payload
```json
{
  "model": "claude-3-7-sonnet-20250219",
  "max_tokens": 4096,
  "system": [
    {
      "type": "text",
      "text": "Eres un asistente de arquitectura de software con acceso al código del proyecto...",
      "cache_control": {"type": "ephemeral"}
    }
  ],
  "tools": [
    {
      "name": "query_database",
      "description": "Ejecuta una consulta SQL en modo de solo lectura",
      "input_schema": {
        "type": "object",
        "properties": {
          "sql_query": {"type": "string", "description": "Query SQL SELECT"}
        },
        "required": ["sql_query"]
      }
    }
  ],
  "messages": [
    {"role": "user", "content": "Verifica las órdenes pendientes en PostgreSQL."}
  ]
}
```

---

## 🐍 Implementación en Python con Streaming
```python
import os
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

async def stream_claude_response(prompt: str):
    async with client.messages.stream(
        model="claude-3-7-sonnet-20250219",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        async for text in stream.text_stream:
            print(text, end="", flush=True)
```
"""
    },
    {
        "id": "api_google_gemini",
        "category": "apis/ai",
        "type": "api",
        "cluster": "cluster_ai_apis",
        "title": "Google Gemini API & Vertex AI (GenerateContent, Multimodal Live, Code Execution)",
        "keywords": ["gemini", "google_ai", "gemini-2.0-flash", "multimodal", "code_execution", "structured_outputs"],
        "content": """---
id: api_google_gemini
title: Google Gemini API & Multimodal Capabilities
type: api
cluster: cluster_ai_apis
category: ai_models
keywords: [gemini, google_ai, gemini-2.0-flash, multimodal, code_execution, structured_outputs]
auth_type: API Key Query Param or Bearer Token (OAuth2 via gcloud)
base_url: https://generativelanguage.googleapis.com/v1beta
---

# Google Gemini API Reference

## 📌 Visión General
La API de Google Gemini (Gemini 2.0 Flash / Pro, Gemini 1.5 Pro) ofrece ventanas de contexto de hasta 2 millones de tokens, soporte nativo multimodal (texto, imágenes, video, audio y PDF), ejecución automática de código Python en sandbox, llamadas a herramientas (*Function Calling*) y APIs de voz/video en tiempo real con latencias inferiores a 300ms (*Multimodal Live API* vía WebSockets).

---

## ⚡ Endpoints Principales
- **POST** `/v1beta/models/{model}:generateContent?key={API_KEY}`
- **POST** `/v1beta/models/{model}:streamGenerateContent?key={API_KEY}`
- **POST** `/v1beta/models/{model}:countTokens?key={API_KEY}`
- **POST** `/v1beta/cachedContents` (Context Caching persistente)

---

## 🐍 Implementación en Python con SDK `google-genai`
```python
import os
from google import genai
from google.genai import types
from pydantic import BaseModel

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class TechnicalSpec(BaseModel):
    architecture_name: str
    scalability_grade: str
    estimated_monthly_cost_usd: float

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Diseña una arquitectura serverless en GCP con Cloud Run y Firestore.',
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=TechnicalSpec,
        temperature=0.1
    )
)

print(response.text)
```
"""
    },
    {
        "id": "api_groq_cloud",
        "category": "apis/ai",
        "type": "api",
        "cluster": "cluster_ai_apis",
        "title": "Groq Cloud API (LPU Inference Engine for Llama 3, DeepSeek & Mixtral)",
        "keywords": ["groq", "lpu", "ultra_fast_inference", "llama3", "deepseek", "low_latency"],
        "content": """---
id: api_groq_cloud
title: Groq Cloud LPU Ultra-Fast Inference API
type: api
cluster: cluster_ai_apis
category: ai_models
keywords: [groq, lpu, ultra_fast_inference, llama3, deepseek, low_latency]
auth_type: Bearer Token
base_url: https://api.groq.com/openai/v1
---

# Groq Cloud API Reference

## 📌 Visión General
Groq utiliza chips propietarios LPU (Language Processing Unit) de arquitectura basada en SRAM tensorial que alcanzan velocidades de generación de tokens superiores a **300 - 800 tokens/segundo** con latencias al primer token (TTFT) inferiores a 100ms. Es 100% compatible con la especificación de OpenAI Chat Completions.

---

## ⚡ Ejemplo de Inferencia Ultra Rápida con Python
```python
import os
from groq import AsyncGroq

client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

async def fast_agent_decision(prompt: str) -> str:
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Toma decisiones tácticas en <50ms."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=500
    )
    return response.choices[0].message.content
```
"""
    },
    {
        "id": "api_deepseek_platform",
        "category": "apis/ai",
        "type": "api",
        "cluster": "cluster_ai_apis",
        "title": "DeepSeek API (DeepSeek-V3 & DeepSeek-R1 Reasoning Tokens)",
        "keywords": ["deepseek", "deepseek-r1", "deepseek-v3", "chain_of_thought", "reasoning", "cost_efficient"],
        "content": """---
id: api_deepseek_platform
title: DeepSeek API (V3 & R1 Reasoning Engine)
type: api
cluster: cluster_ai_apis
category: ai_models
keywords: [deepseek, deepseek-r1, deepseek-v3, chain_of_thought, reasoning, cost_efficient]
auth_type: Bearer Token
base_url: https://api.deepseek.com/v1
---

# DeepSeek API Reference

## 📌 Visión General
La API de DeepSeek proporciona acceso a `deepseek-chat` (DeepSeek-V3 MoE) y `deepseek-reasoner` (DeepSeek-R1). Expone el campo `reasoning_content` en streaming para inspeccionar el flujo de pensamiento paso a paso (*Chain of Thought*) antes del output final. Cuenta con un sistema automático de descuento por *Cache Hit* de contexto.

---

## ⚡ Manejo de Reasoning Tokens en Python
```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[{"role": "user", "content": "Resuelve la optimización de grafos NP-hard."}],
    stream=True
)

for chunk in response:
    delta = chunk.choices[0].delta
    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
        print(f"[Pensamiento]: {delta.reasoning_content}", end="", flush=True)
    elif delta.content:
        print(delta.content, end="", flush=True)
```
"""
    },

    # =========================================================
    # 2. FINTECH, PAYMENTS & BILLING APIS
    # =========================================================
    {
        "id": "api_stripe_platform",
        "category": "apis/fintech",
        "type": "api",
        "cluster": "cluster_fintech_apis",
        "title": "Stripe API Platform (PaymentIntents, Subscriptions, Webhooks, Connect)",
        "keywords": ["stripe", "payment_intents", "webhooks", "subscriptions", "idempotency", "connect", "checkout"],
        "content": """---
id: api_stripe_platform
title: Stripe Payments, Billing & Webhooks API Reference
type: api
cluster: cluster_fintech_apis
category: payments
keywords: [stripe, payment_intents, webhooks, subscriptions, idempotency, connect, checkout]
auth_type: Bearer Secret Key (HTTP Basic / Bearer)
base_url: https://api.stripe.com/v1
---

# Stripe API Platform Reference

## 📌 Visión General
Stripe es el estándar de la industria para procesamiento de pagos globales, suscripciones SaaS recurrentes, facturación y plataformas multi-vendedor (*Stripe Connect*).

---

## ⚡ Patrones Críticos de Integración

### 1. Idempotency Keys (Prevención de Cobros Duplicados)
Cualquier petición `POST` debe incluir la cabecera `Idempotency-Key: <UUID>` para asegurar que reintentos de red no ejecuten transacciones dobles.

### 2. Validación Criptográfica de Webhooks
Los eventos de webhook (`payment_intent.succeeded`, `invoice.payment_failed`) deben ser validados mediante la cabecera `Stripe-Signature` y el `endpoint_secret` para evitar ataques de suplantación.

---

## 🐍 Implementación Completa en FastAPI & Python
```python
import os
import stripe
from fastapi import FastAPI, Request, HTTPException, Header

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

app = FastAPI()

@app.post("/api/create-payment-intent")
async def create_payment(amount_cents: int, currency: str = "usd"):
    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency,
        automatic_payment_methods={"enabled": True},
        idempotency_key=f"order_{os.urandom(8).hex()}"
    )
    return {"clientSecret": intent.client_secret}

@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {e}")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        print(f"💰 Pago recibido exitosamente: {payment_intent['id']}")

    return {"status": "success"}
```
"""
    },
    {
        "id": "api_mercadopago_platform",
        "category": "apis/fintech",
        "type": "api",
        "cluster": "cluster_fintech_apis",
        "title": "Mercado Pago API (Checkout Pro, Preference, Pix & Webhooks v2)",
        "keywords": ["mercadopago", "checkout_pro", "pix", "webhooks", "tarjetas", "ipn", "latam_payments"],
        "content": """---
id: api_mercadopago_platform
title: Mercado Pago API & Checkout Pro Integration
type: api
cluster: cluster_fintech_apis
category: payments
keywords: [mercadopago, checkout_pro, pix, webhooks, tarjetas, ipn, latam_payments]
auth_type: Bearer Access Token
base_url: https://api.mercadopago.com
---

# Mercado Pago API Reference

## 📌 Visión General
Mercado Pago es el principal procesador de pagos de América Latina (Brasil, México, Argentina, Chile, Colombia, Perú, Uruguay). Soporta Checkout Pro (redirección alojada), Checkout Transparente (tarjetas de crédito/débito en frontend propio), Pix en tiempo real y Débito Automático.

---

## ⚡ Creación de Preferencia en Python
```python
import os
import mercadopago

sdk = mercadopago.SDK(os.environ.get("MP_ACCESS_TOKEN"))

def create_checkout_preference(item_title: str, price: float, quantity: int = 1):
    preference_data = {
        "items": [
            {
                "title": item_title,
                "quantity": quantity,
                "unit_price": price,
                "currency_id": "ARS"
            }
        ],
        "back_urls": {
            "success": "https://misuperapp.com/checkout/success",
            "failure": "https://misuperapp.com/checkout/failure",
            "pending": "https://misuperapp.com/checkout/pending"
        },
        "auto_return": "approved",
        "notification_url": "https://misuperapp.com/api/webhooks/mercadopago"
    }
    
    preference_response = sdk.preference().create(preference_data)
    return preference_response["response"]["init_point"]
```
"""
    },
    {
        "id": "api_plaid_financial",
        "category": "apis/fintech",
        "type": "api",
        "cluster": "cluster_fintech_apis",
        "title": "Plaid Financial API (Link, Auth, Transactions Sync & Identity)",
        "keywords": ["plaid", "open_banking", "transactions_sync", "link_token", "bank_account", "ach"],
        "content": """---
id: api_plaid_financial
title: Plaid Open Banking & Financial Data API
type: api
cluster: cluster_fintech_apis
category: fintech
keywords: [plaid, open_banking, transactions_sync, link_token, bank_account, ach]
auth_type: Client ID & Secret in Body or Headers (PLAID-CLIENT-ID, PLAID-SECRET)
base_url: https://production.plaid.com
---

# Plaid Financial API Reference

## 📌 Visión General
Plaid conecta aplicaciones con más de 12,000 instituciones bancarias. Permite autenticar cuentas para transferencias ACH (`/auth/get`), sincronizar transacciones en tiempo real con cursores (`/transactions/sync`), y verificar identidades de usuarios (`/identity/get`).

---

## ⚡ Flujo de Conexión: Link Token ➔ Public Token ➔ Access Token
1. El backend solicita un `link_token` a `/link/token/create`.
2. El usuario inicia sesión en su banco a través del widget Plaid Link y devuelve un `public_token`.
3. El backend intercambia el `public_token` por un `access_token` persistente en `/item/public_token/exchange`.
"""
    },

    # =========================================================
    # 3. AUTHENTICATION & IDENTITY APIS
    # =========================================================
    {
        "id": "api_oauth2_oidc_spec",
        "category": "apis/auth",
        "type": "api",
        "cluster": "cluster_auth_identity",
        "title": "OAuth 2.0 & OpenID Connect RFC Specifications (PKCE, JWT, Introspection)",
        "keywords": ["oauth2", "oidc", "jwt", "pkce", "rfc6749", "rfc7519", "tokens", "authorization_code"],
        "content": """---
id: api_oauth2_oidc_spec
title: OAuth 2.0 & OpenID Connect Architecture Standard
type: api
cluster: cluster_auth_identity
category: authentication
keywords: [oauth2, oidc, jwt, pkce, rfc6749, rfc7519, tokens, authorization_code]
---

# OAuth 2.0 & OpenID Connect (OIDC) Standard

## 📌 Visión General
OAuth 2.0 (RFC 6749) es el protocolo de autorización delegada estándar de internet. OIDC es una capa de identidad montada sobre OAuth 2.0 que introduce el `id_token` firmado en formato JSON Web Token (JWT RFC 7519).

---

## ⚡ Flujo de Authorization Code con PKCE (Proof Key for Code Exchange - RFC 7636)
Imprescindible para SPAs (React/Vue/Next.js) y aplicaciones móviles para evitar la interceptación del código de autorización:

1. **Client genera `code_verifier` (cadena aleatoria segura de 43-128 caracteres)**.
2. **Client calcula `code_challenge = BASE64URL-ENCODE(SHA256(code_verifier))`**.
3. **Paso 1: Autorización**: Redirección a `/oauth/authorize?response_type=code&client_id=...&code_challenge=...&code_challenge_method=S256&scope=openid profile email`.
4. **Paso 2: Intercambio por Token**: `POST /oauth/token` enviando `code` y el `code_verifier` original en texto plano.
"""
    },
    {
        "id": "api_supabase_auth_database",
        "category": "apis/auth",
        "type": "api",
        "cluster": "cluster_auth_identity",
        "title": "Supabase API (GoTrue Auth, PostgREST & Realtime WebSockets)",
        "keywords": ["supabase", "gotrue", "postgrest", "realtime", "row_level_security", "rls", "jwt"],
        "content": """---
id: api_supabase_auth_database
title: Supabase Platform API (Auth, PostgREST & Realtime)
type: api
cluster: cluster_auth_identity
category: backend_as_a_service
keywords: [supabase, gotrue, postgrest, realtime, row_level_security, rls, jwt]
auth_type: API Key (anon/service_role) & Bearer JWT
base_url: https://<project-ref>.supabase.co
---

# Supabase API Reference

## 📌 Visión General
Supabase es una plataforma Backend-as-a-Service basada en PostgreSQL. Proporciona autenticación GoTrue integrada con Row-Level Security (RLS), generación automática de APIs REST via PostgREST, y canales pub/sub bidireccionales en tiempo real con WebSockets.

---

## ⚡ TypeScript Client Example
```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

// Consulta protegida por RLS en PostgreSQL
export async function getActiveProjects(userId: string) {
  const { data, error } = await supabase
    .from('projects')
    .select('id, title, status, created_at')
    .eq('owner_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data;
}
```
"""
    },
    {
        "id": "api_clerk_auth",
        "category": "apis/auth",
        "type": "api",
        "cluster": "cluster_auth_identity",
        "title": "Clerk Authentication & User Management API",
        "keywords": ["clerk", "nextjs_auth", "session_tokens", "organizations", "webhooks", "passkeys"],
        "content": """---
id: api_clerk_auth
title: Clerk Authentication & Identity Platform API
type: api
cluster: cluster_auth_identity
category: authentication
keywords: [clerk, nextjs_auth, session_tokens, organizations, webhooks, passkeys]
auth_type: Bearer Secret Key
base_url: https://api.clerk.com/v1
---

# Clerk API Reference

## 📌 Visión General
Clerk proporciona autenticación y gestión de usuarios multi-tenant para Next.js, React y entornos modernos. Ofrece componentes UI listos para producción, soporte para Passkeys biométricas, SSO empresarial (SAML/OIDC), y gestión de organizaciones.
"""
    },

    # =========================================================
    # 4. DATABASES, VECTOR ENGINES & CACHE APIS
    # =========================================================
    {
        "id": "api_pinecone_vector_db",
        "category": "apis/databases",
        "type": "api",
        "cluster": "cluster_vector_databases",
        "title": "Pinecone Vector Database API (Serverless Index, Hybrid Search, Namespaces)",
        "keywords": ["pinecone", "vector_database", "hnsw", "embeddings", "rag", "similarity_search"],
        "content": """---
id: api_pinecone_vector_db
title: Pinecone Serverless Vector Database API
type: api
cluster: cluster_vector_databases
category: vector_databases
keywords: [pinecone, vector_database, hnsw, embeddings, rag, similarity_search]
auth_type: Api-Key Header
base_url: https://api.pinecone.io
---

# Pinecone API Reference

## 📌 Visión General
Pinecone es una base de datos vectorial serverless diseñada para aplicaciones de IA, búsqueda semántica y RAG a escala masiva con latencias sub-10ms sobre miles de millones de vectores.

---

## 🐍 Implementación en Python (Indexación y Búsqueda Híbrida)
```python
import os
from pinecone import Pinecone

pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index("hermes-semantic-store")

# Upsert de vectores con metadatos
index.upsert(
    vectors=[
        {
            "id": "doc_101",
            "values": [0.024, -0.051, 0.128, ...], # vector embedding
            "metadata": {"category": "architecture", "author": "Rodrigo"}
        }
    ],
    namespace="production-v1"
)

# Consulta por similitud de coseno
query_results = index.query(
    vector=[0.021, -0.048, 0.130, ...],
    top_k=5,
    include_metadata=True,
    namespace="production-v1",
    filter={"category": {"$eq": "architecture"}}
)
```
"""
    },
    {
        "id": "api_qdrant_vector_engine",
        "category": "apis/databases",
        "type": "api",
        "cluster": "cluster_vector_databases",
        "title": "Qdrant Vector Engine API (REST, gRPC, Scalar Quantization & Payload Filtering)",
        "keywords": ["qdrant", "vector_search", "grpc", "scalar_quantization", "hnsw", "payload_filter"],
        "content": """---
id: api_qdrant_vector_engine
title: Qdrant Vector Search Engine (REST & gRPC API)
type: api
cluster: cluster_vector_databases
category: vector_databases
keywords: [qdrant, vector_search, grpc, scalar_quantization, hnsw, payload_filter]
auth_type: api-key Header
base_url: http://localhost:6333 o https://xyz.cloud.qdrant.io
---

# Qdrant Vector Engine API Reference

## 📌 Visión General
Qdrant es un motor de búsqueda vectorial de código abierto escrito en Rust. Ofrece soporte para gRPC de ultra alta velocidad, cuantización escalar (Scalar & Product Quantization) para reducir el consumo de RAM en un 75%, y filtrado estricto de payloads durante la fase de búsqueda HNSW.
"""
    },
    {
        "id": "api_upstash_serverless_redis",
        "category": "apis/databases",
        "type": "api",
        "cluster": "cluster_vector_databases",
        "title": "Upstash REST API (Serverless Redis, QStash Message Queue & Vector)",
        "keywords": ["upstash", "serverless_redis", "qstash", "rate_limiting", "cron", "edge_caching"],
        "content": """---
id: api_upstash_serverless_redis
title: Upstash Serverless Redis & QStash Messaging API
type: api
cluster: cluster_vector_databases
category: databases_cache
keywords: [upstash, serverless_redis, qstash, rate_limiting, cron, edge_caching]
auth_type: Bearer Token
base_url: https://<endpoint>.upstash.io
---

# Upstash API Reference

## 📌 Visión General
Upstash ofrece Redis, Vector DB y colas de mensajes distribuidas (QStash) con arquitectura serverless nativa sobre HTTP/REST. Es ideal para Edge Functions (Vercel Edge, Cloudflare Workers) donde las conexiones TCP persistentes no son viables.
"""
    },

    # =========================================================
    # 5. COMMUNICATIONS & MESSAGING APIS
    # =========================================================
    {
        "id": "api_resend_email_platform",
        "category": "apis/comms",
        "type": "api",
        "cluster": "cluster_comms_messaging",
        "title": "Resend Email Platform API (React Email, Batch Sending & Webhooks)",
        "keywords": ["resend", "transactional_email", "react_email", "smtp", "batch_sending", "webhooks"],
        "content": """---
id: api_resend_email_platform
title: Resend Email Platform & React Email API
type: api
cluster: cluster_comms_messaging
category: communications
keywords: [resend, transactional_email, react_email, smtp, batch_sending, webhooks]
auth_type: Bearer Token
base_url: https://api.resend.com
---

# Resend Email API Reference

## 📌 Visión General
Resend es la plataforma de correo transaccional moderna preferida por desarrolladores de Next.js y Node.js. Soporta plantillas declarativas con React Email, entrega garantizada con DKIM/SPF y webhooks para monitorear aperturas y rebotes.

---

## 🐍 Implementación en Python
```python
import os
import resend

resend.api_key = os.environ.get("RESEND_API_KEY")

params = {
    "from": "Acme <onboarding@resend.dev>",
    "to": ["usuario@ejemplo.com"],
    "subject": "Tu reporte de optimización está listo",
    "html": "<strong>Hola!</strong> Tu sistema fue optimizado con éxito.",
}

email = resend.Emails.send(params)
print(f"Correo enviado con ID: {email['id']}")
```
"""
    },
    {
        "id": "api_twilio_communications",
        "category": "apis/comms",
        "type": "api",
        "cluster": "cluster_comms_messaging",
        "title": "Twilio Communications API (SMS, Voice TwiML, WhatsApp Business & Verify OTP)",
        "keywords": ["twilio", "sms", "voice", "twiml", "whatsapp_business", "verify_otp", "telecom"],
        "content": """---
id: api_twilio_communications
title: Twilio Cloud Communications Platform API
type: api
cluster: cluster_comms_messaging
category: communications
keywords: [twilio, sms, voice, twiml, whatsapp_business, verify_otp, telecom]
auth_type: HTTP Basic Auth (Account SID : Auth Token)
base_url: https://api.twilio.com/2010-04-01
---

# Twilio Communications API Reference

## 📌 Visión General
Twilio provee APIs de telecomunicaciones globales para envío masivo de SMS, llamadas telefónicas interactivas (IVR programable con TwiML), integración oficial con WhatsApp Business API, y verificación de identidad 2FA (Twilio Verify).
"""
    },
    {
        "id": "api_telegram_bot_platform",
        "category": "apis/comms",
        "type": "api",
        "cluster": "cluster_comms_messaging",
        "title": "Telegram Bot API (Webhooks, Inline Keyboards, Bot Payments & Mini Apps)",
        "keywords": ["telegram", "bot_api", "webhooks", "inline_keyboards", "mini_apps", "long_polling"],
        "content": """---
id: api_telegram_bot_platform
title: Telegram Bot Platform API Specification
type: api
cluster: cluster_comms_messaging
category: messaging_bots
keywords: [telegram, bot_api, webhooks, inline_keyboards, mini_apps, long_polling]
auth_type: Bot Token in URL Path (`/bot<token>/<method>`)
base_url: https://api.telegram.org
---

# Telegram Bot API Reference

## 📌 Visión General
La API de Telegram Bot permite construir agentes interactivos, sistemas de alerta, teclados en línea (*Inline Keyboards*) y Telegram Mini Apps (aplicaciones web completas embebidas en el chat con pagos nativos).
"""
    },

    # =========================================================
    # 6. DEVELOPER TOOLS, GIT & PRODUCTIVITY APIS
    # =========================================================
    {
        "id": "api_github_rest_graphql",
        "category": "apis/devtools",
        "type": "api",
        "cluster": "cluster_dev_tools",
        "title": "GitHub REST & GraphQL API (Octokit, Webhooks HMAC, Git Data & Actions)",
        "keywords": ["github", "octokit", "graphql", "webhooks_hmac", "actions_ci", "pull_requests", "git_data"],
        "content": """---
id: api_github_rest_graphql
title: GitHub REST v3 & GraphQL v4 Platform API
type: api
cluster: cluster_dev_tools
category: developer_tools
keywords: [github, octokit, graphql, webhooks_hmac, actions_ci, pull_requests, git_data]
auth_type: Bearer Token (Personal Access Token o GitHub App JWT)
base_url: https://api.github.com
---

# GitHub API Reference

## 📌 Visión General
La API de GitHub proporciona control programático sobre repositorios, Pull Requests, Issues, despliegues, flujos de trabajo de CI/CD (GitHub Actions) y gestión de organizaciones mediante endpoints REST y GraphQL.

---

## ⚡ Verificación de Webhooks con HMAC SHA-256
```python
import hmac
import hashlib

def verify_github_webhook(payload_body: bytes, signature_header: str, secret: str) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)
```
"""
    },
    {
        "id": "api_linear_graphql",
        "category": "apis/devtools",
        "type": "api",
        "cluster": "cluster_dev_tools",
        "title": "Linear GraphQL API (Issue Tracking, Cycles, Projects & Webhooks)",
        "keywords": ["linear", "graphql", "issue_tracking", "project_management", "cycles", "webhooks"],
        "content": """---
id: api_linear_graphql
title: Linear Issue & Project Tracking GraphQL API
type: api
cluster: cluster_dev_tools
category: developer_tools
keywords: [linear, graphql, issue_tracking, project_management, cycles, webhooks]
auth_type: API Key Header (`Authorization: <API_KEY>` o OAuth2 Bearer)
base_url: https://api.linear.app/graphql
---

# Linear API Reference

## 📌 Visión General
Linear ofrece una API basada exclusivamente en GraphQL para sincronizar issues, sprints (*cycles*), proyectos, etiquetas y flujos de trabajo de ingeniería de software con altísima velocidad.
"""
    },

    # =========================================================
    # 7. MODERN ARCHITECTURES, STRUCTURES & CONCEPTS
    # =========================================================
    {
        "id": "arch_model_context_protocol",
        "category": "structures/agents",
        "type": "structure",
        "cluster": "cluster_system_architectures",
        "title": "Model Context Protocol (MCP) Architecture Specification",
        "keywords": ["mcp", "model_context_protocol", "tools", "prompts", "resources", "json_rpc", "fastmcp"],
        "content": """---
id: arch_model_context_protocol
title: Model Context Protocol (MCP) Architecture Standard
type: structure
cluster: cluster_system_architectures
category: agentic_ai
keywords: [mcp, model_context_protocol, tools, prompts, resources, json_rpc, fastmcp]
---

# Model Context Protocol (MCP) Architecture

## 📌 Visión General
El **Model Context Protocol (MCP)** es un estándar abierto desarrollado por Anthropic para conectar de forma desacoplada y segura modelos de lenguaje (LLMs) y asistentes de IA con herramientas externas (*Tools*), fuentes de datos contextuales (*Resources*) y plantillas de interacción (*Prompts*), utilizando transporte JSON-RPC 2.0 (sobre `stdio` o `SSE - Server-Sent Events`).

---

## ⚡ Los Tres Primitivos Fundamentales de MCP

1. **Tools (Herramientas Ejecutables)**:
   - Funciones que el modelo puede invocar con argumentos validados por JSON Schema.
2. **Resources (Recursos de Lectura)**:
   - URIs (`file:///...`, `postgres://...`, `hermes://...`) que exponen datos estáticos o dinámicos para ser incorporados al contexto del LLM.
3. **Prompts (Plantillas Guiadas)**:
   - Flujos de trabajo prediseñados y parametrizados para orientar al modelo en tareas especializadas.

---

## 🐍 Implementación de un Servidor FastMCP
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SystemMetricsServer")

@mcp.tool()
def get_system_load() -> dict:
    \"\"\"Devuelve el estado de CPU, RAM y latencia del cluster.\"\"\"
    import psutil
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
```
"""
    },
    {
        "id": "pattern_event_driven_cqrs",
        "category": "patterns/architecture",
        "type": "pattern",
        "cluster": "cluster_system_architectures",
        "title": "Event-Driven Architecture with CQRS & Event Sourcing",
        "keywords": ["event_driven", "cqrs", "event_sourcing", "kafka", "projections", "eventual_consistency"],
        "content": """---
id: pattern_event_driven_cqrs
title: Event-Driven Architecture with CQRS & Event Sourcing
type: pattern
cluster: cluster_system_architectures
category: distributed_systems
keywords: [event_driven, cqrs, event_sourcing, kafka, projections, eventual_consistency]
---

# Event-Driven Architecture with CQRS & Event Sourcing

## 📌 Visión General
**Command Query Responsibility Segregation (CQRS)** separa conceptual y físicamente las operaciones de modificación de estado (*Commands*) de las operaciones de lectura (*Queries*). Combinado con **Event Sourcing**, el estado de la aplicación no se sobreescribe en una base de datos relacional, sino que se almacena como una secuencia inmutable de eventos de dominio históricos (*Append-Only Event Store*).

---

## ⚡ Diagrama de Flujo
```text
[ Cliente ] ── (Command) ──▶ [ Command Handler ] ──▶ [ Append Event ] ──▶ [ Event Store ]
                                                                                │
                                                                       (Event Published)
                                                                                ▼
[ Cliente ] ◀── (Query) ─── [ Read Model (Redis/Elastic) ] ◀── [ Projection Handler ]
```
"""
    },
    {
        "id": "pattern_hierarchical_multi_agent_supervisor",
        "category": "patterns/agents",
        "type": "pattern",
        "cluster": "cluster_system_architectures",
        "title": "Hierarchical Multi-Agent Supervisor Pattern (LangGraph / StateGraph)",
        "keywords": ["multi_agent", "supervisor", "langgraph", "stategraph", "agentic_workflow", "router"],
        "content": """---
id: pattern_hierarchical_multi_agent_supervisor
title: Hierarchical Multi-Agent Supervisor Pattern
type: pattern
cluster: cluster_system_architectures
category: agentic_ai
keywords: [multi_agent, supervisor, langgraph, stategraph, agentic_workflow, router]
---

# Hierarchical Multi-Agent Supervisor Pattern

## 📌 Visión General
En lugar de depender de un único agente con cientos de herramientas incompatibles, el patrón **Supervisor Jerárquico** delega subtareas a agentes trabajadores especializados (*Coder Agent*, *Research Agent*, *Reviewer Agent*, *Tester Agent*). Un agente Supervisor central orquesta el flujo de ejecución evaluando el estado del grafo y decidiendo el siguiente paso hasta alcanzar la condición de parada.
"""
    },
    {
        "id": "concept_zero_trust_architecture",
        "category": "concepts/security",
        "type": "concept",
        "cluster": "cluster_system_architectures",
        "title": "Zero-Trust Network Architecture (ZTNA, mTLS & Least Privilege)",
        "keywords": ["zero_trust", "ztna", "mtls", "least_privilege", "identity_aware_proxy", "security"],
        "content": """---
id: concept_zero_trust_architecture
title: Zero-Trust Network Architecture (ZTNA)
type: concept
cluster: cluster_system_architectures
category: cybersecurity
keywords: [zero_trust, ztna, mtls, least_privilege, identity_aware_proxy, security]
---

# Zero-Trust Network Architecture (ZTNA)

## 📌 Principio Fundamental
*"Nunca confiar, siempre verificar" (Never Trust, Always Verify)*. En una arquitectura Zero-Trust, ningún usuario o servicio dentro de la red corporativa o de la nube es considerado confiable por defecto. Cada solicitud requiere autenticación mutua criptográfica (mTLS), autorización contextual en tiempo real y cumplimiento estricto del principio de mínimo privilegio.
"""
    }
]

# Clusters a asegurar en el grafo
CLUSTERS = {
    "cluster_ai_apis": {
        "type": "cluster",
        "label": "🤖 AI & LLM APIs",
        "file": "",
        "keywords": ["ai", "llm", "openai", "anthropic", "gemini", "groq", "deepseek", "mistral", "inference"]
    },
    "cluster_fintech_apis": {
        "type": "cluster",
        "label": "💳 FinTech & Payments",
        "file": "",
        "keywords": ["fintech", "payments", "stripe", "mercadopago", "plaid", "paypal", "billing", "subscriptions"]
    },
    "cluster_auth_identity": {
        "type": "cluster",
        "label": "🔐 Auth & Identity",
        "file": "",
        "keywords": ["auth", "oauth2", "oidc", "supabase", "clerk", "auth0", "jwt", "pkce"]
    },
    "cluster_vector_databases": {
        "type": "cluster",
        "label": "🗄️ Vector DBs & Cache",
        "file": "",
        "keywords": ["vector_db", "pinecone", "qdrant", "upstash", "redis", "hnsw", "embeddings"]
    },
    "cluster_comms_messaging": {
        "type": "cluster",
        "label": "📡 Comms & Messaging",
        "file": "",
        "keywords": ["email", "sms", "resend", "twilio", "telegram", "discord", "slack", "webhooks"]
    },
    "cluster_dev_tools": {
        "type": "cluster",
        "label": "🛠️ Dev Tools & Git",
        "file": "",
        "keywords": ["git", "github", "gitlab", "linear", "jira", "ci_cd", "devtools"]
    },
    "cluster_system_architectures": {
        "type": "cluster",
        "label": "🏛️ System Architectures & Patterns",
        "file": "",
        "keywords": ["mcp", "cqrs", "event_driven", "multi_agent", "zero_trust", "architecture", "patterns"]
    }
}


def build_and_ingest():
    print("🚀 Iniciando Ingesta Masiva de la Enciclopedia de APIs y Arquitecturas...")
    
    # 1. Cargar grafo actual
    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    nodes: Dict[str, Any] = graph.get("nodes", {})
    edges: List[Dict[str, Any]] = graph.get("edges", [])

    # 2. Registrar clusters
    for cid, cdata in CLUSTERS.items():
        if cid not in nodes:
            nodes[cid] = cdata
            print(f"  📁 Cluster registrado: {cid}")

    # 3. Escribir archivos de conocimiento e incorporar nodos
    created_items = 0
    for item in ITEMS:
        nid = item["id"]
        cat = item["category"]
        file_name = f"{nid.replace('api_', '').replace('arch_', '').replace('pattern_', '').replace('concept_', '')}.md"
        rel_file = f"{cat}/{file_name}"
        full_path = HUB_ROOT / rel_file
        full_path.parent.mkdir(parents=True, exist_ok=True)

        full_path.write_text(item["content"].strip(), encoding="utf-8")

        nodes[nid] = {
            "type": item["type"],
            "label": item["title"],
            "file": rel_file,
            "keywords": item["keywords"]
        }

        # Conectar al cluster temático
        cluster_id = item["cluster"]
        edges.append({
            "source": cluster_id,
            "target": nid,
            "weight": 0.95,
            "relation": "contains"
        })
        created_items += 1
        print(f"  📄 Documento e Ingesta OK: [{item['type'].upper()}] {nid} -> {rel_file}")

    # 4. Guardar
    graph["nodes"] = nodes
    graph["edges"] = edges

    with open(GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Se generaron e ingirieron {created_items} nuevas APIs y arquitecturas.")
    print(f"📊 Nodos actuales: {len(nodes)} | Aristas actuales: {len(edges)}")


if __name__ == "__main__":
    build_and_ingest()
