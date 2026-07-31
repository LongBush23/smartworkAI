import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Tasks from './pages/Tasks';
import Employees from './pages/Employees';
import Login from './pages/Login';
import Profile from './pages/Profile';
import Notifications from './pages/Notifications';
import AuditLogs from './pages/AuditLogs';
import KPIDashboard from './pages/KPIDashboard';
import KPICatalogPage from './pages/KPICatalog';
import KPIEvaluate from './pages/KPIEvaluate';
import KPIResults from './pages/KPIResults';
import KPICriteria from './pages/KPICriteria';
import Organization from './pages/Organization';
import EmployeeDetail from './pages/EmployeeDetail';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));

  return (
    <>
      <Toaster position="top-right" />
      {!isAuthenticated ? (
        <Login onLoginSuccess={() => setIsAuthenticated(true)} />
      ) : (
        <Router>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="tasks" element={<Tasks />} />
              <Route path="organization" element={<Organization />} />
              <Route path="employees" element={<Employees />} />
              <Route path="employees/:id" element={<EmployeeDetail />} />
              <Route path="profile" element={<Profile />} />
              <Route path="notifications" element={<Notifications />} />
              <Route path="audit-logs" element={<AuditLogs />} />
              <Route path="kpi">
                <Route index element={<KPIDashboard />} />
                <Route path="catalog" element={<KPICatalogPage />} />
                <Route path="evaluate" element={<KPIEvaluate />} />
                <Route path="criteria" element={<KPICriteria />} />
                <Route path="results" element={<KPIResults />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </Router>
      )}
    </>
  );
}

export default App;
