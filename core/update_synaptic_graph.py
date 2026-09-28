#!/usr/bin/env python3
"""
update_synaptic_graph.py - Actualiza SynapticGraph.tsx con modo bajo demanda (On-Demand Rendering)
y optimización para evitar lag con 10,000+ líneas.
"""

from pathlib import Path

CODE = """import React, { useEffect, useRef, useState, useCallback } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw,
  Eye,
  EyeOff,
  Sparkles,
  Zap,
  Activity
} from 'lucide-react';

interface Node {
  id: string;
  label: string;
  type: string;
  file?: string;
  keywords?: string[];
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
  clusterId?: string;
}

interface Edge {
  source: string;
  target: string;
  weight: number;
  relation: string;
}

interface SynapticGraphProps {
  nodesData: Record<string, any>;
  edgesData: Array<{ source: string; target: string; weight: number; relation: string }>;
  activations?: Record<string, number>;
  selectedNodeId?: string | null;
  onSelectNode: (nodeId: string | null) => void;
  searchQuery?: string;
}

const TYPE_COLORS: Record<string, string> = {
  cluster: '#c084fc',     // Glowing Violet
  skill: '#34d399',       // Emerald Neon
  pattern: '#38bdf8',     // Sky Blue
  concept: '#fbbf24',     // Amber
  antipattern: '#fb7185', // Rose/Red
};

const CLUSTER_CENTERS: Record<string, { cx: number; cy: number }> = {
  cluster_web_ecosystem: { cx: -320, cy: -200 },
  cluster_backend_fastapi: { cx: 0, cy: -240 },
  cluster_agentic_ai: { cx: 320, cy: -200 },
  cluster_n8n_automation: { cx: -300, cy: 220 },
  cluster_cybersecurity: { cx: 300, cy: 220 },
  cluster_devops_cloud: { cx: 0, cy: 260 },
};

export const SynapticGraph: React.FC<SynapticGraphProps> = ({
  nodesData,
  edgesData,
  activations = {},
  selectedNodeId = null,
  onSelectNode,
  searchQuery = ''
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  
  // High-performance mutable references
  const nodesRef = useRef<Node[]>([]);
  const edgesRef = useRef<Edge[]>([]);
  const isSimulatingRef = useRef<boolean>(false);
  const zoomRef = useRef<number>(0.85);
  const panRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const hoveredNodeRef = useRef<Node | null>(null);
  const selectedNodeIdRef = useRef<string | null>(selectedNodeId);
  const activationsRef = useRef<Record<string, number>>(activations);
  const searchQueryRef = useRef<string>(searchQuery);
  const activeFilterRef = useRef<string>('all');
  const draggedNodeIdRef = useRef<string | null>(null);
  const isDraggingRef = useRef<boolean>(false);
  const dragStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // On-demand rendering control (default: false to prevent initial GPU lag)
  const [showGraph, setShowGraph] = useState<boolean>(false);
  const showGraphRef = useRef<boolean>(false);

  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [, setRerenderTrigger] = useState<number>(0);

  useEffect(() => {
    showGraphRef.current = showGraph;
    if (showGraph) {
      isSimulatingRef.current = true;
    }
  }, [showGraph]);

  // Sync prop changes to refs
  useEffect(() => {
    selectedNodeIdRef.current = selectedNodeId;
  }, [selectedNodeId]);

  useEffect(() => {
    activationsRef.current = activations;
    // Si hay activaciones activas, permitir visualizarlas
    if (Object.keys(activations).length > 0) {
      isSimulatingRef.current = true;
    }
  }, [activations]);

  useEffect(() => {
    searchQueryRef.current = searchQuery;
  }, [searchQuery]);

  useEffect(() => {
    activeFilterRef.current = activeFilter;
  }, [activeFilter]);

  // 1. Initialize Layout
  useEffect(() => {
    const rawKeys = Object.keys(nodesData);
    if (rawKeys.length === 0) return;

    const nodeClusterMap: Record<string, string> = {};
    edgesData.forEach(e => {
      if (CLUSTER_CENTERS[e.source]) nodeClusterMap[e.target] = e.source;
      if (CLUSTER_CENTERS[e.target]) nodeClusterMap[e.source] = e.target;
    });

    const initialNodes: Node[] = rawKeys.map((id, index) => {
      const data = nodesData[id];
      const type = data.type || 'skill';
      const isCluster = type === 'cluster';
      const isAntipattern = type === 'antipattern';

      let center = { cx: 0, cy: 0 };
      const parentCluster = nodeClusterMap[id];
      if (CLUSTER_CENTERS[id]) {
        center = CLUSTER_CENTERS[id];
      } else if (parentCluster && CLUSTER_CENTERS[parentCluster]) {
        center = CLUSTER_CENTERS[parentCluster];
      } else if (isAntipattern) {
        center = { cx: 0, cy: 240 };
      }

      const angle = (index * 137.5 * Math.PI) / 180;
      const dist = isCluster ? 0 : 35 + (index % 12) * 18;
      const x = center.cx + Math.cos(angle) * dist;
      const y = center.cy + Math.sin(angle) * dist;

      return {
        id,
        label: data.title || data.label || id,
        type,
        file: data.file,
        keywords: data.keywords || [],
        x,
        y,
        vx: 0,
        vy: 0,
        radius: isCluster ? 14 : isAntipattern ? 7 : 5,
        color: TYPE_COLORS[type] || '#94a3b8',
        clusterId: parentCluster || (isCluster ? id : undefined)
      };
    });

    nodesRef.current = initialNodes;
    edgesRef.current = edgesData;
  }, [nodesData, edgesData]);

  // 2. High-Performance Canvas Rendering Loop
  useEffect(() => {
    let animId: number;
    let ticks = 0;

    const render = () => {
      const canvas = canvasRef.current;
      if (!canvas) {
        animId = requestAnimationFrame(render);
        return;
      }
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        animId = requestAnimationFrame(render);
        return;
      }

      const parent = containerRef.current;
      const width = parent?.clientWidth || 800;
      const height = parent?.clientHeight || 600;

      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      // Background clear
      ctx.fillStyle = '#06080e';
      ctx.fillRect(0, 0, width, height);

      // Si el grafo está apagado, renderizar estado idle suave
      if (!showGraphRef.current) {
        animId = requestAnimationFrame(render);
        return;
      }

      ctx.save();
      ctx.translate(width / 2 + panRef.current.x, height / 2 + panRef.current.y);
      ctx.scale(zoomRef.current, zoomRef.current);

      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      const selectedId = selectedNodeIdRef.current;
      const hovered = hoveredNodeRef.current;
      const activeActs = activationsRef.current;
      const query = searchQueryRef.current.toLowerCase().trim();
      const currentFilter = activeFilterRef.current;

      // Soft physics tick with auto-stabilization
      if (isSimulatingRef.current) {
        ticks++;
        if (ticks > 250) {
          isSimulatingRef.current = false; // Auto-sleep to save 100% CPU
        }
        for (let i = 0; i < nodes.length; i++) {
          const n = nodes[i];
          if (n.id === draggedNodeIdRef.current) continue;
          n.x += n.vx;
          n.y += n.vy;
          n.vx *= 0.82;
          n.vy *= 0.82;
        }
      }

      // Precompute node map for fast O(1) edge lookups
      const nodeMap: Record<string, Node> = {};
      for (let i = 0; i < nodes.length; i++) {
        nodeMap[nodes[i].id] = nodes[i];
      }

      // Optimized Edge Rendering: Render high-weight synapses and connected edges
      const isSelective = edges.length > 1500;
      for (let i = 0; i < edges.length; i++) {
        const e = edges[i];
        const source = nodeMap[e.source];
        const target = nodeMap[e.target];
        if (!source || !target) continue;

        const isConnectedToActive = 
          (hovered && (e.source === hovered.id || e.target === hovered.id)) ||
          (selectedId && (e.source === selectedId || e.target === selectedId)) ||
          (activeActs[e.source] && activeActs[e.target]);

        // If over 1,500 edges, only draw relevant or high-weight lines to keep 60 FPS
        if (isSelective && !isConnectedToActive && e.weight < 0.88) {
          continue;
        }

        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);

        if (isConnectedToActive) {
          ctx.strokeStyle = 'rgba(0, 242, 254, 0.7)';
          ctx.lineWidth = 1.5;
        } else {
          ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
          ctx.lineWidth = 0.5;
        }
        ctx.stroke();
      }

      // Node Rendering
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];
        const isSelected = selectedId === node.id;
        const isHovered = hovered?.id === node.id;
        const actEnergy = activeActs[node.id] || 0;
        const isMatch = query && (
          node.id.toLowerCase().includes(query) || 
          node.label.toLowerCase().includes(query)
        );
        const isFilteredOut = currentFilter !== 'all' && node.type !== currentFilter;

        if (isFilteredOut && !isSelected && !isHovered && actEnergy === 0) {
          continue;
        }

        ctx.save();
        ctx.beginPath();
        const baseRadius = node.radius + (actEnergy > 0 ? 3 : 0) + (isSelected ? 3 : 0);
        ctx.arc(node.x, node.y, baseRadius, 0, Math.PI * 2);

        if (isSelected) {
          ctx.fillStyle = '#00f2fe';
          ctx.shadowColor = '#00f2fe';
          ctx.shadowBlur = 15;
        } else if (actEnergy > 0) {
          ctx.fillStyle = '#f59e0b';
          ctx.shadowColor = '#f59e0b';
          ctx.shadowBlur = 12;
        } else if (isHovered) {
          ctx.fillStyle = '#ffffff';
          ctx.shadowColor = '#ffffff';
          ctx.shadowBlur = 10;
        } else {
          ctx.fillStyle = node.color;
          ctx.shadowBlur = 0;
        }
        ctx.fill();

        // Draw Label when hovered, selected, or cluster
        const shouldShowLabel = 
          node.type === 'cluster' || 
          isSelected || 
          isHovered || 
          actEnergy > 0 || 
          isMatch;

        if (shouldShowLabel) {
          const fontSize = node.type === 'cluster' ? 12 : 10;
          ctx.font = `${node.type === 'cluster' ? 'bold ' : '500 '}${fontSize}px Inter, sans-serif`;
          const text = node.label;
          const textWidth = ctx.measureText(text).width;
          const padX = 6;
          const padY = 3;
          const labelY = node.y + node.radius + 12;

          ctx.fillStyle = 'rgba(10, 15, 29, 0.9)';
          ctx.strokeStyle = isSelected ? '#00f2fe' : 'rgba(255, 255, 255, 0.12)';
          ctx.lineWidth = 1;
          
          ctx.beginPath();
          ctx.roundRect(node.x - textWidth / 2 - padX, labelY - fontSize - padY + 2, textWidth + padX * 2, fontSize + padY * 2, 4);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = isSelected ? '#00f2fe' : '#f8fafc';
          ctx.textAlign = 'center';
          ctx.fillText(text, node.x, labelY);
        }

        ctx.restore();
      }

      ctx.restore();
      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, []);

  // Fast Pointer Events
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!showGraph) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const parent = containerRef.current;
    const width = parent?.clientWidth || 800;
    const height = parent?.clientHeight || 600;
    const zoom = zoomRef.current;
    const pan = panRef.current;

    const worldX = (mouseX - width / 2 - pan.x) / zoom;
    const worldY = (mouseY - height / 2 - pan.y) / zoom;

    const nodes = nodesRef.current;
    let clickedNode: Node | null = null;
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      const dx = n.x - worldX;
      const dy = n.y - worldY;
      if (dx * dx + dy * dy <= (n.radius + 8) * (n.radius + 8)) {
        clickedNode = n;
        break;
      }
    }

    if (clickedNode) {
      draggedNodeIdRef.current = clickedNode.id;
      onSelectNode(clickedNode.id);
      isSimulatingRef.current = true;
    } else {
      isDraggingRef.current = true;
      dragStartRef.current = { x: mouseX - pan.x, y: mouseY - pan.y };
    }
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!showGraphRef.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const parent = containerRef.current;
    const width = parent?.clientWidth || 800;
    const height = parent?.clientHeight || 600;
    const zoom = zoomRef.current;
    const pan = panRef.current;

    if (draggedNodeIdRef.current) {
      const worldX = (mouseX - width / 2 - pan.x) / zoom;
      const worldY = (mouseY - height / 2 - pan.y) / zoom;
      const nodes = nodesRef.current;
      for (let i = 0; i < nodes.length; i++) {
        if (nodes[i].id === draggedNodeIdRef.current) {
          nodes[i].x = worldX;
          nodes[i].y = worldY;
          nodes[i].vx = 0;
          nodes[i].vy = 0;
          break;
        }
      }
    } else if (isDraggingRef.current) {
      const nextX = mouseX - dragStartRef.current.x;
      const nextY = mouseY - dragStartRef.current.y;
      panRef.current = {
        x: Math.max(-600, Math.min(600, nextX)),
        y: Math.max(-600, Math.min(600, nextY))
      };
    } else {
      const worldX = (mouseX - width / 2 - pan.x) / zoom;
      const worldY = (mouseY - height / 2 - pan.y) / zoom;
      const nodes = nodesRef.current;
      let found: Node | null = null;
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        const dx = n.x - worldX;
        const dy = n.y - worldY;
        if (dx * dx + dy * dy <= (n.radius + 6) * (n.radius + 6)) {
          found = n;
          break;
        }
      }
      hoveredNodeRef.current = found;
    }
  }, []);

  const handleMouseUp = useCallback(() => {
    isDraggingRef.current = false;
    draggedNodeIdRef.current = null;
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    if (!showGraph) return;
    e.preventDefault();
    const zoomFactor = 1.08;
    if (e.deltaY < 0) {
      zoomRef.current = Math.min(2.5, zoomRef.current * zoomFactor);
    } else {
      zoomRef.current = Math.max(0.4, zoomRef.current / zoomFactor);
    }
  };

  const handleResetView = () => {
    zoomRef.current = 0.85;
    panRef.current = { x: 0, y: 0 };
    isSimulatingRef.current = true;
    setRerenderTrigger(t => t + 1);
  };

  const handleFilterClick = (type: string) => {
    setActiveFilter(type);
    activeFilterRef.current = type;
  };

  const totalNodesCount = Object.keys(nodesData).length;
  const totalEdgesCount = edgesData.length;

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-full overflow-hidden bg-slate-950 select-none"
      style={{ position: 'relative', width: '100%', height: '100%' }}
      onDoubleClick={handleResetView}
    >
      {/* Top Left: Graph Toggle & Filter Controls */}
      <div style={{ position: 'absolute', top: '14px', left: '14px', zIndex: 10, display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        {/* Toggle On-Demand Button */}
        <button
          onClick={() => setShowGraph(prev => !prev)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '8px',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            border: showGraph ? '1px solid rgba(244, 63, 94, 0.4)' : '1px solid rgba(0, 242, 254, 0.4)',
            background: showGraph ? 'rgba(244, 63, 94, 0.15)' : 'linear-gradient(135deg, rgba(0, 242, 254, 0.25), rgba(99, 102, 241, 0.25))',
            color: showGraph ? '#fb7185' : '#00f2fe',
            backdropFilter: 'blur(12px)',
            boxShadow: showGraph ? 'none' : '0 0 15px rgba(0, 242, 254, 0.2)'
          }}
        >
          {showGraph ? <EyeOff size={14} /> : <Eye size={14} />}
          {showGraph ? 'Ocultar Grafo' : 'Visualizar Grafo'}
        </button>

        {showGraph && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(10, 15, 29, 0.85)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border-subtle)', backdropFilter: 'blur(12px)' }}>
            {['all', 'cluster', 'skill', 'pattern', 'concept', 'antipattern'].map(t => (
              <button
                key={t}
                onClick={() => handleFilterClick(t)}
                style={{
                  padding: '3px 8px',
                  borderRadius: '5px',
                  fontSize: '11px',
                  fontWeight: 600,
                  border: 'none',
                  background: activeFilter === t ? 'rgba(0, 242, 254, 0.2)' : 'transparent',
                  color: activeFilter === t ? '#00f2fe' : '#94a3b8',
                  cursor: 'pointer',
                  textTransform: 'capitalize'
                }}
              >
                {t === 'all' ? '🌐 All' : t}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Floating Canvas Controls (Only when visible) */}
      {showGraph && (
        <div style={{ position: 'absolute', bottom: '16px', right: '16px', zIndex: 10, display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(10, 15, 29, 0.9)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <button
            onClick={() => { zoomRef.current = Math.min(2.5, zoomRef.current * 1.2); }}
            style={{ padding: '6px', background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
            title="Zoom In"
          >
            <ZoomIn size={14} />
          </button>
          <button
            onClick={() => { zoomRef.current = Math.max(0.4, zoomRef.current / 1.2); }}
            style={{ padding: '6px', background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
            title="Zoom Out"
          >
            <ZoomOut size={14} />
          </button>
          <button
            onClick={handleResetView}
            style={{ padding: '6px 10px', background: 'rgba(0, 242, 254, 0.1)', border: '1px solid rgba(0, 242, 254, 0.3)', borderRadius: '6px', color: '#00f2fe', fontSize: '11px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
            title="Center Graph"
          >
            <RotateCcw size={12} />
            Center
          </button>
        </div>
      )}

      {/* Empty / Idle State Overlay (When showGraph is false) */}
      {!showGraph && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 5,
          background: 'radial-gradient(circle at center, rgba(15, 23, 42, 0.6) 0%, rgba(6, 8, 14, 0.95) 75%)',
          pointerEvents: 'auto',
          padding: '20px'
        }}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.75)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '20px',
            padding: '2.5rem 2rem',
            maxWidth: '520px',
            textAlign: 'center',
            backdropFilter: 'blur(16px)',
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5)'
          }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, rgba(0, 242, 254, 0.2), rgba(99, 102, 241, 0.2))',
              border: '1px solid rgba(0, 242, 254, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem',
              color: '#00f2fe'
            }}>
              <Zap size={28} />
            </div>
            
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
              Modo de Rendimiento Activo
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5, marginBottom: '1.5rem' }}>
              Tu base cuenta con <strong>{totalNodesCount.toLocaleString()} nodos</strong> y <strong>{totalEdgesCount.toLocaleString()} sinapsis</strong>. Para garantizar una experiencia fluida sin saturar la GPU, el renderizado completo de líneas está pausado por defecto.
            </p>

            <button
              onClick={() => setShowGraph(true)}
              style={{
                background: 'linear-gradient(135deg, #00f2fe 0%, #6366f1 100%)',
                color: '#030712',
                border: 'none',
                padding: '0.75rem 1.75rem',
                borderRadius: '12px',
                fontSize: '0.9rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 0 25px rgba(0, 242, 254, 0.3)',
                transition: 'transform 0.15s ease'
              }}
            >
              <Sparkles size={16} />
              Cargar y Renderizar Grafo ({totalNodesCount} Nodos)
            </button>
          </div>
        </div>
      )}

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onWheel={handleWheel}
        style={{ width: '100%', height: '100%', display: 'block', cursor: showGraph ? 'grab' : 'default' }}
      />
    </div>
  );
};
"""

MEJORA_HERMES_DIR = Path(__file__).resolve().parent.parent
target = MEJORA_HERMES_DIR / "knowledge" / "dashboard" / "src" / "components" / "SynapticGraph.tsx"
if not target.parent.exists():
    target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(CODE, encoding="utf-8")
print(f"✅ SynapticGraph.tsx successfully updated with On-Demand graph rendering at {target}")
