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
  
  const [selectedPages, setSelectedPages] = useState<string[]>([]);
  const [showTestGeneration, setShowTestGeneration] = useState(false);
  const [generatedSuiteId, setGeneratedSuiteId] = useState<string | null>(null);

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
      console.log('🔍 TESTS PAGE: Raw API response:', response.data);
      console.log('🔍 TESTS PAGE: Nodes:', response.data.nodes?.length, 'Edges:', response.data.edges?.length);
      console.log('🔍 TESTS PAGE: First edge:', response.data.edges?.[0]);
      return response.data;
    },
    enabled: !!crawlId,
  });

  // Generate tests mutation
  const generateTestsMutation = useMutation({
    mutationFn: async () => {
      if (!crawlId || selectedPages.length === 0) {
        throw new Error('Missing required data for test generation');
      }
      const response = await axios.post('/api/generate-tests', {
        crawl_id: crawlId,
        page_urls: selectedPages,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setGeneratedSuiteId(data.test_suite_id);
      alert(`✅ Generated ${data.test_count} test cases! Suite ID: ${data.test_suite_id}`);
    },
    onError: (error) => {
      console.error('Test generation failed:', error);
      alert('❌ Test generation failed. Check console for details.');
    },
  });

  // Compile tests mutation
  const compileTestsMutation = useMutation({
    mutationFn: async (suiteId: string) => {
      const response = await axios.post('/api/compile-tests', {
        suite_id: suiteId,
      });
      return response.data;
    },
    onSuccess: (data) => {
      alert(`✅ Tests compiled successfully!\n${data.spec_file_path}`);
    },
    onError: (error) => {
      console.error('Compilation failed:', error);
      alert('❌ Compilation failed. Check console for details.');
    },
  });

  // State for test results
  const [testResults, setTestResults] = useState<any>(null);

  // Run tests mutation (with auto-compile)
  const runTestsMutation = useMutation({
    mutationFn: async (suiteId: string) => {
      // First, compile the tests
      await axios.post('/api/compile-tests', {
        suite_id: suiteId,
      });

      // Then run the tests
      const response = await axios.post('/api/run-tests', {
        suite_id: suiteId,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setTestResults(data);
    },
    onError: (error) => {
      console.error('Test run failed:', error);
      alert('❌ Test run failed. Check console for details.');
    },
  });

  const handleGenerateTests = () => {
    if (selectedPages.length === 0) {
      alert('Please select at least one page');
      return;
    }
    generateTestsMutation.mutate();
  };

  const togglePageSelection = (url: string) => {
    setSelectedPages(prev =>
      prev.includes(url)
        ? prev.filter(p => p !== url)
        : [...prev, url]
    );
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
              togglePageSelection(node.url);
            }}
          />

          <div className="graph-container">
            <div className="simple-graph">
              <h3>📋 Select Pages for Testing ({graphData.nodes.length} Pages)</h3>
              <p className="help-text">
                Click nodes in the graph above or checkboxes below to select pages for test generation
              </p>
              <div className="nodes-list">
                {graphData.nodes.map((node) => (
                  <div key={node.id} className={`node-item ${selectedPages.includes(node.url) ? 'selected' : ''}`}>
                    <div className="node-info">
                      <input
                        type="checkbox"
                        checked={selectedPages.includes(node.url)}
                        onChange={() => togglePageSelection(node.url)}
                        className="page-checkbox"
                      />
                      <div>
                        <strong>{node.label || 'Untitled Page'}</strong>
                        <small>{node.url}</small>
                        <span className="depth-badge">Depth: {node.depth}</span>
                      </div>
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
            <h2>🤖 Generate AI Test Cases</h2>
            <div className="selection-summary">
              <div className="selection-item">
                <strong>Selected Pages:</strong>
                <span>{selectedPages.length > 0 ? `${selectedPages.length} page(s)` : 'None selected'}</span>
              </div>
              {selectedPages.length > 0 && (
                <div className="selected-pages-list">
                  {selectedPages.map((url, index) => (
                    <div key={url} className="selected-page-chip">
                      {index + 1}. {url}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="test-actions">
              <button
                onClick={handleGenerateTests}
                disabled={selectedPages.length === 0 || generateTestsMutation.isPending}
                className="generate-tests-btn"
              >
                {generateTestsMutation.isPending ? '🤖 Generating Tests with AI...' : '🚀 Generate AI Tests'}
              </button>

              {generatedSuiteId && (
                <button
                  onClick={() => runTestsMutation.mutate(generatedSuiteId)}
                  disabled={runTestsMutation.isPending}
                  className="run-tests-btn"
                >
                  {runTestsMutation.isPending ? '🏃 Compiling & Running Tests...' : '▶️ Run Tests (Visible)'}
                </button>
              )}
            </div>

            {generatedSuiteId && !testResults && (
              <div className="success-message">
                <p>✅ Test Suite Ready!</p>
                <p>Suite ID: <code>{generatedSuiteId}</code></p>
                <p>💡 Click "Run Tests" to compile and execute them with a visible browser!</p>
              </div>
            )}

            {testResults && (
              <div className="test-results-section">
                <h2>📊 Test Results</h2>

                <div className={`results-summary ${testResults.failed === 0 ? 'success' : 'warning'}`}>
                  <div className="results-stats">
                    <div className="stat-box passed">
                      <span className="stat-number">{testResults.passed}</span>
                      <span className="stat-label">Passed</span>
                    </div>
                    <div className="stat-box failed">
                      <span className="stat-number">{testResults.failed}</span>
                      <span className="stat-label">Failed</span>
                    </div>
                    <div className="stat-box total">
                      <span className="stat-number">{testResults.total_tests}</span>
                      <span className="stat-label">Total</span>
                    </div>
                  </div>
                </div>

                {testResults.ai_summary && (
                  <div className="ai-summary-box">
                    <h3>🤖 AI Analysis</h3>
                    <p className="ai-summary-text">{testResults.ai_summary}</p>
                  </div>
                )}

                {testResults.test_results && testResults.test_results.length > 0 && (
                  <div className="individual-results">
                    <h3>Individual Test Results</h3>
                    <div className="test-list">
                      {testResults.test_results.map((test: any, index: number) => (
                        <div key={index} className={`test-item ${test.status}`}>
                          <div className="test-header">
                            <span className="test-status-icon">
                              {test.status === 'passed' ? '✅' : '❌'}
                            </span>
                            <span className="test-name">{test.name}</span>
                          </div>
                          {test.error && (
                            <div className="test-error">
                              <pre>{test.error}</pre>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <button
                  onClick={() => {
                    setTestResults(null);
                    setGeneratedSuiteId(null);
                    setSelectedPages([]);
                  }}
                  className="reset-btn"
                >
                  🔄 Generate New Tests
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TestsPage;