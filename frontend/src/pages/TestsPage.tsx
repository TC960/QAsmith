import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';
import GraphVisualization from '../components/GraphVisualization';
import './TestsPage.css';

interface GraphNode {
  id: string;
  label: string;
  url: string;
  depth: number;
}

interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface CrawlSummary {
  crawl_id: string;
  base_url: string;
  domain: string;
  status: string;
  page_count: number;
  element_count: number;
  link_count: number;
}

const TestsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const crawlId = searchParams.get('crawl_id');
  const baseUrl = searchParams.get('base_url');
  
  const [selectedStartPage, setSelectedStartPage] = useState<string>('');
  const [selectedEndPage, setSelectedEndPage] = useState<string>('');
  const [showTestGeneration, setShowTestGeneration] = useState(false);

  // Fetch crawl summary
  const { data: crawlSummary, isLoading: summaryLoading } = useQuery<CrawlSummary>({
    queryKey: ['crawl-summary', crawlId],
    queryFn: async () => {
      if (!crawlId) throw new Error('No crawl ID provided');
      const response = await axios.get(`/api/crawl/${crawlId}/summary`);
      return response.data;
    },
    enabled: !!crawlId,
  });

  // Fetch graph visualization data
  const { data: graphData, isLoading: graphLoading } = useQuery<GraphData>({
    queryKey: ['graph-viz', crawlId],
    queryFn: async () => {
      if (!crawlId) throw new Error('No crawl ID provided');
      const response = await axios.get(`/api/graph/${crawlId}/visualize`);
      return response.data;
    },
    enabled: !!crawlId,
  });

  // Generate tests mutation
  const generateTestsMutation = useMutation({
    mutationFn: async () => {
      if (!crawlId || !selectedStartPage || !selectedEndPage) {
        throw new Error('Missing required data for test generation');
      }
      const response = await axios.post('/api/generate-tests', {
        crawl_id: crawlId,
        start_url: selectedStartPage,
        end_url: selectedEndPage,
      });
      return response.data;
    },
    onSuccess: (data) => {
      alert(`✅ Generated ${data.test_count} test cases! Suite ID: ${data.suite_id}`);
    },
    onError: (error) => {
      console.error('Test generation failed:', error);
      alert('❌ Test generation failed. Check console for details.');
    },
  });

  const handleGenerateTests = () => {
    if (!selectedStartPage || !selectedEndPage) {
      alert('Please select both start and end pages');
      return;
    }
    generateTestsMutation.mutate();
  };

  if (!crawlId) {
    return (
      <div className="tests-page">
        <h1 className="page-title">Test Management</h1>
        <div className="error-message">
          <p>❌ No crawl data found. Please crawl a website first.</p>
          <a href="/crawl">Go to Crawl Page</a>
        </div>
      </div>
    );
  }

  return (
    <div className="tests-page">
      <h1 className="page-title">Website Graph & Test Generation</h1>
      
      {crawlSummary && (
        <div className="crawl-summary">
          <h2>Crawl Summary</h2>
          <div className="summary-stats">
            <div className="stat">
              <span className="stat-label">Website:</span>
              <span className="stat-value">{crawlSummary.base_url}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Pages Found:</span>
              <span className="stat-value">{crawlSummary.page_count}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Interactive Elements:</span>
              <span className="stat-value">{crawlSummary.element_count}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Links:</span>
              <span className="stat-value">{crawlSummary.link_count}</span>
            </div>
          </div>
        </div>
      )}

      {graphLoading && (
        <div className="loading">
          <p>🔄 Loading graph visualization...</p>
        </div>
      )}

      {graphData && (
        <div className="graph-section">
          <h2>🌐 Interactive Website Graph</h2>
          
          {/* Interactive Graph Visualization */}
          <GraphVisualization 
            graphData={{
              nodes: graphData.nodes.map(node => ({
                url: node.url,
                title: node.label || 'Untitled',
                depth: node.depth,
                page_id: node.id
              })),
              edges: graphData.edges.map(edge => ({
                from_url: edge.source,
                to_url: edge.target
              }))
            }}
            onNodeClick={(node) => {
              console.log('📍 TESTS: Node clicked from graph:', node);
              if (!selectedStartPage) {
                setSelectedStartPage(node.url);
              } else if (!selectedEndPage && node.url !== selectedStartPage) {
                setSelectedEndPage(node.url);
              }
            }}
          />

          <div className="graph-container">
            <div className="simple-graph">
              <h3>📋 Select Test Journey ({graphData.nodes.length} Pages)</h3>
              <p className="help-text">
                Click nodes in the graph above or buttons below to select start/end pages
              </p>
              <div className="nodes-list">
                {graphData.nodes.map((node) => (
                  <div key={node.id} className="node-item">
                    <div className="node-info">
                      <strong>{node.label || 'Untitled Page'}</strong>
                      <small>{node.url}</small>
                      <span className="depth-badge">Depth: {node.depth}</span>
                    </div>
                    <div className="node-actions">
                      <button
                        onClick={() => setSelectedStartPage(node.url)}
                        className={selectedStartPage === node.url ? 'selected' : ''}
                      >
                        Set as Start
                      </button>
                      <button
                        onClick={() => setSelectedEndPage(node.url)}
                        className={selectedEndPage === node.url ? 'selected' : ''}
                      >
                        Set as End
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {graphData.edges.length > 0 && (
                <div className="edges-info">
                  <h3>Navigation Links ({graphData.edges.length})</h3>
                  <div className="edges-list">
                    {graphData.edges.slice(0, 10).map((edge, index) => (
                      <div key={index} className="edge-item">
                        <span>From: {edge.source}</span>
                        <span>→</span>
                        <span>To: {edge.target}</span>
                        {edge.label && <small>({edge.label})</small>}
                      </div>
                    ))}
                    {graphData.edges.length > 10 && (
                      <p>... and {graphData.edges.length - 10} more links</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="test-generation-section">
            <h2>Generate Test Cases</h2>
            <div className="selection-summary">
              <div className="selection-item">
                <strong>Start Page:</strong>
                <span>{selectedStartPage || 'Not selected'}</span>
              </div>
              <div className="selection-item">
                <strong>End Page:</strong>
                <span>{selectedEndPage || 'Not selected'}</span>
              </div>
            </div>

            <button
              onClick={handleGenerateTests}
              disabled={!selectedStartPage || !selectedEndPage || generateTestsMutation.isPending}
              className="generate-tests-btn"
            >
              {generateTestsMutation.isPending ? '🤖 Generating Tests...' : '🚀 Generate AI Tests'}
            </button>

            {generateTestsMutation.isSuccess && (
              <div className="success-message">
                <p>✅ Test generation completed!</p>
                <p>Generated {generateTestsMutation.data.test_count} test cases</p>
                <p>Suite ID: {generateTestsMutation.data.suite_id}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TestsPage;