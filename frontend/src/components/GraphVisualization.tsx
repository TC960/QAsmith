import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'vis-network/standalone';
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

    // Calculate stats
    const maxDepth = Math.max(...graphData.nodes.map(n => n.depth));
    setStats({
      nodes: graphData.nodes.length,
      edges: graphData.edges.length,
      maxDepth: maxDepth
    });

    // Prepare nodes for vis-network
    const visNodes = graphData.nodes.map((node, idx) => {
      // Color by depth
      const colors = [
        '#667eea', // depth 0 - purple
        '#48bb78', // depth 1 - green
        '#ed8936', // depth 2 - orange
        '#f56565', // depth 3 - red
        '#9f7aea', // depth 4 - purple
        '#38b2ac', // depth 5 - teal
        '#4299e1', // depth 6+ - blue
      ];
      
      const color = colors[Math.min(node.depth, colors.length - 1)];
      
      // Size by depth (deeper = smaller)
      const size = Math.max(15, 35 - (node.depth * 3));
      
      return {
        id: idx,
        label: node.title || new URL(node.url).pathname || '/',
        title: `${node.title}\n${node.url}\nDepth: ${node.depth}`,
        color: {
          background: color,
          border: color,
          highlight: {
            background: '#ffd700',
            border: '#ffa500'
          }
        },
        font: {
          color: '#ffffff',
          size: 12,
          face: 'Arial'
        },
        size: size,
        shape: node.depth === 0 ? 'star' : 'dot',
        borderWidth: 2
      };
    });

    // Prepare edges for vis-network
    const visEdges = graphData.edges.map(edge => {
      const fromId = urlToId.get(edge.from_url);
      const toId = urlToId.get(edge.to_url);
      
      if (fromId === undefined || toId === undefined) {
        console.warn('🚨 GRAPH: Edge references unknown node:', edge);
        return null;
      }
      
      return {
        from: fromId,
        to: toId,
        arrows: 'to',
        color: {
          color: '#cbd5e0',
          highlight: '#4299e1',
          hover: '#4299e1'
        },
        width: 1,
        smooth: {
          type: 'continuous',
          roundness: 0.5
        }
      };
    }).filter(edge => edge !== null);

    // Create network
    const data = {
      nodes: visNodes,
      edges: visEdges
    };

    const options = {
      nodes: {
        font: {
          color: '#ffffff',
          size: 12
        }
      },
      edges: {
        font: {
          color: '#333',
          size: 10
        }
      },
      physics: {
        enabled: true,
        stabilization: {
          enabled: true,
          iterations: 200,
          updateInterval: 25
        },
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 150,
          springConstant: 0.04,
          damping: 0.09,
          avoidOverlap: 0.1
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        zoomView: true,
        dragView: true
      },
      layout: {
        improvedLayout: true,
        hierarchical: {
          enabled: false
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

