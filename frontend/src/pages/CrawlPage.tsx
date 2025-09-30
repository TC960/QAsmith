import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import './CrawlPage.css';

const CrawlPage: React.FC = () => {
  const [url, setUrl] = useState('');

  const crawlMutation = useMutation({
    mutationFn: async (targetUrl: string) => {
      const response = await axios.post('/api/crawl', { url: targetUrl });
      return response.data;
    },
    onSuccess: (data) => {
      console.log('Crawl complete:', data);
      alert(`Successfully crawled ${data.total_pages} pages!`);
    },
    onError: (error) => {
      console.error('Crawl failed:', error);
      alert('Crawl failed. Check console for details.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url) {
      crawlMutation.mutate(url);
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
            disabled={crawlMutation.isPending}
            className="url-input"
          />
        </div>

        <button
          type="submit"
          disabled={crawlMutation.isPending}
          className="submit-button"
        >
          {crawlMutation.isPending ? 'Crawling...' : 'Start Crawl'}
        </button>
      </form>

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