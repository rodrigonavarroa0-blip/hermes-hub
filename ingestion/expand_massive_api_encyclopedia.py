#!/usr/bin/env python3
"""
expand_massive_api_encyclopedia.py
Expande masivamente la enciclopedia de APIs, arquitecturas, estructuras y conceptos en ~/.hermes-hub.
Cubre: Cloud, E-Commerce, CRM, Media, Geo, Protocolos, Microservicios, RAG Avanzado y Algoritmos Distribuidos.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
GRAPH_FILE = CONFIG_DIR / "graph.json"

APIS_DIR = HUB_ROOT / "apis"
PATTERNS_DIR = HUB_ROOT / "patterns"
CONCEPTS_DIR = HUB_ROOT / "concepts"
STRUCTURES_DIR = HUB_ROOT / "structures"

ADDITIONAL_ITEMS = [
    # =========================================================
    # CLOUD, COMPUTE, SERVERLESS & STORAGE APIS
    # =========================================================
    {
        "id": "api_aws_s3_storage",
        "category": "apis/cloud",
        "type": "api",
        "cluster": "cluster_cloud_infra",
        "title": "AWS S3 Object Storage API (Presigned URLs, Multipart & Bucket Policies)",
        "keywords": ["aws", "s3", "presigned_urls", "multipart_upload", "bucket_policy", "object_storage", "boto3"],
        "content": """---
id: api_aws_s3_storage
title: AWS S3 REST API & Boto3 Integration Reference
type: api
cluster: cluster_cloud_infra
category: cloud_storage
keywords: [aws, s3, presigned_urls, multipart_upload, bucket_policy, object_storage, boto3]
auth_type: AWS Signature Version 4 (SigV4)
base_url: https://<bucket>.s3.<region>.amazonaws.com
---

# AWS S3 Object Storage API Reference

## 📌 Visión General
Amazon Simple Storage Service (S3) es el almacenamiento de objetos líder en la nube. Ofrece alta durabilidad (99.999999999%), URLs prefirmadas para subida y descarga directa desde el navegador (sin saturar el servidor backend) y soporte para transferencias multiparte en archivos grandes.

---

## ⚡ Generación de Presigned URL en Python con Boto3
```python
import boto3
from botocore.config import Config

s3_client = boto3.client(
    's3',
    region_name='us-east-1',
    config=Config(signature_version='s3v4')
)

def generate_presigned_upload_url(bucket_name: str, object_key: str, expires_in: int = 3600) -> str:
    \"\"\"Genera una URL temporal para que el frontend suba un archivo directamente a S3 con PUT.\"\"\"
    return s3_client.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': bucket_name,
            'Key': object_key,
            'ContentType': 'application/octet-stream'
        },
        ExpiresIn=expires_in
    )
```
"""
    },
    {
        "id": "api_cloudflare_workers_kv_d1",
        "category": "apis/cloud",
        "type": "api",
        "cluster": "cluster_cloud_infra",
        "title": "Cloudflare Workers, KV, D1 SQL & Vectorize API",
        "keywords": ["cloudflare", "workers", "kv_store", "d1_database", "vectorize", "edge_compute", "serverless"],
        "content": """---
id: api_cloudflare_workers_kv_d1
title: Cloudflare Edge Computing, KV & D1 REST/Bindings API
type: api
cluster: cluster_cloud_infra
category: edge_computing
keywords: [cloudflare, workers, kv_store, d1_database, vectorize, edge_compute, serverless]
auth_type: Bearer API Token
base_url: https://api.cloudflare.com/client/v4
---

# Cloudflare Workers & Edge Infrastructure API Reference

## 📌 Visión General
La red perimetral de Cloudflare ejecuta Workers con aislamiento basado en V8 V8-Isolates en más de 300 ciudades con latencia sub-50ms. Integra almacenamiento clave-valor global (Workers KV), base de datos relacional serverless SQLite distribuida (D1 SQL) y base de datos vectorial (Vectorize).
"""
    },
    {
        "id": "api_vercel_rest_platform",
        "category": "apis/cloud",
        "type": "api",
        "cluster": "cluster_cloud_infra",
        "title": "Vercel REST API (Deployments, Edge Config & Environment Variables)",
        "keywords": ["vercel", "deployments", "edge_config", "nextjs_hosting", "domains", "env_vars"],
        "content": """---
id: api_vercel_rest_platform
title: Vercel REST Platform & Deployment API
type: api
cluster: cluster_cloud_infra
category: cloud_platform
keywords: [vercel, deployments, edge_config, nextjs_hosting, domains, env_vars]
auth_type: Bearer Token
base_url: https://api.vercel.com
---

# Vercel API Reference

## 📌 Visión General
La API de Vercel permite automatizar despliegues de aplicaciones frontend y serverless, gestionar variables de entorno por rama (`preview`, `production`), y actualizar *Edge Config* (almacén global de lectura ultra rápida en <1ms) para toggles y configuraciones en tiempo real.
"""
    },
    {
        "id": "api_flyio_machines",
        "category": "apis/cloud",
        "type": "api",
        "cluster": "cluster_cloud_infra",
        "title": "Fly.io Machines REST API (Micro-VMs Creation & Lifecycle)",
        "keywords": ["flyio", "machines_api", "micro_vms", "firecracker", "docker_containers", "edge"],
        "content": """---
id: api_flyio_machines
title: Fly.io Machines Micro-VM REST API
type: api
cluster: cluster_cloud_infra
category: cloud_infrastructure
keywords: [flyio, machines_api, micro_vms, firecracker, docker_containers, edge]
auth_type: Bearer Fly API Token
base_url: https://api.machines.dev/v1
---

# Fly.io Machines API Reference

## 📌 Visión General
Fly.io Machines es una API REST pura para aprovisionar y destruir micro-VMs basadas en Firecracker en menos de 300 milisegundos en cualquier región del planeta. Ideal para ejecutar sandboxes de código de usuarios y agentes de IA aislados de forma segura.
"""
    },

    # =========================================================
    # E-COMMERCE & CRM APIS
    # =========================================================
    {
        "id": "api_shopify_admin_graphql",
        "category": "apis/ecommerce",
        "type": "api",
        "cluster": "cluster_ecommerce_crm",
        "title": "Shopify Admin GraphQL API (Products, Orders, Customers & Webhooks)",
        "keywords": ["shopify", "graphql_admin", "ecommerce", "orders", "inventory", "webhooks_hmac", "storefront"],
        "content": """---
id: api_shopify_admin_graphql
title: Shopify Admin GraphQL API & Storefront Reference
type: api
cluster: cluster_ecommerce_crm
category: ecommerce
keywords: [shopify, graphql_admin, ecommerce, orders, inventory, webhooks_hmac, storefront]
auth_type: X-Shopify-Access-Token Header
base_url: https://<shop_name>.myshopify.com/admin/api/2024-10/graphql.json
---

# Shopify Admin GraphQL API Reference

## 📌 Visión General
La API GraphQL de Shopify Admin es la interfaz principal para sincronizar catálogos masivos, inventarios multi-ubicación, clientes y pedidos de comercio electrónico con soporte de operaciones en lote (*Bulk Operations*).

---

## ⚡ Consulta GraphQL de Productos en Python
```python
import httpx

SHOPIFY_URL = "https://tu-tienda.myshopify.com/admin/api/2024-10/graphql.json"
HEADERS = {
    "X-Shopify-Access-Token": "shpat_xxxxxxxxxxxxxxxx",
    "Content-Type": "application/json"
}

QUERY = \"\"\"
query getProducts($first: Int!) {
  products(first: $first) {
    edges {
      node {
        id
        title
        handle
        totalInventory
        priceRangeV2 {
          minVariantPrice { amount currencyCode }
        }
      }
    }
  }
}
\"\"\"

async def fetch_products():
    async with httpx.AsyncClient() as client:
        res = await client.post(SHOPIFY_URL, headers=HEADERS, json={"query": QUERY, "variables": {"first": 10}})
        return res.json()["data"]["products"]["edges"]
```
"""
    },
    {
        "id": "api_hubspot_crm_v3",
        "category": "apis/crm",
        "type": "api",
        "cluster": "cluster_ecommerce_crm",
        "title": "HubSpot CRM API v3 (Contacts, Deals, Companies & Batch Operations)",
        "keywords": ["hubspot", "crm", "contacts", "deals", "companies", "sales_pipeline", "marketing"],
        "content": """---
id: api_hubspot_crm_v3
title: HubSpot CRM API v3 Platform Reference
type: api
cluster: cluster_ecommerce_crm
category: crm
keywords: [hubspot, crm, contacts, deals, companies, sales_pipeline, marketing]
auth_type: Bearer Private App Access Token
base_url: https://api.hubapi.com
---

# HubSpot CRM API v3 Reference

## 📌 Visión General
La API v3 de HubSpot permite sincronizar contactos (`/crm/v3/objects/contacts`), negocios y oportunidades comerciales (`/crm/v3/objects/deals`), empresas y líneas de tiempo de eventos con soporte nativo para operaciones por lotes (*batch*).
"""
    },
    {
        "id": "api_airtable_rest_database",
        "category": "apis/crm",
        "type": "api",
        "cluster": "cluster_ecommerce_crm",
        "title": "Airtable REST API (Bases, Tables, Records CRUD & Webhooks)",
        "keywords": ["airtable", "low_code", "records_crud", "relational_sheets", "webhooks"],
        "content": """---
id: api_airtable_rest_database
title: Airtable REST API & Webhooks
type: api
cluster: cluster_ecommerce_crm
category: crm_nocode
keywords: [airtable, low_code, records_crud, relational_sheets, webhooks]
auth_type: Bearer Personal Access Token (PAT)
base_url: https://api.airtable.com/v0
---

# Airtable REST API Reference

## 📌 Visión General
Airtable expone una API REST automática para cada base de datos. Permite leer, crear, actualizar y filtrar registros con fórmulas avanzadas (`filterByFormula`) y suscripciones a webhooks para cambios de fila.
"""
    },

    # =========================================================
    # MEDIA, GEO & CONTENT APIS
    # =========================================================
    {
        "id": "api_cloudinary_media",
        "category": "apis/media",
        "type": "api",
        "cluster": "cluster_media_geo",
        "title": "Cloudinary Media API (Image/Video Upload, Dynamic Transformations & AI)",
        "keywords": ["cloudinary", "image_transformation", "video_streaming", "cdn", "ai_cropping", "media"],
        "content": """---
id: api_cloudinary_media
title: Cloudinary Media Transformation & Storage API
type: api
cluster: cluster_media_geo
category: media_cdn
keywords: [cloudinary, image_transformation, video_streaming, cdn, ai_cropping, media]
auth_type: API Key & API Secret (HMAC SHA-1 Signature)
base_url: https://api.cloudinary.com/v1_1/<cloud_name>
---

# Cloudinary Media API Reference

## 📌 Visión General
Cloudinary es la plataforma líder para gestión, optimización y transformación de imágenes y videos en tiempo real a través de URLs inteligentes (conversión automática a formato WebP/AVIF, recorte inteligente basado en rostros por IA y streaming HLS/DASH).
"""
    },
    {
        "id": "api_google_maps_platform",
        "category": "apis/geo",
        "type": "api",
        "cluster": "cluster_media_geo",
        "title": "Google Maps Platform APIs (Geocoding, Places, Routes & Distance Matrix)",
        "keywords": ["google_maps", "geocoding", "places_api", "routes", "distance_matrix", "gis"],
        "content": """---
id: api_google_maps_platform
title: Google Maps Platform REST APIs Reference
type: api
cluster: cluster_media_geo
category: geolocation
keywords: [google_maps, geocoding, places_api, routes, distance_matrix, gis]
auth_type: API Key in Query Parameter (`key=...`) o Header (`X-Goog-Api-Key`)
base_url: https://maps.googleapis.com/maps/api
---

# Google Maps Platform Reference

## 📌 Visión General
Google Maps Platform ofrece APIs geoespaciales para geocodificación directa e inversa (`/geocode/json`), búsqueda de puntos de interés (`/place/nearbysearch/json`), y cálculo de rutas óptimas con tráfico en tiempo real (`/directions/json` y Routes API v2).
"""
    },

    # =========================================================
    # MODERN ARCHITECTURAL PATTERNS & DISTRIBUTED SYSTEMS
    # =========================================================
    {
        "id": "pattern_hexagonal_ports_adapters",
        "category": "patterns/architecture",
        "type": "pattern",
        "cluster": "cluster_system_architectures",
        "title": "Hexagonal Architecture (Ports & Adapters) & Clean Domain Design",
        "keywords": ["hexagonal_architecture", "ports_and_adapters", "clean_architecture", "domain_driven_design", "dependency_inversion"],
        "content": """---
id: pattern_hexagonal_ports_adapters
title: Hexagonal Architecture (Ports and Adapters)
type: pattern
cluster: cluster_system_architectures
category: software_architecture
keywords: [hexagonal_architecture, ports_and_adapters, clean_architecture, domain_driven_design, dependency_inversion]
---

# Hexagonal Architecture (Ports & Adapters)

## 📌 Principio Rector
Aislar la lógica de negocio central (*Dominio*) de cualquier dependencia externa (FastAPI, PostgreSQL, Redis, APIs de terceros). El dominio define **Puertos** (interfaces abstractas) y la infraestructura provee **Adaptadores** concretos que implementan dichos puertos.

---

## ⚡ Implementación en Python
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

# 1. DOMINIO PURO (Sin dependencias externas)
@dataclass
class User:
    id: str
    email: str
    is_active: bool

# 2. PUERTO (Interfaz Abstracta)
class UserRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> None:
        pass

# 3. CASO DE USO (Orquestación del Dominio)
class ActivateUserUseCase:
    def __init__(self, repo: UserRepositoryPort):
        self.repo = repo

    async def execute(self, user_id: str) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        user.is_active = True
        await self.repo.save(user)
        return user
```
"""
    },
    {
        "id": "pattern_saga_distributed_transactions",
        "category": "patterns/distributed",
        "type": "pattern",
        "cluster": "cluster_system_architectures",
        "title": "Saga Pattern for Distributed Transactions (Orchestration vs Choreography)",
        "keywords": ["saga_pattern", "distributed_transactions", "compensating_actions", "microservices", "orchestrator"],
        "content": """---
id: pattern_saga_distributed_transactions
title: Saga Distributed Transaction Pattern
type: pattern
cluster: cluster_system_architectures
category: distributed_systems
keywords: [saga_pattern, distributed_transactions, compensating_actions, microservices, orchestrator]
---

# Saga Distributed Transaction Pattern

## 📌 Visión General
En arquitecturas de microservicios donde las transacciones ACID distribuidas (2PC - Two-Phase Commit) resultan inviables por bloqueo y latencia, el patrón **Saga** ejecuta una secuencia de transacciones locales coordinadas. Si un paso falla, la Saga ejecuta **Acciones Compensatorias** en orden inverso para revertir el estado del sistema.
"""
    },
    {
        "id": "pattern_advanced_hybrid_rag",
        "category": "patterns/ai_rag",
        "type": "pattern",
        "cluster": "cluster_system_architectures",
        "title": "Advanced Hybrid RAG Architecture (BM25 + Dense Vectors + Cohere Rerank)",
        "keywords": ["hybrid_rag", "dense_retrieval", "sparse_retrieval", "bm25", "cohere_rerank", "reciprocal_rank_fusion"],
        "content": """---
id: pattern_advanced_hybrid_rag
title: Advanced Hybrid RAG Architecture
type: pattern
cluster: cluster_system_architectures
category: agentic_ai
keywords: [hybrid_rag, dense_retrieval, sparse_retrieval, bm25, cohere_rerank, reciprocal_rank_fusion]
---

# Advanced Hybrid RAG Architecture

## 📌 Pipeline de 3 Etapas
1. **Recuperación Híbrida (Sparse + Dense)**:
   - BM25 / Elastic para coincidencia léxica exacta (IDs, códigos, nombres técnicos).
   - Dense Embeddings (OpenAI / BGE-Large) para coincidencia semántica conceptual.
2. **Fusión de Rangos (RRF - Reciprocal Rank Fusion)**:
   - $RRF(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$ con $k=60$.
3. **Re-ordenamiento con Cross-Encoder (Cohere Rerank v3)**:
   - Evalúa conjuntamente `(Query, Document)` calculando un score de relevancia de alta precisión antes de inyectar el contexto al LLM.
"""
    },
    {
        "id": "concept_hnsw_vector_indexing",
        "category": "concepts/algorithms",
        "type": "concept",
        "cluster": "cluster_system_architectures",
        "title": "Hierarchical Navigable Small World (HNSW) Vector Indexing",
        "keywords": ["hnsw", "approximate_nearest_neighbors", "ann", "vector_search", "graph_indexing", "cosine_distance"],
        "content": """---
id: concept_hnsw_vector_indexing
title: HNSW (Hierarchical Navigable Small World) Indexing
type: concept
cluster: cluster_system_architectures
category: computer_science
keywords: [hnsw, approximate_nearest_neighbors, ann, vector_search, graph_indexing, cosine_distance]
---

# HNSW Vector Indexing Concept

## 📌 Fundamento Algorítmico
HNSW es la estructura de datos para Búsqueda de Vecinos Más Próximos Aproximados (ANN) más eficiente en la actualidad (complejidad de búsqueda $O(\log N)$). Modela una jerarquía multicapa de grafos donde las capas superiores contienen saltos largos para navegación rápida (búsqueda global tipo Skip List) y las capas inferiores contienen conexiones densas para convergencia local de alta precisión.
"""
    },
    {
        "id": "concept_crdt_collaborative_sync",
        "category": "concepts/distributed",
        "type": "concept",
        "cluster": "cluster_system_architectures",
        "title": "Conflict-Free Replicated Data Types (CRDTs) for Realtime Collaboration",
        "keywords": ["crdt", "local_first", "yjs", "automerge", "eventual_consistency", "realtime_collaboration"],
        "content": """---
id: concept_crdt_collaborative_sync
title: CRDTs (Conflict-Free Replicated Data Types)
type: concept
cluster: cluster_system_architectures
category: distributed_systems
keywords: [crdt, local_first, yjs, automerge, eventual_consistency, realtime_collaboration]
---

# Conflict-Free Replicated Data Types (CRDTs)

## 📌 Visión General
Los CRDTs permiten que múltiples nodos en una red distribuida (o clientes web en aplicaciones tipo Figma / Notion / Google Docs) editen concurrentemente una misma estructura de datos sin coordinación central ni bloqueos de red, garantizando matemáticamente que cuando todos los nodos reciban los mismos mensajes convergerán al **mismo estado idéntico** (Convergencia Eventual Fuerte).
"""
    }
]

# Clusters adicionales
EXTRA_CLUSTERS = {
    "cluster_cloud_infra": {
        "type": "cluster",
        "label": "☁️ Cloud & Serverless Infra",
        "file": "",
        "keywords": ["aws", "gcp", "cloudflare", "vercel", "flyio", "serverless", "storage"]
    },
    "cluster_ecommerce_crm": {
        "type": "cluster",
        "label": "🛍️ E-Commerce & CRM",
        "file": "",
        "keywords": ["shopify", "hubspot", "airtable", "salesforce", "ecommerce", "crm"]
    },
    "cluster_media_geo": {
        "type": "cluster",
        "label": "🗺️ Media, Geo & Maps",
        "file": "",
        "keywords": ["cloudinary", "google_maps", "geocoding", "places", "cdn", "streaming"]
    }
}


def expand():
    print("🚀 Expandiendo la Enciclopedia Global de APIs y Arquitecturas...")

    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    nodes: Dict[str, Any] = graph.get("nodes", {})
    edges: List[Dict[str, Any]] = graph.get("edges", [])

    for cid, cdata in EXTRA_CLUSTERS.items():
        if cid not in nodes:
            nodes[cid] = cdata
            print(f"  📁 Cluster registrado: {cid}")

    added = 0
    for item in ADDITIONAL_ITEMS:
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

        cluster_id = item["cluster"]
        edges.append({
            "source": cluster_id,
            "target": nid,
            "weight": 0.95,
            "relation": "contains"
        })
        added += 1
        print(f"  📄 Ingesta OK: [{item['type'].upper()}] {nid} -> {rel_file}")

    graph["nodes"] = nodes
    graph["edges"] = edges

    with open(GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Se agregaron {added} nuevas especificaciones de primer nivel.")
    print(f"📊 Nodos totales: {len(nodes)} | Aristas totales: {len(edges)}")


if __name__ == "__main__":
    expand()
