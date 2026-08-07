import React, { useState } from 'react';
import api from '../lib/api';
import toast from 'react-hot-toast';
import { LogIn, User, Key, Building, AlertCircle } from 'lucide-react';

const Login = ({ onLoginSuccess }: { onLoginSuccess: () => void }) => {
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [shake, setShake] = useState(false);

  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      const res = await api.post('/auth/login', formData.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      localStorage.setItem('token', res.data.access_token);
      if (res.data.refresh_token) {
        localStorage.setItem('refresh_token', res.data.refresh_token);
      }
      toast.success('Đăng nhập thành công!');
      onLoginSuccess();
    } catch (err: any) {
      // Phân biệt ba tình huống khác hẳn nhau. Trước đây gộp hết thành "sai tài
      // khoản hoặc mật khẩu", nên khi máy chủ không phản hồi hoặc bị chặn CORS,
      // người dùng cứ ngỡ mình gõ sai mật khẩu và loay hoay không rõ nguyên nhân.
      let msg: string;

      if (!err.response) {
        // Không nhận được phản hồi: máy chủ chưa chạy, mất mạng, hoặc bị CORS chặn
        msg =
          'Không kết nối được máy chủ. Kiểm tra máy chủ đã chạy chưa và ' +
          'địa chỉ giao diện đã được phép gọi API (biến CORS_ORIGINS).';
      } else {
        const detail = err.response?.data?.detail;
        if (typeof detail === 'string' && detail) {
          // Máy chủ có nêu lý do cụ thể — hiện đúng lý do đó, ví dụ trường hợp
          // tài khoản dùng mật khẩu mặc định bị chặn trên môi trường thật
          msg = detail;
        } else if (err.response.status === 401) {
          msg = 'Tài khoản hoặc mật khẩu không chính xác.';
        } else {
          msg = `Máy chủ trả về lỗi ${err.response.status}. Vui lòng thử lại.`;
        }
      }

      setErrorMsg(msg);
      toast.error(msg, { duration: 7000 });
      setPassword(''); // Xoá password để người dùng nhập lại dễ hơn
      setShake(true);
      setTimeout(() => setShake(false), 500);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-gray-100">
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-blue-200 transform rotate-3">
            <Building className="text-white w-8 h-8 -rotate-3" />
          </div>
          <h2 className="text-2xl font-extrabold text-gray-900 tracking-tight">Hệ thống Tính điểm KPI</h2>
          <p className="text-gray-600 mt-1 text-sm font-medium">Công an nhân dân</p>
          <p className="text-gray-400 mt-2 text-xs leading-relaxed">
            Đánh giá, xếp loại chất lượng tập thể, cá nhân<br />
            theo Hướng dẫn số 20-HD/ĐUCA
          </p>
        </div>

        {errorMsg && (
          <div className="mb-6 p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg flex items-start gap-2 text-sm font-medium">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleAuth} className={`space-y-5 ${shake ? 'animate-shake' : ''}`}>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Tên đăng nhập</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User size={18} className="text-gray-400" />
              </div>
              <input 
                type="text" required value={username} onChange={e => setUsername(e.target.value)}
                className="pl-10 w-full px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                placeholder="username"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Mật khẩu</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Key size={18} className="text-gray-400" />
              </div>
              <input 
                type="password" required value={password} onChange={e => setPassword(e.target.value)}
                className="pl-10 w-full px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-xl focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 border border-transparent rounded-xl shadow-sm text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="animate-pulse">Đang xử lý...</span>
            ) : (
              <><LogIn size={18} /> Đăng nhập</>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
