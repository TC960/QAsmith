import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import CrawlPage from './pages/CrawlPage';
import TestsPage from './pages/TestsPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/crawl" element={<CrawlPage />} />
        <Route path="/tests" element={<TestsPage />} />
        <Route path="/results" element={<ResultsPage />} />
      </Routes>
    </Layout>
  );
}

export default App;