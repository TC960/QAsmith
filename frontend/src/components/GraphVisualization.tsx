import React, { useEffect, useRef, useState } from 'react';
import { Network, DataSet } from 'vis-network/standalone';
import './GraphVisualization.css';

interface Node {
  url: string;
  title: string;
  depth: number;
  page_id?: string;
}

interface Edge {
  from_url: string;
  to_url: string;
  label?: string;
}

interface GraphData {
  nodes: Node[];
  edges: Edge[];
}

interface GraphVisualizationProps {
  graphData: GraphData;
  onNodeClick?: (node: Node) => void;
}

const GraphVisualization: React.FC<GraphVisualizationProps> = ({ graphData, onNodeClick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [stats, setStats] = useState({ nodes: 0, edges: 0, maxDepth: 0 });

  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    console.log('🎨 GRAPH: Rendering visualization with', graphData.nodes.length, 'nodes');

    // Create a URL to ID mapping
    const urlToId = new Map<string, number>();
    graphData.nodes.forEach((node, idx) => {
      urlToId.set(node.url, idx);
    });

    console.log('🗺️ GRAPH: URL to ID mapping:', Array.from(urlToId.entries()).slice(0, 5));
    console.log('🔗 GRAPH: Sample edge URLs:', graphData.edges.slice(0, 3).map(e => ({ from: e.from_url, to: e.to_url })));

    // Calculate stats
    const maxDepth = Math.max(...graphData.nodes.map(n => n.depth));
    setStats({
      nodes: graphData.nodes.length,
      edges: graphData.edges.length,
      maxDepth: maxDepth
    });

    // Prepare nodes for vis-network
    const visNodes = graphData.nodes.map((node, idx) => {
      // IMPROVED: Magenta for home, blue for depth 1, green for depth 2
      const colors = [
        '#e91e63', // depth 0 - magenta (homepage)
        '#3b82f6', // depth 1 - blue
        '#10b981', // depth 2 - green
        '#f59e0b', // depth 3 - amber
        '#8b5cf6', // depth 4 - purple
        '#06b6d4', // depth 5 - cyan
        '#ef4444', // depth 6+ - red
      ];

      const color = colors[Math.min(node.depth, colors.length - 1)];

      // IMPROVED: Larger nodes for better visibility
      const size = Math.max(25, 50 - (node.depth * 4));

      // IMPROVED: Shorter, cleaner labels
      const urlPath = new URL(node.url).pathname;
      const shortLabel = node.title?.substring(0, 30) || urlPath.split('/').filter(Boolean).pop() || 'Home';

      return {
        id: idx,
        label: shortLabel,
        title: `${node.title}\n${node.url}\nDepth: ${node.depth}`,
        level: node.depth, // IMPROVED: Use depth as hierarchical level
        color: {
          background: color,
          border: '#ffffff', // White border for better contrast
          highlight: {
            background: '#ffd700',
            border: '#ff6b00'
          }
        },
        font: {
          color: '#1a202c', // IMPROVED: Dark text (better contrast)
          size: 14, // IMPROVED: Larger font
          face: 'Inter, system-ui, -apple-system, sans-serif',
          bold: true, // IMPROVED: Bold text
          strokeWidth: 3, // IMPROVED: Text outline for readability
          strokeColor: '#ffffff' // White outline
        },
        size: size,
        shape: node.depth === 0 ? 'star' : 'dot',
        borderWidth: 3, // IMPROVED: Thicker borders
        shadow: {
          enabled: true,
          color: 'rgba(0, 0, 0, 0.3)',
          size: 10,
          x: 0,
          y: 2
        }
      };
    });

    // Prepare edges for vis-network
    const visEdges = graphData.edges.map((edge, idx) => {
      const fromId = urlToId.get(edge.from_url);
      const toId = urlToId.get(edge.to_url);

      if (fromId === undefined || toId === undefined) {
        console.warn('🚨 GRAPH: Edge references unknown node:', {
          edge,
          fromId,
          toId,
          fromExists: urlToId.has(edge.from_url),
          toExists: urlToId.has(edge.to_url)
        });
        return null;
      }

      if (idx < 3) {
        console.log('✅ GRAPH: Creating edge', fromId, '->', toId, edge.from_url, '->', edge.to_url);
      }

      return {
        from: fromId,
        to: toId,
        arrows: 'to',
        color: '#000000', // STARK BLACK for maximum visibility
        width: 6, // Even thicker
        shadow: true,
        smooth: false, // Straight lines - easier to see
        physics: true,
        hidden: false, // Explicitly not hidden
        selectionWidth: 2
      };
    }).filter(edge => edge !== null);

    console.log('🎨 GRAPH: Created', visEdges.length, 'edges');
    console.log('🔍 GRAPH: Sample edges:', visEdges.slice(0, 3));

    // Create network using DataSet for better control
    const nodes = new DataSet(visNodes);
    const edges = new DataSet(visEdges);

    const data = {
      nodes: nodes,
      edges: edges
    };

    const options = {
      nodes: {
        font: {
          color: '#ffffff',
          size: 12
        }
      },
      edges: {
        // CRITICAL: Set default edge appearance
        color: {
          color: '#000000',
          highlight: '#ef4444',
          hover: '#f59e0b',
          inherit: false,
          opacity: 1.0
        },
        width: 6,
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 1.5
          }
        },
        smooth: {
          enabled: false // Straight lines
        },
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.5)',
          size: 10,
          x: 2,
          y: 2
        },
        hidden: false,
        physics: true,
        selectionWidth: 3,
        hoverWidth: 0.5
      },
      physics: {
        enabled: true,
        stabilization: {
          enabled: true,
          iterations: 400,
          updateInterval: 25,
          fit: true
        },
        // IMPROVED: Use force-directed layout (like Neo4j) instead of hierarchical
        barnesHut: {
          gravitationalConstant: -3000, // Stronger repulsion for better spacing
          centralGravity: 0.15, // Pull towards center
          springLength: 180, // Edge length
          springConstant: 0.04,
          damping: 0.09,
          avoidOverlap: 0.2 // Prevent node overlap
        },
        solver: 'barnesHut',
        adaptiveTimestep: true
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true,
        hoverConnectedEdges: true, // Highlight edges on hover
        selectConnectedEdges: true,
        dragNodes: true, // Allow dragging nodes
        navigationButtons: true, // Show zoom controls
        keyboard: {
          enabled: true
        }
      },
      layout: {
        improvedLayout: true,
        randomSeed: 42, // Consistent layout on reload
        hierarchical: {
          enabled: false // IMPROVED: Disable hierarchical, use organic force-directed
        }
      }
    };

    // Destroy existing network
    if (networkRef.current) {
      networkRef.current.destroy();
    }

    // Create new network
    const network = new Network(containerRef.current, data, options);
    networkRef.current = network;

    // DEBUGGING: Force redraw and check edges
    network.on('afterDrawing', (ctx) => {
      console.log('🎨 GRAPH: Canvas drawn');
    });

    network.on('stabilizationIterationsDone', () => {
      console.log('✅ GRAPH: Physics stabilized');
      network.fit();
    });

    // Log edge dataset
    console.log('📊 GRAPH: Edge dataset:', network.body.data.edges.get());

    // Add click handler
    network.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = graphData.nodes[nodeId];
        console.log('🖱️ GRAPH: Node clicked:', node);
        setSelectedNode(node);
        if (onNodeClick) {
          onNodeClick(node);
        }
      } else {
        setSelectedNode(null);
      }
    });

    // Stabilization progress
    network.on('stabilizationProgress', (params) => {
      const progress = Math.round((params.iterations / params.total) * 100);
      console.log(`⚙️ GRAPH: Stabilizing... ${progress}%`);
    });

    network.on('stabilizationIterationsDone', () => {
      console.log('✅ GRAPH: Layout stabilized');
      network.setOptions({ physics: { enabled: false } });
    });

    // Cleanup
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [graphData, onNodeClick]);

  // Toggle hierarchical view
  const toggleHierarchical = () => {
    if (!networkRef.current) return;
    
    const currentOptions = networkRef.current.options as any;
    const isHierarchical = currentOptions?.layout?.hierarchical?.enabled || false;
    
    networkRef.current.setOptions({
      layout: {
        hierarchical: {
          enabled: !isHierarchical,
          direction: 'UD',
          sortMethod: 'directed',
          levelSeparation: 150,
          nodeSpacing: 100
        }
      },
      physics: {
        enabled: true,
        hierarchicalRepulsion: {
          nodeDistance: 120
        }
      }
    });

    // Disable physics after stabilization
    setTimeout(() => {
      if (networkRef.current) {
        networkRef.current.setOptions({ physics: { enabled: false } });
      }
    }, 2000);
  };

  const fitGraph = () => {
    if (networkRef.current) {
      networkRef.current.fit({ animation: { duration: 1000 } });
    }
  };

  return (
    <div className="graph-visualization">
      <div className="graph-header">
        <div className="graph-stats">
          <span className="stat">
            <strong>{stats.nodes}</strong> Pages
          </span>
          <span className="stat">
            <strong>{stats.edges}</strong> Links
          </span>
          <span className="stat">
            Max Depth: <strong>{stats.maxDepth}</strong>
          </span>
        </div>
        <div className="graph-controls">
          <button onClick={toggleHierarchical} className="control-btn">
            🔄 Toggle Layout
          </button>
          <button onClick={fitGraph} className="control-btn">
            🎯 Fit View
          </button>
        </div>
      </div>

      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#667eea' }}></span>
          <span>Depth 0 (Home)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#48bb78' }}></span>
          <span>Depth 1</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#ed8936' }}></span>
          <span>Depth 2</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#f56565' }}></span>
          <span>Depth 3+</span>
        </div>
      </div>

      <div ref={containerRef} className="graph-container" />

      {selectedNode && (
        <div className="node-details">
          <h4>Selected Page</h4>
          <p><strong>Title:</strong> {selectedNode.title}</p>
          <p><strong>URL:</strong> {selectedNode.url}</p>
          <p><strong>Depth:</strong> {selectedNode.depth}</p>
        </div>
      )}
    </div>
  );
};

export default GraphVisualization;

