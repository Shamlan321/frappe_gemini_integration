import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

import Sidebar from './components/Sidebar';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import Configuration from './components/Configuration';
import Outreach from './components/Outreach';
import EmailTemplateBuilder from './components/EmailTemplateBuilder';
import EmailTracking from './components/EmailTracking';
import EmailServerConfig from './components/EmailServerConfig';
import LeadGeneration from './components/LeadGeneration';
import { AuthProvider, useAuth } from './context/AuthContext';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/lead-generation" element={<PrivateRoute><LeadGeneration /></PrivateRoute>} />
            <Route path="/configuration" element={<PrivateRoute><Configuration /></PrivateRoute>} />
            <Route path="/outreach" element={<PrivateRoute><Outreach /></PrivateRoute>} />
            <Route path="/email-templates" element={<PrivateRoute><EmailTemplateBuilder /></PrivateRoute>} />
            <Route path="/email-tracking" element={<PrivateRoute><EmailTracking /></PrivateRoute>} />
            <Route path="/email-servers" element={<PrivateRoute><EmailServerConfig /></PrivateRoute>} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}

export default App;