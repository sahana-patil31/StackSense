import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { useState } from 'react';
import DashboardPage from './pages/DashboardPage';
import { CodeIntelligencePage } from './pages/CodeIntelligencePage';
import { RiskDashboardPage } from './pages/RiskDashboardPage';
import { AnomaliesPage } from './pages/AnomaliesPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { AssistantPage } from './pages/AssistantPage';
import { LoginPage } from './pages/LoginPage';
import { RepositoriesPage } from './pages/RepositoriesPage';
import { SettingsPage } from './pages/SettingsPage';
import type { AuthResponse } from './types/auth';

const ProtectedRoutes = () => (
  <Routes>
    <Route path="/" element={<DashboardPage />} />
    <Route path="/dashboard" element={<DashboardPage />} />
    <Route path="/code-intelligence" element={<CodeIntelligencePage />} />
    <Route path="/risk" element={<RiskDashboardPage />} />
    <Route path="/anomalies" element={<AnomaliesPage />} />
    <Route path="/incidents" element={<IncidentsPage />} />
    <Route path="/assistant" element={<AssistantPage />} />
    <Route path="/repositories" element={<RepositoriesPage />} />
    <Route path="/settings" element={<SettingsPage />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);

function App() {
  const [session, setSession] = useState<AuthResponse | null>(() => {
    const token = localStorage.getItem('stacksense_token');
    const rawUser = localStorage.getItem('stacksense_user');
    return token && rawUser ? { access_token: token, token_type: 'bearer', user: JSON.parse(rawUser) } : null;
  });

  const authenticated = (response: AuthResponse) => {
    localStorage.setItem('stacksense_token', response.access_token);
    localStorage.setItem('stacksense_user', JSON.stringify(response.user));
    setSession(response);
  };

  return (
    <BrowserRouter>
      {session ? <ProtectedRoutes /> : <Routes><Route path="/login" element={<LoginPage onAuthenticated={authenticated} />} /><Route path="*" element={<LoginPage onAuthenticated={authenticated} />} /></Routes>}
    </BrowserRouter>
  );
}

export default App;
