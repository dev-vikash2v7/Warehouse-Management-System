import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { UploadPage } from './pages/UploadPage';
import { DashboardPage } from './pages/DashboardPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { Navigation } from './components/Navigation';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 