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

  // Update progress and dynamic nodes height
  useEffect(() => {
    if (crawlId) {
      window.localStorage.setItem('qa_progress_step', '3'); // Generate Tests step when on Tests page
      window.dispatchEvent(new Event('qa_progress_changed'));
    }
  }, [crawlId]);

  useEffect(() => {
    const root = document.documentElement;
    const count = graphData?.nodes?.length || 0;
    // Base height 200px + 56px per 4 items, clamp between 200 and 720
    const rows = Math.ceil(count / 1); // each node-item is one row in current layout
    const height = Math.min(720, Math.max(200, 120 + rows * 72));
    root.style.setProperty('--nodes-max-height', `${height}px`);
  }, [graphData]);

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
      window.localStorage.setItem('qa_progress_step', '5');
      window.dispatchEvent(new Event('qa_progress_changed'));
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

  // Convert markdown text to sanitized HTML (basic renderer)
  const renderMarkdown = (text: string): string => {
    if (!text) return '';

    let html = text;

    // Escape HTML first to avoid injection, then unescape inside code blocks
    html = html
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Fenced code blocks ```lang\ncode\n```
    html = html.replace(/```[a-zA-Z0-9_-]*\n[\s\S]*?```/g, (block) => {
      const content = block.replace(/^```[a-zA-Z0-9_-]*\n/, '').replace(/```$/, '');
      const unescaped = content.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
      return `<pre><code>${unescaped}</code></pre>`;
    });

    // Headings
    html = html
      .replace(/^######\s+(.*)$/gm, '<h6>$1</h6>')
      .replace(/^#####\s+(.*)$/gm, '<h5>$1</h5>')
      .replace(/^####\s+(.*)$/gm, '<h4>$1</h4>')
      .replace(/^###\s+(.*)$/gm, '<h3>$1</h3>')
      .replace(/^##\s+(.*)$/gm, '<h2>$1</h2>')
      .replace(/^#\s+(.*)$/gm, '<h1>$1</h1>');

    // Bold/Italic
    html = html
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/(?<!\*)\*(?!\*)([^*]+)\*(?!\*)/g, '<em>$1</em>');

    // Inline code `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Links [text](url)
    html = html.replace(/\[(.*?)\]\((https?:[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer noopener">$1</a>');

    // Lists
    html = html
      .replace(/^(?:- |\* )(.*)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\s*)+/g, (m) => `<ul>${m}</ul>`)
      .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\s*)+/g, (m) => (m.includes('<ul>') ? m : `<ol>${m}</ol>`));

    // Paragraphs: wrap top-level lines that are not already block elements
    html = html
      .split(/\n{2,}/)
      .map((chunk) => {
        if (/^\s*<\/?(h\d|ul|ol|li|pre|code|blockquote)/.test(chunk)) return chunk;
        if (!chunk.trim()) return '';
        return `<p>${chunk.replace(/\n/g, '<br/>')}</p>`;
      })
      .join('');

    return html;
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
                onClick={() => {
                  window.localStorage.setItem('qa_progress_step', '3');
                  window.dispatchEvent(new Event('qa_progress_changed'));
                  handleGenerateTests();
                }}
                disabled={selectedPages.length === 0 || generateTestsMutation.isPending}
                className="generate-tests-btn"
              >
                {generateTestsMutation.isPending ? '🤖 Generating Tests with AI...' : '🚀 Generate AI Tests'}
              </button>

              {generatedSuiteId && (
                <button
                  onClick={() => {
                    window.localStorage.setItem('qa_progress_step', '4');
                    window.dispatchEvent(new Event('qa_progress_changed'));
                    runTestsMutation.mutate(generatedSuiteId);
                  }}
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
                    <div className="ai-summary-header">
                      <h3>🤖 AI Analysis</h3>
                      <div className="ai-actions">
                        <button
                          type="button"
                          className="ai-btn"
                          onClick={() => {
                            navigator.clipboard.writeText(testResults.ai_summary);
                          }}
                        >
                          Copy
                        </button>
                        <button
                          type="button"
                          className="ai-btn"
                          onClick={() => {
                            const box = document.querySelector('.ai-summary-text');
                            if (!box) return;
                            box.classList.toggle('collapsed');
                          }}
                        >
                          Toggle
                        </button>
                      </div>
                    </div>
                    <div
                      className="ai-summary-text"
                      dangerouslySetInnerHTML={{
                        __html: renderMarkdown(testResults.ai_summary)
                      }}
                    />
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