import React, { useMemo, useState } from 'react';
import type { GraphData, GraphNode } from '../../types/code_analysis';

interface DependencyGraphProps {
  data: GraphData;
}

const TYPE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  FILE: { bg: 'bg-cyan-950/60', border: 'border-cyan-500/50', text: 'text-cyan-400' },
  MODULE: { bg: 'bg-blue-950/60', border: 'border-blue-500/50', text: 'text-blue-400' },
  CLASS: { bg: 'bg-purple-950/60', border: 'border-purple-500/50', text: 'text-purple-400' },
  FUNCTION: { bg: 'bg-emerald-950/60', border: 'border-emerald-500/50', text: 'text-emerald-400' },
  METHOD: { bg: 'bg-amber-950/60', border: 'border-amber-500/50', text: 'text-amber-400' },
};

const EDGE_COLORS: Record<string, string> = {
  CONTAINS: '#64748b', // slate
  IMPORTS: '#6366f1',  // indigo
  CALLS: '#14b8a6',    // teal
  DEFINES: '#ec4899',  // pink
};

export const DependencyGraph: React.FC<DependencyGraphProps> = ({ data }) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterRel, setFilterRel] = useState<string>('ALL');

  // Filtered nodes
  const filteredNodes = useMemo(() => {
    return data.nodes.filter((node) => {
      const matchesSearch =
        node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (node.file_path && node.file_path.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesType = filterType === 'ALL' || node.type === filterType;
      return matchesSearch && matchesType;
    });
  }, [data.nodes, searchTerm, filterType]);

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((n) => n.id)), [filteredNodes]);

  // Filtered edges
  const filteredEdges = useMemo(() => {
    return data.edges.filter((edge) => {
      const matchesRel = filterRel === 'ALL' || edge.relationship_type === filterRel;
      return matchesRel && filteredNodeIds.has(edge.source);
    });
  }, [data.edges, filterRel, filteredNodeIds]);

  // Compute grid/hierarchical node positions for SVG rendering
  const nodePositions = useMemo(() => {
    const posMap = new Map<string, { x: number; y: number }>();
    const fileNodes = filteredNodes.filter((n) => n.type === 'FILE');
    const symbolNodes = filteredNodes.filter((n) => n.type !== 'FILE');

    const totalWidth = 900;
    const padding = 100;

    // Arrange file nodes in top row
    fileNodes.forEach((node, idx) => {
      const spacing = totalWidth / Math.max(1, fileNodes.length);
      const x = padding + idx * spacing + spacing / 2;
      const y = 80;
      posMap.set(node.id, { x, y });
    });

    // Arrange symbol nodes in subsequent grid rows
    const cols = 4;
    symbolNodes.forEach((node, idx) => {
      const row = Math.floor(idx / cols);
      const col = idx % cols;
      const x = 120 + col * 210;
      const y = 220 + row * 120;
      posMap.set(node.id, { x, y });
    });

    return posMap;
  }, [filteredNodes]);

  // Inbound & Outbound edges for selected node inspector
  const selectedNodeInspector = useMemo(() => {
    if (!selectedNode) return null;
    const outbound = data.edges.filter((e) => e.source === selectedNode.id);
    const inbound = data.edges.filter((e) => e.target === selectedNode.id);
    return { outbound, inbound };
  }, [selectedNode, data.edges]);

  return (
    <div className="flex flex-col gap-6">
      {/* Controls & Filters Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            placeholder="Filter nodes by name or path..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-64 rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
          />

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-slate-200 focus:border-cyan-500 focus:outline-none"
          >
            <option value="ALL">All Entity Types</option>
            <option value="FILE">FILE</option>
            <option value="CLASS">CLASS</option>
            <option value="FUNCTION">FUNCTION</option>
            <option value="METHOD">METHOD</option>
          </select>

          <select
            value={filterRel}
            onChange={(e) => setFilterRel(e.target.value)}
            className="rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-slate-200 focus:border-cyan-500 focus:outline-none"
          >
            <option value="ALL">All Relationships</option>
            <option value="IMPORTS">IMPORTS</option>
            <option value="CALLS">CALLS</option>
            <option value="CONTAINS">CONTAINS</option>
          </select>
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-cyan-400"></span> FILE
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-purple-400"></span> CLASS
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400"></span> FUNCTION
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400"></span> METHOD
          </span>
        </div>
      </div>

      {/* Main Canvas + Inspector Grid */}
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {/* SVG Interactive Canvas */}
        <div className="relative min-h-[500px] overflow-auto rounded-3xl border border-slate-800 bg-slate-950/80 p-4">
          {filteredNodes.length === 0 ? (
            <div className="flex h-64 items-center justify-center text-slate-500">
              No matching code entities found in graph.
            </div>
          ) : (
            <svg className="h-[600px] w-full min-w-[850px]">
              <defs>
                <marker
                  id="arrow"
                  viewBox="0 0 10 10"
                  refX="16"
                  refY="5"
                  markerWidth="6"
                  markerHeight="6"
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
                </marker>
              </defs>

              {/* Draw Edges */}
              {filteredEdges.map((edge) => {
                const srcPos = nodePositions.get(edge.source);
                const tgtPos = nodePositions.get(edge.target);
                if (!srcPos || !tgtPos) return null;

                const color = EDGE_COLORS[edge.relationship_type] || '#64748b';
                const isDashed = edge.relationship_type === 'CONTAINS';

                return (
                  <g key={edge.id}>
                    <line
                      x1={srcPos.x}
                      y1={srcPos.y}
                      x2={tgtPos.x}
                      y2={tgtPos.y}
                      stroke={color}
                      strokeWidth={edge.relationship_type === 'IMPORTS' ? '2' : '1.5'}
                      strokeDasharray={isDashed ? '4,4' : undefined}
                      opacity={0.65}
                      markerEnd="url(#arrow)"
                    />
                    <text
                      x={(srcPos.x + tgtPos.x) / 2}
                      y={(srcPos.y + tgtPos.y) / 2 - 6}
                      fill={color}
                      fontSize="9"
                      textAnchor="middle"
                      className="font-mono opacity-80 select-none"
                    >
                      {edge.relationship_type}
                    </text>
                  </g>
                );
              })}

              {/* Draw Nodes */}
              {filteredNodes.map((node) => {
                const pos = nodePositions.get(node.id) || { x: 100, y: 100 };
                const isSelected = selectedNode?.id === node.id;
                const colors = TYPE_COLORS[node.type] || TYPE_COLORS.FILE;

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x - 75}, ${pos.y - 25})`}
                    onClick={() => setSelectedNode(node)}
                    className="cursor-pointer transition-all hover:scale-105"
                  >
                    <rect
                      width="150"
                      height="50"
                      rx="12"
                      className={`fill-slate-900 stroke-2 ${
                        isSelected ? 'stroke-cyan-400 fill-slate-800 shadow-lg' : colors.border
                      }`}
                    />
                    <text
                      x="75"
                      y="22"
                      fill="#f8fafc"
                      fontSize="12"
                      fontWeight="600"
                      textAnchor="middle"
                      className="pointer-events-none select-none"
                    >
                      {node.name.length > 18 ? `${node.name.substring(0, 16)}…` : node.name}
                    </text>
                    <text
                      x="75"
                      y="38"
                      className={`${colors.text} pointer-events-none select-none font-mono text-[10px] font-semibold`}
                      textAnchor="middle"
                    >
                      {node.type}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </div>

        {/* Selected Node Details Side Inspector */}
        <div className="flex flex-col gap-4 rounded-3xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
          <h3 className="text-lg font-semibold text-slate-100">Entity Inspector</h3>

          {selectedNode ? (
            <div className="space-y-4 text-sm text-slate-300">
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4 space-y-2">
                <div>
                  <p className="text-xs uppercase tracking-wider text-slate-500">Name</p>
                  <p className="font-mono text-base font-semibold text-cyan-400">{selectedNode.name}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-slate-500">Entity Type</p>
                  <span className="inline-block rounded-md bg-slate-800 px-2 py-0.5 text-xs font-mono text-slate-200">
                    {selectedNode.type}
                  </span>
                </div>
                {selectedNode.file_path && (
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500">File Path</p>
                    <p className="font-mono text-xs text-slate-300 break-all">{selectedNode.file_path}</p>
                  </div>
                )}
                {selectedNode.start_line && (
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500">Location</p>
                    <p className="font-mono text-xs text-slate-400">
                      Lines {selectedNode.start_line} – {selectedNode.end_line}
                    </p>
                  </div>
                )}
              </div>

              {selectedNodeInspector && (
                <div className="space-y-3">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-400 mb-1.5 font-semibold">
                      Outbound Dependencies ({selectedNodeInspector.outbound.length})
                    </p>
                    {selectedNodeInspector.outbound.length === 0 ? (
                      <p className="text-xs text-slate-500 italic">None</p>
                    ) : (
                      <ul className="space-y-1 text-xs">
                        {selectedNodeInspector.outbound.map((e) => (
                          <li key={e.id} className="rounded-lg bg-slate-950 p-2 border border-slate-800">
                            <span className="text-cyan-400 font-semibold">{e.relationship_type}</span>{' '}
                            <span className="text-slate-300 font-mono">{e.raw_target || e.target}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-400 mb-1.5 font-semibold">
                      Inbound References ({selectedNodeInspector.inbound.length})
                    </p>
                    {selectedNodeInspector.inbound.length === 0 ? (
                      <p className="text-xs text-slate-500 italic">None</p>
                    ) : (
                      <ul className="space-y-1 text-xs">
                        {selectedNodeInspector.inbound.map((e) => (
                          <li key={e.id} className="rounded-lg bg-slate-950 p-2 border border-slate-800">
                            <span className="text-indigo-400 font-semibold">{e.relationship_type}</span> from{' '}
                            <span className="text-slate-300 font-mono">{e.source}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-400">
              Click any node in the dependency graph to inspect its code entity properties and relationship details.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
