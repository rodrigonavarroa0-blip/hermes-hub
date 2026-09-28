#!/usr/bin/env python3
"""
ingest_ai_parameters_encyclopedia.py
Investiga e ingesta la enciclopedia exhaustiva de Parámetros de Inteligencia Artificial en Hermes Hub.
Cubre: Inferencia y Muestreo Estocástico, Modelos de Razonamiento CoT, Hiperparámetros de Fine-Tuning (LoRA/DPO),
Servidores de Inferencia / VRAM (vLLM/SGLang), Cuantización y Parámetros Agénticos.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
GRAPH_FILE = CONFIG_DIR / "graph.json"

AI_PARAMETER_ITEMS = [
    # =========================================================
    # 1. INFERENCE & SAMPLING PARAMETERS
    # =========================================================
    {
        "id": "concept_ai_sampling_parameters",
        "category": "concepts/ai_parameters",
        "type": "concept",
        "cluster": "cluster_ai_parameters",
        "title": "LLM Sampling & Decoding Parameters (Temperature, Top-P, Top-K, Min-P)",
        "keywords": ["temperature", "top_p", "top_k", "min_p", "sampling_parameters", "softmax_entropy", "nucleus_sampling", "decoding_strategies"],
        "content": """---
id: concept_ai_sampling_parameters
title: LLM Sampling & Decoding Parameters (Temperature, Top-P, Top-K, Min-P)
type: concept
cluster: cluster_ai_parameters
category: ai_parameters
keywords: [temperature, top_p, top_k, min_p, sampling_parameters, softmax_entropy, nucleus_sampling, decoding_strategies]
---

# LLM Sampling & Decoding Parameters: Fundamentos Matemáticos y Guía Técnica

## 📌 1. Temperature ($T$)
La temperatura escala los logits crudos $z_i$ de la capa final antes de aplicar la función Softmax:

$$P(w_i) = \\frac{\\exp(z_i / T)}{\\sum_{j} \\exp(z_j / T)}$$

### Impacto y Valores Recomendados:
- **$T = 0.0$ (Argmax / Greedy Search)**: Determinismo puro. Siempre selecciona el token con mayor probabilidad. Ideal para extracción estructurada, SQL, JSON y razonamiento matemático estricto.
- **$T = 0.2 - 0.4$**: Salida altamente factual y consistente con ligeras variaciones léxicas. Ideal para agentes de código, análisis de datos y RAG.
- **$T = 0.7 - 0.9$**: Balance estándar para redacción general, asistencia conversacional y síntesis creativa.
- **$T \ge 1.2$**: Alta entropía. Aumenta la diversidad pero incrementa drásticamente el riesgo de alucinaciones y sintaxis rota.

---

## 📌 2. Top-P (Nucleus Sampling)
Selecciona el conjunto más pequeño de tokens cuya suma de probabilidades acumulada supere el umbral $p$:

$$\\sum_{i \\in V^{(p)}} P(w_i) \\ge p$$

- **Rango típico**: `0.85` a `0.95`.
- **Efecto**: Corta la "cola larga" de tokens con probabilidad infinitesimal sin imponer un número fijo de candidatos.

---

## 📌 3. Top-K
Fija un límite estricto de exactamente los $K$ tokens más probables antes del muestreo:
- **$K = 1$**: Equivalente a Greedy Decoding.
- **$K = 40 - 50$**: Valor común en motores de inferencia locales (Llama.cpp, Ollama).
- **Limitación**: Inflexible frente a distribuciones planas o muy puntiagudas.

---

## 📌 4. Min-P (El Nuevo Estándar Superior a Top-P)
**Min-P** escala el umbral mínimo relativo a la probabilidad del token número 1 ($P_{max}$):

$$P_{threshold} = \\text{min\\_p} \\times P_{max}$$

Solo se consideran los tokens cuya probabilidad sea al menos una fracción fija del mejor token:
- **Ventaja crítica**: Cuando el modelo está 99% seguro de una respuesta, solo considera ese token (cero ruido). Cuando el modelo tiene dudas legítimas, abre el abanico proporcionalmente.
- **Valor recomendado**: `min_p = 0.05` a `0.10`.
"""
    },
    {
        "id": "concept_penalties_repetition_logit_bias",
        "category": "concepts/ai_parameters",
        "type": "concept",
        "cluster": "cluster_ai_parameters",
        "title": "Repetition Penalties, Frequency/Presence Penalties & Logit Bias",
        "keywords": ["presence_penalty", "frequency_penalty", "repetition_penalty", "logit_bias", "token_suppression", "infinite_loops"],
        "content": """---
id: concept_penalties_repetition_logit_bias
title: Penalties & Logit Bias: Control Anti-Repetición y Modificación de Logits
type: concept
cluster: cluster_ai_parameters
category: ai_parameters
keywords: [presence_penalty", "frequency_penalty", "repetition_penalty", "logit_bias", "token_suppression", "infinite_loops]
---

# Penalizaciones Anti-Repetición y Logit Bias

## 📌 1. Presence Penalty vs Frequency Penalty (Estilo OpenAI / vLLM)

Los logits de cada token $k$ se ajustan según su historial en el contexto generado:

$$z'_k = z_k - (\\text{presence\\_penalty} \\cdot \\mathbb{I}_{c_k > 0}) - (\\text{frequency\\_penalty} \\cdot c_k)$$

Donde $c_k$ es la cantidad de veces que el token $k$ ya ha aparecido en la respuesta.

| Parámetro | Rango Típico | Comportamiento |
| :--- | :--- | :--- |
| **`presence_penalty`** | `0.0` a `2.0` (Recom: `0.1 - 0.5`) | Penalización binaria. Penaliza a cualquier token que ya haya aparecido al menos 1 vez, incentivando introducir **temas y conceptos nuevos**. |
| **`frequency_penalty`** | `0.0` a `2.0` (Recom: `0.1 - 0.3`) | Penalización proporcional. Penaliza más fuerte a tokens que se repiten con alta frecuencia (ideal para evitar bucles infinitos en listas). |

---

## 📌 2. Repetition Penalty (Estilo Hugging Face / LLaMA)
Aplica una penalización multiplicativa sobre los logits:

$$z'_k = \\begin{cases} z_k / \\theta & \\text{si } z_k > 0 \\\\ z_k \\cdot \\theta & \\text{si } z_k \\le 0 \\end{cases}$$

- **Valor neutro**: $\\theta = 1.0$.
- **Valor óptimo**: $\\theta = 1.05 - 1.15$.
- ⚠️ **Peligro**: Si $\\theta > 1.25$, el modelo evitará usar artículos gramaticales esenciales ("el", "la", "de"), destruyendo la coherencia del lenguaje.

---

## 📌 3. Logit Bias & Logit Processors
Permite alterar los logits de tokens específicos antes del muestreo:
- `logit_bias: {"1234": -100}`: **Prohíbe completamente** el token `1234` (ej. censurar palabras o secuencias).
- `logit_bias: {"5678": 100}`: **Fuerza la emisión** inmediata del token `5678`.
"""
    },

    # =========================================================
    # 2. REASONING & EXTENDED THINKING PARAMETERS
    # =========================================================
    {
        "id": "concept_reasoning_parameters_cot",
        "category": "concepts/ai_parameters",
        "type": "concept",
        "cluster": "cluster_ai_parameters",
        "title": "Reasoning Models Parameters: Reasoning Effort & Thinking Budget (o1, o3, Claude 3.7, DeepSeek-R1)",
        "keywords": ["reasoning_effort", "thinking_budget", "max_thinking_tokens", "chain_of_thought", "o1", "o3_mini", "claude_3_7_sonnet", "deepseek_r1"],
        "content": """---
id: concept_reasoning_parameters_cot
title: Reasoning & Extended Thinking Parameters (o1, o3-mini, Claude 3.7, DeepSeek-R1)
type: concept
cluster: cluster_ai_parameters
category: ai_parameters
keywords: [reasoning_effort, thinking_budget, max_thinking_tokens, chain_of_thought, o1, o3_mini, claude_3_7_sonnet, deepseek_r1]
---

# Parámetros de Modelos de Razonamiento (CoT & Extended Thinking)

## 📌 1. `reasoning_effort` (OpenAI o1 / o3-mini)
Controla la cantidad de tokens de pensamiento interno (*Hidden Chain of Thought*) generados antes de producir la respuesta visible:

- **`low`**: Menor latencia y costo. Ideal para tareas de refactorización simple o resolución de bugs evidentes.
- **`medium`** (Default): Balance óptimo para arquitectura, análisis de dependencias y debugging multi-archivo.
- **`high`**: Máxima profundidad deductiva. Utiliza árboles de búsqueda MCTS y backtracking para problemas de concurrencia complejos, optimizaciones de algoritmos $O(N)$ y pruebas matemáticas.

---

## 📌 2. `thinking.budget_tokens` / `max_thinking_tokens` (Anthropic Claude 3.7 Sonnet)
Permite especificar el número exacto de tokens de razonamiento asignados al modelo:

```python
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-7-sonnet-20250219",
    max_tokens=4096,
    thinking={
        "type": "enabled",
        "budget_tokens": 2048  # Presupuesto para razonamiento interno
    },
    messages=[{"role": "user", "content": "Diseña un algoritmo de consenso distribuido tolerante a fallos bizantinos."}]
)
```

---

## ⚠️ Regla de Oro: Temperature en Modelos de Razonamiento
- En modelos con razonamiento extendido (o1, DeepSeek-R1, Claude 3.7 Thinking), **NO debe alterarse `temperature = 0.0`**, ya que el razonamiento requiere diversidad estocástica en la búsqueda interna para podar ramas erróneas. Debe dejarse en su valor nativo (`temperature = 1.0`).
"""
    },

    # =========================================================
    # 3. FINE-TUNING & ALIGNMENT HYPERPARAMETERS
    # =========================================================
    {
        "id": "concept_lora_qlora_hyperparameters",
        "category": "concepts/ai_parameters",
        "type": "concept",
        "cluster": "cluster_ai_parameters",
        "title": "LoRA & QLoRA Hyperparameters (Rank r, Alpha, Dropout, Target Modules)",
        "keywords": ["lora_r", "lora_alpha", "lora_dropout", "target_modules", "qlora", "peft", "fine_tuning", "rank_stabilization"],
        "content": """---
id: concept_lora_qlora_hyperparameters
title: Hiperparámetros de LoRA y QLoRA (Rank, Alpha, Dropout y Módulos)
type: concept
cluster: cluster_ai_parameters
category: ai_parameters
keywords: [lora_r, lora_alpha, lora_dropout, target_modules, qlora, peft, fine_tuning, rank_stabilization]
---

# Hiperparámetros de LoRA y QLoRA (Low-Rank Adaptation)

## 📌 1. `lora_r` (Intrinsic Rank)
Define la dimensionalidad de las matrices de bajo rango $A \\in \\mathbb{R}^{d \\times r}$ y $B \\in \\mathbb{R}^{r \\times k}$:

$$W' = W_0 + \\Delta W = W_0 + \\frac{\\alpha}{r} (B \\cdot A)$$

- **$r = 8 - 16$**: Óptimo para ajuste de estilo, extracción de entidades y clasificación.
- **$r = 32 - 64$**: Recomendado para inyección de nuevo conocimiento de dominio (código, medicina, leyes).
- **$r > 128$**: Casi nunca mejora la métrica y satura VRAM innecesariamente.

---

## 📌 2. `lora_alpha` ($\alpha$ Scaling Factor)
Controla la magnitud del impacto de la actualización $\\Delta W$ sobre los pesos congelados $W_0$:
- **Regla estándar de oro**: Fijar $\\alpha = 2 \\times r$ (ej. si $r=32$, $\\alpha=64$).
- **Rank-Stabilized LoRA (rsLoRA)**: Escala por $\\frac{\\alpha}{\\sqrt{r}}$ permitiendo estabilidad numérica con ranks muy altos.

---

## 📌 3. `target_modules`
Define qué capas de atención y MLP recibirán adaptadores LoRA:
- **Mínimo**: `["q_proj", "v_proj"]`.
- **Completo (All-Linear - Altamente Recomendado)**: `["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`. Brinda hasta un 25% mejor convergencia que solo adaptar atención.
"""
    },
    {
        "id": "concept_dpo_rlhf_alignment_parameters",
        "category": "concepts/ai_parameters",
        "type": "concept",
        "cluster": "cluster_ai_parameters",
        "title": "DPO, KTO & RLHF Alignment Parameters (Beta, Loss Types & KL Penalty)",
        "keywords": ["dpo_beta", "rlhf", "preference_optimization", "kto", "kl_divergence", "alignment", "reward_modeling"],
        "content": """---
id: concept_dpo_rlhf_alignment_parameters
title: Parámetros de Alineamiento DPO, KTO y RLHF (Beta y Pérdidas)
type: concept
cluster: cluster_ai_parameters
category: ai_parameters
keywords: [dpo_beta, rlhf, preference_optimization, kpto, kl_divergence, alignment, reward_modeling]
---

# Parámetros de Alineamiento: DPO y RLHF

## 📌 1. `beta` (DPO Regularization Parameter)
En **Direct Preference Optimization (DPO)**, $\\beta$ controla qué tan estricta es la penalización de divergencia KL con respecto al modelo de referencia original $\\pi_{ref}$:

$$\\mathcal{L}_{DPO}(\\pi_\\theta; \\pi_{ref}) = -\\mathbb{E}_{(x, y_w, y_l)} \\left[ \\log \\sigma \\left( \\beta \\log \\frac{\\pi_\\theta(y_w|x)}{\\pi_{ref}(y_w|x)} - \\beta \\log \\frac{\\pi_\\theta(y_l|x)}{\\pi_{ref}(y_l|x)} \\right) \\right]$$

- **$\\beta = 0.1$ (Default estándar)**: Balance óptimo entre aprender las preferencias y no olvidar el conocimiento general.
- **$\\beta = 0.01 - 0.05$**: Permite cambios más agresivos (usar solo con datasets de preferencias de altísima pureza).
- **$\\beta = 0.2 - 0.5$**: Muy conservador. Evita degradación en benchmarks matemáticos.

---

## 📌 2. `loss_type`
- **`sigmoid`**: Formulación DPO estándar.
- **`ipo` (Identity Preference Optimization)**: Evita sobreajuste cuando los datos de preferencia tienen ruido.
- **`kto` (Kahneman-Tversky Optimization)**: Modela aversión a la pérdida sobre datos de pulgar arriba / pulgar abajo binarios.
"""
    },

    # =========================================================
    # 4. INFERENCE ENGINES, HARDWARE & VRAM PARAMETERS
    # =========================================================
    {
        "id": "concept_vllm_sglang_serving_parameters",
        "category": "concepts/ai_parameters",
        "type": "concept",
        "cluster": "cluster_ai_parameters",
        "title": "vLLM & SGLang High-Performance Serving Parameters (VRAM, Block Size, TP)",
        "keywords": ["gpu_memory_utilization", "block_size", "max_model_len", "tensor_parallel_size", "kv_cache_dtype", "vllm_parameters", "sglang"],
        "content": """---
id: concept_vllm_sglang_serving_parameters
title: Parámetros de Servidores de Inferencia vLLM y SGLang
type: concept
cluster: cluster_ai_parameters
category: ai_parameters
keywords: [gpu_memory_utilization, block_size, max_model_len, tensor_parallel_size, kv_cache_dtype, vllm_parameters, sglang]
---

# Parámetros de Inferencia en Servidores vLLM y SGLang

## 📌 1. `gpu_memory_utilization`
Porcentaje total de memoria VRAM asignada al proceso (Pesos del modelo + KV Cache):
- **Valor por defecto**: `0.90` (90% de VRAM).
- **En producción**: `0.92 - 0.95`. Deja un 5-8% libre para operaciones temporales de PyTorch y CUDA context.

---

## 📌 2. `max_model_len`
Define el límite superior de la ventana de contexto admitida por el servidor:
- ⚠️ Si se fija a `128000` (128k), el servidor reservará mucha más memoria por slot, reduciendo el número de peticiones concurrentes.
- **Recomendación**: Configurar al tamaño real requerido por la aplicación (ej. `8192` o `16384`) para maximizar el throughput.

---

## 📌 3. `block_size` (PagedAttention)
Tamaño en tokens de cada página física en VRAM:
- **`16`**: Menor fragmentación interna para prompts cortos.
- **`32`**: Mayor eficiencia de throughput en GPUs modernas (A100 / H100).

---

## 📌 4. `tensor_parallel_size` (`tp`)
Número de GPUs sobre las que se divide el modelo mediante paralelismo tensorial:
- Llama-3-70B: `tp = 4` (4x RTX 4090 o 4x A100) o `tp = 2` (2x H100 80GB).
"""
    },
    {
        "id": "concept_quantization_parameters",
        "category": "concepts/ai_parameters",
        "type": "concept",
        "cluster": "cluster_ai_parameters",
        "title": "Quantization Parameters (AWQ, GPTQ, BitsAndBytes 4/8-bit, FP8 E4M3 vs E5M2)",
        "keywords": ["awq", "gptq", "bitsandbytes", "fp8", "e4m3", "e5m2", "group_size", "weight_quantization", "vram_reduction"],
        "content": """---
id: concept_quantization_parameters
title: Parámetros de Cuantización (AWQ, GPTQ, BitsAndBytes, FP8)
type: concept
cluster: cluster_ai_parameters
category: ai_parameters
keywords: [awq, gptq, bitsandbytes, fp8, e4m3, e5m2, group_size, weight_quantization, vram_reduction]
---

# Parámetros de Cuantización y Compresión de Pesos

## 📌 1. Tipos de Cuantización de Pesos y Activaciones
| Método | Precisión | Hardware Óptimo | Pérdida de Perplejidad |
| :--- | :--- | :--- | :--- |
| **FP8 (E4M3)** | 8-bit Float | NVIDIA Hopper (H100/L40S) / Ada Lovelace | $< 0.01$ (Cero degradación) |
| **AWQ (Activation-aware)** | 4-bit Int | Todas las GPUs modernas (vLLM, TGI) | $< 0.05$ (Excelente retención) |
| **GPTQ** | 4-bit Int | Inferencia batch en GPUs de consumo | $< 0.08$ |
| **BitsAndBytes (NF4)** | 4-bit NormalFloat | Fine-tuning (QLoRA) en 1 sola GPU | $< 0.06$ |

---

## 📌 2. `group_size` (AWQ / GPTQ)
Determina la cantidad de pesos que comparten la misma escala y factor de punto cero:
- **`group_size = 128`**: Estándar de la industria. Excelente balance entre compresión y calidad de generación.
- **`group_size = 32`**: Mayor fidelidad matemática a expensas de un 10% más de VRAM.
"""
    },

    # =========================================================
    # 5. AGENTIC ORCHESTRATION & TOOL CALLING PARAMETERS
    # =========================================================
    {
        "id": "concept_agentic_loop_parameters",
        "category": "concepts/ai_parameters",
        "type": "concept",
        "cluster": "cluster_ai_parameters",
        "title": "Agentic Loop Parameters (Tool Choice, Parallel Tool Calls, Recursion Limits)",
        "keywords": ["tool_choice", "parallel_tool_calls", "recursion_limit", "max_iterations", "agent_sentinels", "react_budget"],
        "content": """---
id: concept_agentic_loop_parameters
title: Parámetros de Control y Ejecución en Agentes Autónomos
type: concept
cluster: cluster_ai_parameters
category: ai_parameters
keywords: [tool_choice, parallel_tool_calls, recursion_limit, max_iterations, agent_sentinels, react_budget]
---

# Parámetros de Orquestación Agéntica

## 📌 1. `tool_choice`
Modo de invocación de herramientas en la API del LLM:
- **`auto`**: El modelo decide autónomamente si responde con texto o llama a una herramienta.
- **`required` / `any`**: Obliga al modelo a llamar al menos a una herramienta antes de responder al usuario.
- **`{"type": "function", "function": {"name": "get_weather"}}`**: Fuerza el uso exclusivo de una función específica.

---

## 📌 2. `parallel_tool_calls`
- **`True`** (Default en GPT-4o / Claude 3.5): El modelo genera múltiples llamadas a herramientas en un único turno (ej. buscar 3 archivos en paralelo). Reduce drásticamente la latencia total.
- **`False`**: Fuerza la ejecución secuencial estricta paso a paso (útil cuando el resultado de la herramienta 2 depende estrictamente del resultado de la herramienta 1).

---

## 📌 3. Centinelas de Presupuesto (`recursion_limit` & `max_iterations`)
- **`recursion_limit` (LangGraph / CrewAI)**: Máximo número de transiciones entre nodos antes de abortar el flujo con error controlado (ej. `25`).
- **`max_tokens_budget` (Hermes Compact Resolution)**: Límite estricto de tokens de contexto para evitar desbordamiento de ventana.
"""
    }
]

CLUSTERS = {
    "cluster_ai_parameters": {
        "type": "cluster",
        "label": "🎛️ AI Parameters & Hyperparameters Encyclopedia",
        "file": "",
        "keywords": ["temperature", "top_p", "min_p", "lora_r", "lora_alpha", "dpo_beta", "gpu_memory_utilization", "reasoning_effort", "tool_choice"]
    }
}


def ingest_parameters():
    print("🚀 Ingeriendo Enciclopedia Exhaustiva de Parámetros de IA...")

    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    nodes: Dict[str, Any] = graph.get("nodes", {})
    edges: List[Dict[str, Any]] = graph.get("edges", [])

    # Registrar cluster
    for cid, cdata in CLUSTERS.items():
        if cid not in nodes:
            nodes[cid] = cdata
            print(f"  📁 Cluster registrado: {cid}")

    # Escribir archivos de parámetros
    for item in AI_PARAMETER_ITEMS:
        nid = item["id"]
        cat = item["category"]
        file_name = f"{nid.replace('concept_', '').replace('skill_', '').replace('pattern_', '')}.md"
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

        # Conectar al cluster
        edges.append({
            "source": item["cluster"],
            "target": nid,
            "weight": 0.95,
            "relation": "contains"
        })
        print(f"  📄 Documento OK: [{item['type'].upper()}] {nid} -> {rel_file}")

    graph["nodes"] = nodes
    graph["edges"] = edges

    with open(GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Se registraron {len(AI_PARAMETER_ITEMS)} conceptos exhaustivos de Parámetros de IA.")


if __name__ == "__main__":
    ingest_parameters()
