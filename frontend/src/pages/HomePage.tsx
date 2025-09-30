import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';

const HomePage: React.FC = () => {
  return (
    <div className="home-page">
      <section className="hero">
        <h1 className="hero-title">AI-Powered E2E Test Generation</h1>
        <p className="hero-subtitle">
          Automatically generate comprehensive end-to-end tests for any website using AI
        </p>
        <Link to="/crawl" className="cta-button">
          Get Started
        </Link>
      </section>

      <section className="features">
        <h2 className="section-title">How It Works</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🕷️</div>
            <h3>1. Crawl</h3>
            <p>Point QAsmith at your website URL and let the Playwright crawler map your application</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>2. Generate</h3>
            <p>Claude AI analyzes your app structure and generates comprehensive test cases</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⚙️</div>
            <h3>3. Compile</h3>
            <p>Test cases are compiled into executable Playwright TypeScript specs</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🚀</div>
            <h3>4. Run & Report</h3>
            <p>Execute tests and view rich HTML reports with AI-powered failure analysis</p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;