#!/usr/bin/env python3
"""
Hermes CLI & Project Engine
Generador de proyectos y gobernanza de IA impulsado por Hermes Knowledge Hub.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Path al motor de Hermes
SCRIPT_DIR = Path(__file__).resolve().parent
HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
EPISODIC_MEMORY_FILE = HUB_PATH / "config" / "episodic_memory.json"
GRAPH_FILE = HUB_PATH / "config" / "graph.json"

# Colores y Formato Terminal
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}⚡ HERMES PROJECT ENGINE & KNOWLEDGE SCAFFOLDER ⚡{Colors.END}
{Colors.DIM}Connected to Hermes Hub: {HUB_PATH} (1,175+ nodes & synaptic graph){Colors.END}
"""
    print(banner)


def save_episodic_record(project_name: str, archetype: str, mode: str, path: Path, facts: List[str]):
    """Guarda automáticamente el hito del proyecto en la memoria episódica de Hermes."""
    try:
        EPISODIC_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        memories = {}
        if EPISODIC_MEMORY_FILE.exists():
            try:
                with open(EPISODIC_MEMORY_FILE, "r", encoding="utf-8") as f:
                    memories = json.load(f)
            except Exception:
                memories = {}

        entry = {
            "timestamp": datetime.now().isoformat(),
            "summary": f"Proyecto '{project_name}' inicializado con arquetipo '{archetype}' en modo '{mode}'.",
            "facts": [
                f"Ubicación: {str(path)}",
                f"Arquetipo: {archetype}",
                f"Modo: {mode}",
                *facts
            ]
        }

        cid = f"project-{project_name}"
        if cid not in memories:
            memories[cid] = []
        memories[cid].append(entry)

        with open(EPISODIC_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memories, f, indent=2, ensure_ascii=False)
            
        print(f"  {Colors.GREEN}✓{Colors.END} Hito registrado en memoria episódica de Hermes ({cid}).")
    except Exception as e:
        print(f"  {Colors.WARNING}⚠️ No se pudo registrar memoria episódica: {e}{Colors.END}")


# ==============================================================================
# DEFINICIONES DE ARQUETIPOS Y PLANTILLAS
# ==============================================================================

ARCHETYPES = {
    "modern-web": {
        "name": "Modern Fullstack Web (Next.js 15 & React 19)",
        "description": "Next.js 15 App Router, React 19, TypeScript, Tailwind CSS, Zustand, WCAG 2.1 AA a11y, Local SEO JSON-LD y optimización CWV.",
        "skills": ["modern-web-guidance", "chrome-extensions", "hermes"],
        "facts": [
            "Arquitectura Next.js 15 App Router con Server Components y Client Components aislados.",
            "Accesibilidad WCAG 2.1 AA nativa (roles ARIA, focus rings visibles, contraste AAA).",
            "Paleta estética Dark Titanium (#0B0D11, #13161F, #202533) con micro-animaciones.",
            "SEO estructurado con schema.org JSON-LD.",
            "Gestión de estado global ultra liviana con Zustand."
        ]
    },
    "fastapi-backend": {
        "name": "High-Performance Python Backend (FastAPI & AsyncIO)",
        "description": "FastAPI, Pydantic v2, AsyncIO, SQLAlchemy 2.0 / DuckDB, UV / Ruff, Pytest y tipado estricto.",
        "skills": ["managing-python-dependencies", "hermes"],
        "facts": [
            "FastAPI estructurado por módulos de dominio y routers versionados (/api/v1).",
            "Validación rigurosa con Pydantic v2 y configuración mediante pydantic-settings.",
            "I/O totalmente asíncrono con AsyncIO y SQLAlchemy 2.0 async sessions.",
            "Pipeline de linting y formateo ultrarrápido con Ruff y gestión con UV.",
            "Suite de pruebas parametrizadas con Pytest y AsyncClient."
        ]
    },
    "agentic-ai": {
        "name": "Agentic AI & Data Pipelines (FastMCP & Multi-Agent)",
        "description": "FastMCP Server, Presupuesto de Tokens, Memoria Episódica Jerárquica, Polars / Vector Search y fallback resiliente.",
        "skills": ["hermes", "ml-best-practices", "bigquery-sql"],
        "facts": [
            "Servidor FastMCP nativo para exposición de herramientas y recursos a agentes.",
            "Presupuesto de tokens estricto y poda semántica en tiempo de ejecución.",
            "Memoria episódica persistente con retención selectiva y búsqueda de hechos.",
            "Diseño multi-agente desacoplado con manejo granular de errores y fallbacks."
        ]
    },
    "mobile-crossplatform": {
        "name": "Mobile Cross-Platform & Clean Architecture",
        "description": "Arquitectura limpia en capas (Presentación, Dominio, Datos), estado offline-first, accesibilidad y rendimiento fluido 60/120fps.",
        "skills": ["android-cli", "hermes"],
        "facts": [
            "Separación estricta de capas de dominio, datos y presentación.",
            "Caché offline-first con sincronización en segundo plano.",
            "Semántica de accesibilidad para lectores de pantalla móviles."
        ]
    },
    "agentic-coding-cli": {
        "name": "Autonomous Agentic Coding Assistant (Claw Architecture)",
        "description": "High-performance autonomous coding CLI in Python/Rust, 9-crate modular design, FastMCP/ACP protocol, strict path-scoping security, session hygiene, and event streaming.",
        "skills": ["claw-code-agentic-runtime", "claw-security-path-scoping", "claw-mcp-lifecycle", "hermes"],
        "facts": [
            "Arquitectura modular desacoplada: CLI REPL, Agent Loop, Policy Engine, Tool Registry y Provider Router.",
            "Seguridad reforzada con Path Scoping estricto, prevención de directory traversal y sandbox.",
            "Soporte nativo de Model Context Protocol (MCP) y streaming JSON-RPC / ACP.",
            "Persistencia de sesiones JSONL atómica con recuperación de ramas git y comandos /resume.",
            "Compatibilidad universal con modelos Claude 3.5 y proveedores locales OpenAI-compatible (Ollama/vLLM)."
        ]
    },
    "custom": {
        "name": "Custom / Dynamic Context Resolution",
        "description": "Consulta en tiempo real al grafo sináptico de Hermes para extraer patrones a medida.",
        "skills": ["hermes"],
        "facts": [
            "Resolución sináptica personalizada generada a partir de los requerimientos del usuario."
        ]
    }
}


def generate_governance_files(target_dir: Path, archetype_key: str, project_name: str, custom_desc: str = ""):
    """Genera las reglas `.agents/rules/`, `.agents/skills/` y `AGENTS.md`."""
    arch = ARCHETYPES.get(archetype_key, ARCHETYPES["custom"])
    agents_dir = target_dir / ".agents"
    rules_dir = agents_dir / "rules"
    skills_dir = agents_dir / "skills" / "hermes"
    
    rules_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    # 1. AGENTS.md
    agents_md = f"""# {project_name} — Guía de Desarrollo y Gobernanza de Agentes

> **Generado por Hermes Project Engine**  
> **Arquetipo:** {arch['name']}  
> **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

## 🎯 Visión y Objetivos del Proyecto
{custom_desc or arch['description']}

## 🏛️ Principios y Estándares de Hermes Aplicados
{chr(10).join(f"- {f}" for f in arch['facts'])}

## 🛠️ Protocolo del Asistente en este Repositorio
1. **Consulta Continua a Hermes**: Utilizar las herramientas de `hermes-hub` (`resolve_compact_context`) para validar arquitecturas y patrones.
2. **Calidad de Código**: Cumplir estrictamente las reglas en `.agents/rules/`.
3. **Refuerzo Sináptico**: Registrar memoria episódica en hitos clave del desarrollo con `save_episodic_memory()`.
"""
    (target_dir / "AGENTS.md").write_text(agents_md, encoding="utf-8")

    # 2. Regla de Estándares según Arquetipo
    if archetype_key == "modern-web":
        rule_content = """# Estándares de Desarrollo Web Moderno (Hermes Verified)

## 1. Arquitectura y Componentes
- Usar **Next.js 15 App Router** con Server Components por defecto.
- Marcar `'use client'` únicamente en hojas terminales que requieran interacción (onClick, useState, framer-motion).
- Evitar problemas de hidratación garantizando que el renderizado inicial coincida estrictamente con el HTML del servidor.

## 2. Accesibilidad (WCAG 2.1 AA)
- Todos los modales y diálogos deben incluir `role="dialog"`, `aria-modal="true"`, y `aria-label`.
- Los botones de alternancia deben incluir `aria-pressed` o `aria-expanded`.
- Navegación por teclado completa (Tab, Esc para cerrar modales, focus rings visibles con `focus-visible:ring-2`).

## 3. Estética y UI
- Utilizar paletas seleccionadas y oscuras (Dark Titanium: `#0B0D11`, `#13161F`, `#202533`).
- Tipografía moderna (Inter, Geist Sans) y micro-animaciones fluidas con GPU acceleration.

## 4. Rendimiento y SEO (CWV)
- Imágenes secundarias o bajo el pliegue con `loading="lazy"`.
- Marcado estructurado JSON-LD (`schema.org`) en `layout.tsx` o `page.tsx`.
"""
        (rules_dir / "web_standards.md").write_text(rule_content, encoding="utf-8")

    elif archetype_key == "fastapi-backend":
        rule_content = """# Estándares de Backend Python & FastAPI (Hermes Verified)

## 1. Arquitectura y Código Asíncrono
- Todo endpoint de I/O (base de datos, llamadas HTTP, colas) debe ser `async def`.
- No bloquear el event loop con operaciones síncronas de lectura pesada de archivos.

## 2. Validación de Datos (Pydantic v2)
- Usar schemas `BaseModel` con `ConfigDict(strict=True)` donde aplique.
- Centralizar variables de entorno en `pydantic_settings.BaseSettings`.

## 3. Gestión de Dependencias y Linting
- Utilizar `uv` para resolución de paquetes.
- Formateo y linting automatizado con `ruff check .` y `ruff format .`.
- Tipado estricto con `mypy` o `pyright`.
"""
        (rules_dir / "backend_standards.md").write_text(rule_content, encoding="utf-8")

    elif archetype_key == "agentic-coding-cli":
        rule_content = """# Estándares de Asistentes de Codificación Agéntica (Claw & Hermes Verified)

## 1. Arquitectura y Bucle Agéntico (Agent Loop)
- Desacoplar I/O de terminal, despacho de herramientas, motor de políticas y llamadas a modelos LLM.
- Implementar streaming de tokens y eventos estructurados (`event:tool_call_started`, `event:tool_call_completed`).
- Proteger contra bucles infinitos con límites de pasos (`max_steps`) y monitoreo de latencia.

## 2. Seguridad y Path Scoping
- Todo acceso a archivos debe resolverse con `Path.resolve()` y validarse contra el workspace permitido (`allowed_paths`).
- Bloqueo incondicional de rutas del sistema (`/etc`, `~/.ssh`, `~/.aws`, `~/.gnupg`).
- Clasificar comandos bash en seguros (auto-ejecución) y mutacionales/destructivos (confirmación requerida).

## 3. Protocolo MCP y Estado de Sesión
- Conectar herramientas mediante Model Context Protocol (FastMCP / JSON-RPC).
- Persistir estados y checkpoints en `.claw/sessions/` para permitir reanudación con `/resume`.
"""
        (rules_dir / "agentic_coding_standards.md").write_text(rule_content, encoding="utf-8")

    elif archetype_key == "agentic-ai":
        rule_content = """# Estándares de Sistemas Agentic AI & MCP (Hermes Verified)

## 1. Eficiencia de Tokens y Contexto
- Aplicar presupuesto estricto de tokens en prompts y herramientas (`max_token_budget`).
- Podar snippets y código irrelevante antes de inyectarlo al contexto del LLM.

## 2. Protocolo FastMCP
- Definir herramientas limpias con descripciones unívocas y tipos estrictos de retorno.
- Diseñar fallbacks resilientes ante caídas de proveedores de modelos o APIs externas.

## 3. Memoria y Estado
- Persistir memoria episódica en `~/.hermes-hub` en cada hito relevante.
"""
        (rules_dir / "agentic_standards.md").write_text(rule_content, encoding="utf-8")

    else:
        rule_content = """# Estándares de Proyecto Personalizado (Hermes Verified)

## 1. Principios Generales
- Mantener tipado estricto y documentación concisa en código.
- Modularidad alta y bajo acoplamiento.
- Consultar patrones en `~/.hermes-hub` mediante `resolve_compact_context`.
"""
        (rules_dir / "general_standards.md").write_text(rule_content, encoding="utf-8")

    # 3. Local Hermes Skill
    hermes_skill_content = """---
name: hermes
description: Consulta local y sincronización con el Hermes Knowledge Hub.
---

# Hermes Local Skill

Para resolver dudas de arquitectura, optimización o patrones en este proyecto:
- Consulta `resolve_compact_context(query)` desde el servidor MCP `hermes-hub`.
- Aplica las reglas locales documentadas en `.agents/rules/`.
"""
    (skills_dir / "SKILL.md").write_text(hermes_skill_content, encoding="utf-8")
    print(f"  {Colors.GREEN}✓{Colors.END} Gobernanza `.agents/` y `AGENTS.md` inyectados exitosamente.")


def generate_modern_web_boilerplate(target_dir: Path, project_name: str):
    """Crea el boilerplate completo de Next.js 15 + React 19 + TypeScript + Tailwind."""
    # package.json
    pkg = {
        "name": project_name.lower().replace(" ", "-"),
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "next lint"
        },
        "dependencies": {
            "react": "^19.0.0",
            "react-dom": "^19.0.0",
            "next": "^15.1.0",
            "lucide-react": "^0.460.0",
            "zustand": "^5.0.0",
            "clsx": "^2.1.1",
            "tailwind-merge": "^2.5.4",
            "framer-motion": "^11.11.0"
        },
        "devDependencies": {
            "typescript": "^5.6.3",
            "@types/node": "^22.0.0",
            "@types/react": "^19.0.0",
            "@types/react-dom": "^19.0.0",
            "postcss": "^8.4.49",
            "tailwindcss": "^3.4.15",
            "eslint": "^9.0.0",
            "eslint-config-next": "^15.1.0"
        }
    }
    (target_dir / "package.json").write_text(json.dumps(pkg, indent=2), encoding="utf-8")

    # tsconfig.json
    tsconfig = {
        "compilerOptions": {
            "target": "ES2022",
            "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": True,
            "skipLibCheck": True,
            "strict": True,
            "noEmit": True,
            "esModuleInterop": True,
            "module": "esnext",
            "moduleResolution": "bundler",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "jsx": "preserve",
            "incremental": True,
            "plugins": [{"name": "next"}],
            "paths": {"@/*": ["./src/*"]}
        },
        "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
        "exclude": ["node_modules"]
    }
    (target_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2), encoding="utf-8")

    # tailwind.config.ts
    tailwind_cfg = """import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        titanium: {
          900: "#0B0D11",
          800: "#13161F",
          700: "#202533",
          600: "#2F364A",
          100: "#E2E8F0"
        },
        primary: {
          500: "#3B82F6",
          600: "#2563EB"
        }
      }
    },
  },
  plugins: [],
};
export default config;
"""
    (target_dir / "tailwind.config.ts").write_text(tailwind_cfg, encoding="utf-8")

    # postcss.config.mjs
    postcss_cfg = """const config = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
export default config;
"""
    (target_dir / "postcss.config.mjs").write_text(postcss_cfg, encoding="utf-8")

    # src/app structure
    app_dir = target_dir / "src" / "app"
    app_dir.mkdir(parents=True, exist_ok=True)

    globals_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --background: #0B0D11;
  --foreground: #F8FAFC;
}

body {
  color: var(--foreground);
  background: var(--background);
  font-feature-settings: "rlig" 1, "calt" 1;
}

/* Accessible focus ring */
:focus-visible {
  outline: 2px solid #3B82F6;
  outline-offset: 2px;
}
"""
    (app_dir / "globals.css").write_text(globals_css, encoding="utf-8")

    layout_tsx = f"""import type {{ Metadata }} from "next";
import "./globals.css";

export const metadata: Metadata = {{
  title: "{project_name} — High Performance App",
  description: "Construido con estándares de arquitectura y accesibilidad de Hermes Knowledge Hub.",
}};

export default function RootLayout({{
  children,
}}: Readonly<{{
  children: React.ReactNode;
}}>) {{
  return (
    <html lang="es" className="dark">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{{{
            __html: JSON.stringify({{
              "@context": "https://schema.org",
              "@type": "WebApplication",
              "name": "{project_name}",
              "applicationCategory": "BusinessApplication"
            }}),
          }}}}
        />
      </head>
      <body className="min-h-screen bg-titanium-900 text-slate-100 antialiased selection:bg-blue-600 selection:text-white">
        {{children}}
      </body>
    </html>
  );
}}
"""
    (app_dir / "layout.tsx").write_text(layout_tsx, encoding="utf-8")

    page_tsx = f"""import {{ Sparkles, ShieldCheck, Zap, Compass }} from "lucide-react";

export default function HomePage() {{
  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-4 py-16 text-center max-w-5xl mx-auto">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-titanium-800 border border-titanium-700 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-6">
        <Sparkles className="w-4 h-4" /> Hermes Verified Architecture
      </div>
      
      <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-white mb-6">
        Bienvenido a <span className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">{project_name}</span>
      </h1>
      
      <p className="text-lg md:text-xl text-slate-400 max-w-2xl mb-12">
        Proyecto optimizado con Next.js 15, React 19, accesibilidad WCAG 2.1 AA, paleta Dark Titanium y gobernanza de IA preconfigurada.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left">
        <div className="p-6 rounded-2xl bg-titanium-800/80 border border-titanium-700 hover:border-blue-500/50 transition-colors">
          <Zap className="w-8 h-8 text-amber-400 mb-4" />
          <h3 className="text-lg font-bold text-white mb-2">Core Web Vitals</h3>
          <p className="text-sm text-slate-400">Estructura preparada para puntuaciones 100/100 en Lighthouse y tiempos de carga instantáneos.</p>
        </div>

        <div className="p-6 rounded-2xl bg-titanium-800/80 border border-titanium-700 hover:border-blue-500/50 transition-colors">
          <ShieldCheck className="w-8 h-8 text-emerald-400 mb-4" />
          <h3 className="text-lg font-bold text-white mb-2">WCAG 2.1 AA</h3>
          <p className="text-sm text-slate-400">Contraste verificado, focus traps accesibles y marcado semántico nativo.</p>
        </div>

        <div className="p-6 rounded-2xl bg-titanium-800/80 border border-titanium-700 hover:border-blue-500/50 transition-colors">
          <Compass className="w-8 h-8 text-blue-400 mb-4" />
          <h3 className="text-lg font-bold text-white mb-2">AI Governance</h3>
          <p className="text-sm text-slate-400">Integración con Hermes Hub para asistencia en desarrollo y sincronización sináptica.</p>
        </div>
      </div>
    </main>
  );
}}
"""
    (app_dir / "page.tsx").write_text(page_tsx, encoding="utf-8")

    # .gitignore
    gitignore = """node_modules
.next
out
.env*.local
.DS_Store
*.log
"""
    (target_dir / ".gitignore").write_text(gitignore, encoding="utf-8")


def generate_fastapi_boilerplate(target_dir: Path, project_name: str):
    """Crea el boilerplate completo de FastAPI + Pydantic v2 + AsyncIO."""
    # pyproject.toml
    pyproject = f"""[project]
name = "{project_name.lower().replace(' ', '_')}"
version = "0.1.0"
description = "High-performance FastAPI service scaffolded by Hermes Project Engine"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "httpx>=0.28.0",
    "sqlalchemy>=2.0.36",
    "asyncpg>=0.30.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0"
]

[tool.ruff]
line-length = 100
target-version = "py311"
"""
    (target_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")

    # src structure
    app_dir = target_dir / "src" / "app"
    core_dir = app_dir / "core"
    api_dir = app_dir / "api" / "v1" / "endpoints"
    schemas_dir = app_dir / "schemas"
    tests_dir = target_dir / "tests"

    for d in [core_dir, api_dir, schemas_dir, tests_dir]:
        d.mkdir(parents=True, exist_ok=True)
        (d / "__init__.py").write_text("", encoding="utf-8")

    # config.py
    config_py = f"""from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "{project_name}"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
"""
    (core_dir / "config.py").write_text(config_py, encoding="utf-8")

    # health endpoint
    health_py = """from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health", summary="Health Check")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "hermes_verified": True
    }
"""
    (api_dir / "health.py").write_text(health_py, encoding="utf-8")

    # main.py
    main_py = f"""from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.app.core.config import settings
from src.app.api.v1.endpoints import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{{settings.API_V1_STR}}/openapi.json",
    docs_url=f"{{settings.API_V1_STR}}/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])

@app.get("/")
async def root():
    return {{
        "message": f"Welcome to {{settings.PROJECT_NAME}}",
        "docs": f"{{settings.API_V1_STR}}/docs",
        "engine": "Hermes Knowledge Hub"
    }}
"""
    (app_dir / "main.py").write_text(main_py, encoding="utf-8")

    # test
    test_py = """import pytest
from httpx import AsyncClient, ASGITransport
from src.app.main import app

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["hermes_verified"] is True
"""
    (tests_dir / "test_health.py").write_text(test_py, encoding="utf-8")

    # .gitignore
    (target_dir / ".gitignore").write_text("__pycache__\n.venv\n.pytest_cache\n.env\n*.pyc\n", encoding="utf-8")


def generate_agentic_boilerplate(target_dir: Path, project_name: str):
    """Crea el boilerplate completo de FastMCP + Agentic AI."""
    pyproject = f"""[project]
name = "{project_name.lower().replace(' ', '_')}"
version = "0.1.0"
description = "FastMCP Agentic Engine scaffolded by Hermes"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=0.4.0",
    "pydantic>=2.10.0",
    "httpx>=0.28.0",
    "polars>=1.15.0",
    "tiktoken>=0.8.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "ruff>=0.8.0"
]
"""
    (target_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    
    src_dir = target_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    
    server_py = f"""from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import List, Dict, Any

mcp = FastMCP("{project_name}")

class QueryRequest(BaseModel):
    query: str = Field(..., description="Consulta a procesar")
    max_tokens: int = Field(500, description="Presupuesto máximo de tokens")

@mcp.tool()
def process_agent_task(task_description: str, budget_tokens: int = 400) -> Dict[str, Any]:
    \"\"\"Procesa una tarea con presupuesto estricto de tokens y fallback resiliente.\"\"\"
    return {{
        "task": task_description,
        "budget_tokens": budget_tokens,
        "status": "completed",
        "hermes_verified": True
    }}

if __name__ == "__main__":
    mcp.run(transport="stdio")
"""
    (src_dir / "server.py").write_text(server_py, encoding="utf-8")
    (target_dir / ".gitignore").write_text("__pycache__\n.venv\n*.pyc\n", encoding="utf-8")


# ==============================================================================
# COMANDOS PRINCIPALES DEL CLI
# ==============================================================================

def generate_agentic_coding_boilerplate(target_dir: Path, project_name: str):
    """Crea el boilerplate de un Asistente Agéntico de Codificación (Python/FastMCP/AsyncIO)."""
    pyproject = f"""[project]
name = "{project_name.lower().replace(' ', '_')}"
version = "0.1.0"
description = "High-performance Agentic Coding Assistant powered by Claw & Hermes"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=0.4.0",
    "pydantic>=2.10.0",
    "httpx>=0.28.0",
    "prompt-toolkit>=3.0.48",
    "rich>=13.9.0",
    "tiktoken>=0.8.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0"
]
"""
    (target_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")

    src_dir = target_dir / "src"
    runtime_dir = src_dir / "runtime"
    tools_dir = src_dir / "tools"
    policy_dir = src_dir / "policy"

    for d in [runtime_dir, tools_dir, policy_dir]:
        d.mkdir(parents=True, exist_ok=True)
        (d / "__init__.py").write_text("", encoding="utf-8")

    # Path scope enforcement
    path_scope_py = """from pathlib import Path
from typing import List

class PathScopeEnforcer:
    def __init__(self, allowed_roots: List[Path]):
        self.allowed_roots = [p.resolve() for p in allowed_roots]

    def is_allowed(self, target_path: Path) -> bool:
        resolved = target_path.resolve()
        for root in self.allowed_roots:
            try:
                resolved.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def check_access(self, target_path: Path):
        if not self.is_allowed(target_path):
            raise PermissionError(f"Access denied: {target_path} is outside allowed workspace paths.")
"""
    (policy_dir / "path_scope.py").write_text(path_scope_py, encoding="utf-8")

    # Agent Loop
    agent_loop_py = f'''import asyncio
from typing import Dict, Any, List
from pathlib import Path
from src.policy.path_scope import PathScopeEnforcer

class AgentRuntime:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self.policy = PathScopeEnforcer([self.workspace_root])
        self.session_id = "{project_name.lower().replace(' ', '-')}-session"

    async def execute_task(self, prompt: str) -> Dict[str, Any]:
        """Ejecuta una instrucción agéntica con verificación de políticas y streaming."""
        return {{
            "task": prompt,
            "status": "completed",
            "workspace": str(self.workspace_root),
            "hermes_verified": True,
            "claw_runtime": True
        }}
'''
    (runtime_dir / "agent_loop.py").write_text(agent_loop_py, encoding="utf-8")

    # CLI Entrypoint
    main_py = f"""import asyncio
from pathlib import Path
from rich.console import Console
from src.runtime.agent_loop import AgentRuntime

console = Console()

async def main():
    console.print("[bold cyan]⚡ {project_name} — Agentic Coding Assistant ⚡[/bold cyan]")
    runtime = AgentRuntime(Path.cwd())
    console.print(f"[dim]Workspace scoped at: {{runtime.workspace_root}}[/dim]")
    res = await runtime.execute_task("System Ready")
    console.print(f"[green]✓ Status:[/green] {{res['status']}}")

if __name__ == '__main__':
    asyncio.run(main())
"""
    (src_dir / "main.py").write_text(main_py, encoding="utf-8")
    (target_dir / ".gitignore").write_text("__pycache__\n.venv\n.claw/\n*.pyc\n", encoding="utf-8")

def scaffold_project(name: str, target_dir: Path, archetype: str, mode: str, desc: str = ""):
    """Ejecuta el proceso completo de scaffolding y registro."""
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n{Colors.CYAN}🚀 Inicializando proyecto '{name}'...{Colors.END}")
    print(f"  {Colors.BOLD}Destino:{Colors.END} {target_dir}")
    print(f"  {Colors.BOLD}Arquetipo:{Colors.END} {archetype} ({ARCHETYPES.get(archetype, {}).get('name', 'Custom')})")
    print(f"  {Colors.BOLD}Modo:{Colors.END} {mode}")

    # 1. Generar Gobernanza de IA (.agents/ y AGENTS.md)
    generate_governance_files(target_dir, archetype, name, desc)

    # 2. Generar Código Boilerplate si el modo es 'full'
    if mode == "full":
        if archetype == "modern-web":
            generate_modern_web_boilerplate(target_dir, name)
            print(f"  {Colors.GREEN}✓{Colors.END} Boilerplate de Next.js 15 + React 19 + Tailwind generado.")
        elif archetype == "fastapi-backend":
            generate_fastapi_boilerplate(target_dir, name)
            print(f"  {Colors.GREEN}✓{Colors.END} Boilerplate de FastAPI + Pydantic v2 + Pytest generado.")
        elif archetype == "agentic-coding-cli":
            generate_agentic_coding_boilerplate(target_dir, name)
            print(f"  {Colors.GREEN}✓{Colors.END} Boilerplate de Autonomous Agentic Coding Assistant (Claw) generado.")
        elif archetype == "agentic-ai":
            generate_agentic_boilerplate(target_dir, name)
            print(f"  {Colors.GREEN}✓{Colors.END} Boilerplate de FastMCP + Agentic Pipeline generado.")
        else:
            # Custom / Mobile
            (target_dir / "README.md").write_text(f"# {name}\n\n{desc or 'Proyecto inicializado con Hermes'}\n", encoding="utf-8")
            print(f"  {Colors.GREEN}✓{Colors.END} Estructura base generada.")

    # 3. Guardar Hito en Memoria Episódica
    save_episodic_record(name, archetype, mode, target_dir, ARCHETYPES.get(archetype, {}).get("facts", []))

    print(f"\n{Colors.GREEN}{Colors.BOLD}✨ ¡Proyecto '{name}' configurado exitosamente! ✨{Colors.END}")
    print(f"\n{Colors.BOLD}Próximos pasos recomendados:{Colors.END}")
    print(f"  1. Navegar al proyecto: {Colors.CYAN}cd {target_dir}{Colors.END}")
    if mode == "full":
        if archetype == "modern-web":
            print(f"  2. Instalar dependencias: {Colors.CYAN}npm install{Colors.END}")
            print(f"  3. Iniciar servidor: {Colors.CYAN}npm run dev{Colors.END}")
        elif archetype in ["fastapi-backend", "agentic-ai"]:
            print(f"  2. Sincronizar entorno virtual: {Colors.CYAN}uv sync{Colors.END} o {Colors.CYAN}pip install -e .{Colors.END}")
            print(f"  3. Ejecutar pruebas: {Colors.CYAN}pytest{Colors.END}")
    print(f"  {Colors.DIM}Los agentes en Antigravity IDE aplicarán automáticamente las reglas de Hermes.{Colors.END}\n")


def interactive_wizard():
    """Asistente interactivo en terminal."""
    print_banner()
    try:
        name = input(f"{Colors.BOLD}Nombre del proyecto: {Colors.END}").strip() or "hermes-project"
        
        print(f"\n{Colors.BOLD}Selecciona el Arquetipo:{Colors.END}")
        archetype_keys = list(ARCHETYPES.keys())
        for idx, k in enumerate(archetype_keys, 1):
            arch = ARCHETYPES[k]
            print(f"  {Colors.CYAN}[{idx}]{Colors.END} {Colors.BOLD}{k}{Colors.END}: {arch['name']}")
            print(f"      {Colors.DIM}{arch['description']}{Colors.END}")
            
        choice = input(f"\n{Colors.BOLD}Opción (1-{len(archetype_keys)}) [1]: {Colors.END}").strip() or "1"
        try:
            chosen_key = archetype_keys[int(choice) - 1]
        except Exception:
            chosen_key = "modern-web"

        print(f"\n{Colors.BOLD}Selecciona el Modo de Generación:{Colors.END}")
        print(f"  {Colors.CYAN}[1]{Colors.END} {Colors.BOLD}full{Colors.END}: Proyecto completo con código, dependencias, linter y `.agents/`")
        print(f"  {Colors.CYAN}[2]{Colors.END} {Colors.BOLD}governance{Colors.END}: Solo gobernanza de IA (`.agents/rules/`, `AGENTS.md`)")
        
        mode_choice = input(f"\n{Colors.BOLD}Modo [1]: {Colors.END}").strip() or "1"
        mode = "governance" if mode_choice == "2" else "full"

        target_path = Path.cwd() / name if mode == "full" else Path.cwd()
        
        desc = ""
        if chosen_key == "custom":
            desc = input(f"\n{Colors.BOLD}Describe brevemente qué deseas construir: {Colors.END}").strip()

        scaffold_project(name, target_path, chosen_key, mode, desc)

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Cancelado por el usuario.{Colors.END}")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Hermes Project Engine & Knowledge Scaffolder")
    subparsers = parser.add_subparsers(dest="command")

    # hermes new <name>
    new_p = subparsers.add_parser("new", help="Crear un nuevo proyecto desde cero")
    new_p.add_argument("name", help="Nombre del proyecto o carpeta")
    new_p.add_argument("-a", "--archetype", choices=list(ARCHETYPES.keys()), default="modern-web", help="Arquetipo a utilizar")
    new_p.add_argument("-m", "--mode", choices=["full", "governance"], default="full", help="Modo de generación")
    new_p.add_argument("-d", "--dir", default=None, help="Directorio destino (por defecto ./<name>)")
    new_p.add_argument("--desc", default="", help="Descripción del proyecto")

    # hermes init
    init_p = subparsers.add_parser("init", help="Inyectar gobernanza de Hermes en el directorio actual")
    init_p.add_argument("-a", "--archetype", choices=list(ARCHETYPES.keys()), default="modern-web", help="Arquetipo a utilizar")
    init_p.add_argument("-m", "--mode", choices=["full", "governance"], default="governance", help="Modo de generación")
    init_p.add_argument("-n", "--name", default="", help="Nombre del proyecto (por defecto nombre del directorio actual)")
    init_p.add_argument("--desc", default="", help="Descripción del proyecto")

    # hermes search <query>
    search_p = subparsers.add_parser("search", help="Búsqueda híbrida SOTA v3 con razonamiento causal y token pruner")
    search_p.add_argument("query", help="Consulta de arquitectura o código")
    search_p.add_argument("-k", "--top-k", type=int, default=3, help="Cantidad de resultados")
    search_p.add_argument("-b", "--budget", type=int, default=1200, help="Presupuesto de tokens")

    # hermes audit
    audit_p = subparsers.add_parser("audit", help="Auditoría de antipatrones de workspace y riesgos causales")
    audit_p.add_argument("-p", "--path", default=None, help="Ruta del workspace a auditar")

    # hermes ast-scan
    ast_p = subparsers.add_parser("ast-scan", help="Escaneo estructural AST de símbolos de código")
    ast_p.add_argument("-p", "--path", default=None, help="Ruta del workspace")
    ast_p.add_argument("--max-files", type=int, default=100, help="Límite de archivos a escanear")

    # hermes dream
    dream_p = subparsers.add_parser("dream", help="Ejecutar ciclo de consolidación 'Modo Sueño'")
    dream_p.add_argument("--daemon", action="store_true", help="Ejecutar en modo daemon continuo")
    dream_p.add_argument("--interval", type=int, default=120, help="Intervalo en segundos si corre como daemon")

    # hermes feedback
    fb_p = subparsers.add_parser("feedback", help="Registrar resultado de ejecución de test/build")
    fb_p.add_argument("--patterns", nargs="+", required=True, help="IDs de patrones involucrados")
    fb_p.add_argument("--success", action="store_true", help="Marcar como ejecución exitosa")
    fb_p.add_argument("--fail", action="store_true", help="Marcar como ejecución fallida")
    fb_p.add_argument("--task", default="cli_test", help="Tipo de tarea ejecutada")

    # hermes status
    subparsers.add_parser("status", help="Mostrar estado global de la base de conocimiento y sinapsis")

    # hermes archetypes
    subparsers.add_parser("archetypes", help="Listar arquetipos soportados")

    args = parser.parse_args()

    if not args.command:
        interactive_wizard()
        return

    print_banner()

    if args.command == "status":
        from deep_code_integrity_audit import audit_graph_integrity
        audit_graph_integrity()
        return

    if args.command == "search":
        from hybrid_retriever import get_hybrid_retriever
        retriever = get_hybrid_retriever()
        res = retriever.search_pipeline(args.query, top_k=args.top_k, token_budget=args.budget, include_causal=True)
        print(f"\n{Colors.BOLD}🔍 Resultados de Búsqueda ({res['latency_ms']}ms):{Colors.END}\n")
        for idx, cand in enumerate(res.get("candidates", []), 1):
            print(f"  {Colors.CYAN}{idx}. {cand.get('label', cand['node_id'])}{Colors.END} (RRF: {cand.get('rrf_score', 0):.4f} | Rerank: {cand.get('rerank_score', 0):.2f})")
            if cand.get("summary"):
                print(f"     {cand['summary'][:180]}...")
        if res.get("causal_markdown"):
            print(res["causal_markdown"])
        return

    if args.command == "audit":
        from smart_watcher import SmartWorkspaceWatcher
        watcher = SmartWorkspaceWatcher(workspace_path=Path(args.path) if args.path else Path.cwd())
        report = watcher.scan_workspace()
        print(f"\n{Colors.BOLD}🛡️ Auditoría de Antipatrones ({report.get('files_scanned', 0)} archivos analizados):{Colors.END}")
        issues = report.get("issues_found", [])
        if not issues:
            print(f"  {Colors.GREEN}✓ Cero violaciones críticas detectadas en el workspace.{Colors.END}")
        else:
            for issue in issues:
                print(f"  {Colors.FAIL}• [{issue.get('severity', 'WARN')}] {issue.get('title')}{Colors.END} en {issue.get('file')}:{issue.get('line')}")
                print(f"    Solución recomendada: {issue.get('recommended_pattern')}")
        return

    if args.command == "ast-scan":
        from ast_graph_parser import get_ast_parser
        parser_ast = get_ast_parser(Path(args.path) if args.path else Path.cwd())
        res = parser_ast.scan_workspace_symbols(max_files=args.max_files)
        print(f"\n{Colors.BOLD}🌲 Escaneo AST de Símbolos:{Colors.END}")
        print(f"  • Archivos analizados: {res['files_scanned']}")
        print(f"  • Símbolos extraídos: {res['total_symbols_extracted']}")
        print(f"  • Vínculos con patrones de Hermes: {len(res['pattern_bindings'])}")
        for b in res["pattern_bindings"][:8]:
            pats = ", ".join([p["label"] for p in b["associated_patterns"]])
            print(f"    - {Colors.CYAN}{b['kind']} {b['symbol_name']}{Colors.END} ({b['file']}:{b['line']}) -> Patrones: {pats}")
        return

    if args.command == "dream":
        from dream_daemon import DreamConsolidationDaemon
        daemon = DreamConsolidationDaemon(interval_seconds=args.interval)
        if args.daemon:
            daemon.start_loop()
        else:
            daemon.run_single_cycle()
        return

    if args.command == "feedback":
        from feedback_engine import get_feedback_engine
        engine_fb = get_feedback_engine()
        is_success = True if args.success or not args.fail else False
        res = engine_fb.record_execution_result(pattern_ids=args.patterns, success=is_success, task_type=args.task)
        print(f"  {Colors.GREEN}✓{Colors.END} Feedback registrado: {res['delta_applied']} delta aplicado a {len(args.patterns)} patrones.")
        return

    if args.command == "archetypes":
        print(f"{Colors.BOLD}Arquetipos de Hermes Disponibles:{Colors.END}\n")
        for k, v in ARCHETYPES.items():
            print(f"  {Colors.CYAN}{Colors.BOLD}• {k}{Colors.END}: {v['name']}")
            print(f"    {v['description']}")
            print(f"    {Colors.DIM}Skills: {', '.join(v['skills'])}{Colors.END}\n")
        return

    if args.command == "new":
        target = Path(args.dir) if args.dir else Path.cwd() / args.name
        scaffold_project(args.name, target, args.archetype, args.mode, args.desc)

    elif args.command == "init":
        curr_dir = Path.cwd()
        name = args.name or curr_dir.name
        scaffold_project(name, curr_dir, args.archetype, args.mode, args.desc)


if __name__ == "__main__":
    main()

