import React from 'react';
import './ResultsPage.css';

const ResultsPage: React.FC = () => {
  return (
    <div className="results-page">
      <h1 className="page-title">Test Results</h1>
      <p className="page-description">
        View test run history and detailed reports with AI-powered failure analysis.
      </p>

      <div className="placeholder">
        <p>🚧 Results dashboard coming soon</p>
        <ul className="feature-list">
          <li>View test run history</li>
          <li>Browse HTML reports</li>
          <li>AI-generated failure summaries</li>
          <li>Screenshots & video recordings</li>
          <li>Trace viewer integration</li>
        </ul>
      </div>
    </div>
  );
};

export default ResultsPage;