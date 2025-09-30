import React from 'react';
import './TestsPage.css';

const TestsPage: React.FC = () => {
  return (
    <div className="tests-page">
      <h1 className="page-title">Test Management</h1>
      <p className="page-description">
        Generate, compile, and manage your test suites.
      </p>

      <div className="placeholder">
        <p>🚧 Test management UI coming soon</p>
        <ul className="feature-list">
          <li>View app maps</li>
          <li>Generate test cases with AI</li>
          <li>Compile to Playwright specs</li>
          <li>Select pages to test</li>
        </ul>
      </div>
    </div>
  );
};

export default TestsPage;