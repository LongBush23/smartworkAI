import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, lazy, Suspense } from 'react';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import Login from './pages/Login';

/*
 * Các trang nạp theo nhu cầu.
 *
 * Trước đây toàn bộ ứng dụng nằm trong một khối JavaScript 846 KB, phải tải và
 * phân tích xong mới gọi được API đầu tiên. Đo trên bản triển khai: 2,1 giây
 * trôi qua trước khi có bất kỳ yêu cầu nào rời trình duyệt.
 *
 * Người dùng mở app chỉ nhìn thấy Trang chủ. Mười trang còn lại — kể cả thư
 * viện biểu đồ nặng nề đi kèm — không cần có mặt ngay lúc đó.
 *
 * Layout và Login KHÔNG nạp theo nhu cầu: cái nào cũng cần ngay ở khung hình
 * đầu tiên, tách ra chỉ thêm một vòng tải.
 */
const Dashboard      = lazy(() => import('./pages/Dashboard'));
const Tasks          = lazy(() => import('./pages/Tasks'));
const Employees      = lazy(() => import('./pages/Employees'));
const Profile        = lazy(() => import('./pages/Profile'));
const Notifications  = lazy(() => import('./pages/Notifications'));
const AuditLogs      = lazy(() => import('./pages/AuditLogs'));
const KPIDashboard   = lazy(() => import('./pages/KPIDashboard'));
const KPICatalogPage = lazy(() => import('./pages/KPICatalog'));
const KPIEvaluate    = lazy(() => import('./pages/KPIEvaluate'));
const KPIResults     = lazy(() => import('./pages/KPIResults'));
const KPICriteria    = lazy(() => import('./pages/KPICriteria'));
const Organization   = lazy(() => import('./pages/Organization'));
const EmployeeDetail = lazy(() => import('./pages/EmployeeDetail'));
const QualityReview  = lazy(() => import('./pages/QualityReview'));

const DangTai = () => (
  <div className="flex justify-center items-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy-600" />
  </div>
);

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));

  return (
    <>
      <Toaster position="top-right" />
      {!isAuthenticated ? (
        <Login onLoginSuccess={() => setIsAuthenticated(true)} />
      ) : (
        <Router>
          <Suspense fallback={<DangTai />}>
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
                <Route path="quality-review" element={<QualityReview />} />
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
          </Suspense>
        </Router>
      )}
    </>
  );
}

export default App;
