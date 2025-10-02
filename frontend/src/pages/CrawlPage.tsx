import React, { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import CrawlerSettings, { CrawlerConfig } from '../components/CrawlerSettings';
import './CrawlPage.css';

interface CrawlProgress {
  type: string;
  url?: string;
  title?: string;
  depth?: number;
  visited?: number;
  page_id?: string;
  error?: string;
  crawl_id?: string;
  summary?: any;
}

const CrawlPage: React.FC = () => {
  const [url, setUrl] = useState('');
  const [useWebSocket, setUseWebSocket] = useState(true);
  const [crawlProgress, setCrawlProgress] = useState<CrawlProgress[]>([]);
  const [isWebSocketCrawling, setIsWebSocketCrawling] = useState(false);
  const [crawlerSettings, setCrawlerSettings] = useState<CrawlerConfig>({
    max_depth: 2,
    max_pages: 20,
    timeout: 15000,
    screenshot: false,
    page_delay_ms: 300,
    skip_embeddings: true
  });
  const wsRef = useRef<WebSocket | null>(null);
  const navigate = useNavigate();
  
  // Fetch current crawler config
  const { data: configData } = useQuery<CrawlerConfig>({
    queryKey: ['crawler-config'],
    queryFn: async () => {
      const response = await axios.get('/api/config/crawler');
      return response.data;
    },
    onSuccess: (data) => {
      setCrawlerSettings(data);
    },
    onError: (error) => {
      console.error('Failed to fetch crawler config:', error);
    }
  });

  const crawlMutation = useMutation({
    mutationFn: async (targetUrl: string) => {
      console.log('🚀 FRONTEND: Starting crawl request for:', targetUrl);
      try {
        const response = await axios.post('/api/crawl', { url: targetUrl });
        console.log('✅ FRONTEND: Crawl API response:', response.data);
        return response.data;
      } catch (error) {
        console.error('❌ FRONTEND: Crawl API error:', error);
        if (axios.isAxiosError(error)) {
          console.error('❌ FRONTEND: Response data:', error.response?.data);
          console.error('❌ FRONTEND: Response status:', error.response?.status);
        }
        throw error;
      }
    },
    onSuccess: (data) => {
      console.log('🎉 FRONTEND: Crawl completed successfully:', data);
      console.log('🔄 FRONTEND: Redirecting to tests page...');
      // Redirect to tests page with crawl data
      navigate(`/tests?crawl_id=${data.crawl_id}&base_url=${encodeURIComponent(data.base_url)}`);
    },
    onError: (error) => {
      console.error('❌ FRONTEND: Crawl mutation failed:', error);
      if (axios.isAxiosError(error)) {
        const errorMessage = error.response?.data?.detail || error.message;
        alert(`Crawl failed: ${errorMessage}`);
      } else {
        alert('Crawl failed. Check console for details.');
      }
    },
  });

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Progress step when on crawl page
  useEffect(() => {
    window.localStorage.setItem('qa_progress_step', '2');
    window.dispatchEvent(new Event('qa_progress_changed'));
  }, []);

  const startWebSocketCrawl = (targetUrl: string) => {
    console.log('🔌 FRONTEND: Starting WebSocket crawl for:', targetUrl);
    setCrawlProgress([]);
    setIsWebSocketCrawling(true);
    window.localStorage.setItem('qa_progress_step', '2');
    window.dispatchEvent(new Event('qa_progress_changed'));
    
    // Generate session ID
    const sessionId = `crawl_${Date.now()}`;
    
    // Connect to WebSocket
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/ws/crawl/${sessionId}`;
    
    console.log('🔌 FRONTEND: Connecting to WebSocket:', wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('✅ FRONTEND: WebSocket connected');
      // Send the URL and settings to crawl
      ws.send(JSON.stringify({ 
        url: targetUrl,
        settings: crawlerSettings
      }));
      console.log('📤 FRONTEND: Sent crawl settings:', crawlerSettings);
      setCrawlProgress(prev => [...prev, { type: 'connected', url: targetUrl }]);
    };
    
    ws.onmessage = (event) => {
      const data: CrawlProgress = JSON.parse(event.data);
      
      // Skip heartbeats from logs (but still process them to keep connection alive)
      if (data.type !== 'heartbeat') {
        console.log('📡 FRONTEND: WebSocket message:', data);
        setCrawlProgress(prev => [...prev, data]);
      }
      
      if (data.type === 'crawl_complete') {
        console.log('🎉 FRONTEND: Crawl complete via WebSocket:', data);
        setIsWebSocketCrawling(false);
        ws.close();
        
        // Navigate to tests page
        setTimeout(() => {
          navigate(`/tests?crawl_id=${data.crawl_id}&base_url=${encodeURIComponent(targetUrl)}`);
        }, 1000);
      } else if (data.type === 'error') {
        console.error('❌ FRONTEND: WebSocket crawl error:', data.error);
        setIsWebSocketCrawling(false);
        ws.close();
        alert(`Crawl failed: ${data.error}`);
      }
      
      // Update progress stats for UI
      if (data.type === 'page_complete') {
        const completedPages = crawlProgress.filter(p => p.type === 'page_complete').length + 1;
        console.log(`📊 FRONTEND: Crawled ${completedPages} pages so far`);
      }
    };
    
    ws.onerror = (error) => {
      console.error('❌ FRONTEND: WebSocket error:', error);
      setIsWebSocketCrawling(false);
      setCrawlProgress(prev => [...prev, { type: 'error', error: 'WebSocket connection failed' }]);
    };
    
    ws.onclose = () => {
      console.log('🔌 FRONTEND: WebSocket closed');
      setIsWebSocketCrawling(false);
    };
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url) {
      if (useWebSocket) {
        startWebSocketCrawl(url);
      } else {
        crawlMutation.mutate(url);
      }
    }
  };

  return (
    <div className="crawl-page">
      <h1 className="page-title">Crawl Website</h1>
      <p className="page-description">
        Enter a website URL to start crawling. QAsmith will map all pages, forms, and interactive elements.
      </p>

      <form onSubmit={handleSubmit} className="crawl-form">
        <div className="form-group">
          <label htmlFor="url">Website URL</label>
          <input
            type="url"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            required
            disabled={crawlMutation.isPending || isWebSocketCrawling}
            className="url-input"
          />
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useWebSocket}
              onChange={(e) => setUseWebSocket(e.target.checked)}
              disabled={crawlMutation.isPending || isWebSocketCrawling}
            />
            <span>Real-time progress updates (WebSocket)</span>
          </label>
        </div>
        
        {/* Crawler Settings Panel */}
        <CrawlerSettings 
          settings={crawlerSettings}
          onSettingsChange={setCrawlerSettings}
          disabled={crawlMutation.isPending || isWebSocketCrawling}
        />

        <button
          type="submit"
          disabled={crawlMutation.isPending || isWebSocketCrawling}
          className="submit-button"
        >
          {(crawlMutation.isPending || isWebSocketCrawling) ? 'Crawling...' : 'Start Crawl'}
        </button>
      </form>

      {/* Real-time progress display */}
      {isWebSocketCrawling && crawlProgress.length > 0 && (
        <div className="progress-container">
          <h3>🕷️ Crawl Progress</h3>
          <div className="progress-log">
            {crawlProgress.slice(-10).reverse().map((progress, idx) => (
              <div key={idx} className={`progress-item ${progress.type}`}>
                {progress.type === 'page_loading' && (
                  <span>🔍 Loading: {progress.url} (depth: {progress.depth})</span>
                )}
                {progress.type === 'page_complete' && (
                  <span>✅ Completed: {progress.title || progress.url}</span>
                )}
                {progress.type === 'page_error' && (
                  <span>❌ Error: {progress.url} - {progress.error}</span>
                )}
                {progress.type === 'crawl_start' && (
                  <span>🚀 Starting crawl for: {progress.url}</span>
                )}
                {progress.type === 'crawl_complete' && (
                  <span>🎉 Crawl complete! Found {progress.summary?.page_count || 0} pages</span>
                )}
              </div>
            ))}
          </div>
          <div className="progress-stats">
            <p>Pages visited: {crawlProgress.filter(p => p.type === 'page_complete').length}</p>
          </div>
        </div>
      )}

      {crawlMutation.isPending && (
        <div className="status-message info">
          <p>Crawling in progress... This may take a few minutes.</p>
        </div>
      )}

      {crawlMutation.isSuccess && (
        <div className="status-message success">
          <p>✓ Crawl completed successfully!</p>
          <p>Found {crawlMutation.data.total_pages} pages</p>
        </div>
      )}

      {crawlMutation.isError && (
        <div className="status-message error">
          <p>✗ Crawl failed</p>
        </div>
      )}
    </div>
  );
};

export default CrawlPage;