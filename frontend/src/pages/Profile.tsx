import React, { useState, useEffect, useMemo } from 'react';
import api from '../lib/api';
import toast from 'react-hot-toast';
import { User, Mail, Shield, Key, Save, X, BrainCircuit, Target, Star, Award, TrendingUp, Clock, Search, FileText, Camera } from 'lucide-react';

interface Skill {
  skill_name: string;
  self_rating: number;
  verified_rating?: number | null;
}

interface Preferences {
  interests: string[];
  preferred_task_types: string[];
  max_concurrent_tasks: number;
}

const SKILL_CATEGORIES = [
  {
    id: "hanh-chinh",
    name: "🏛 Hành chính & Tổng hợp",
    skills: ["Soạn thảo văn bản", "Văn thư lưu trữ", "Quản lý con dấu", "Tổ chức sự kiện", "Lên lịch công tác"]
  },
  {
    id: "phap-che",
    name: "⚖️ Pháp chế & Thanh tra",
    skills: ["Xây dựng văn bản QPPL", "Tiếp công dân", "Giải quyết khiếu nại", "Thanh tra chuyên ngành", "Phổ biến pháp luật"]
  },
  {
    id: "tai-chinh",
    name: "💰 Tài chính & Đầu tư",
    skills: ["Lập dự toán ngân sách", "Kế toán công", "Nghiệp vụ đấu thầu", "Thẩm định dự án", "Giải ngân vốn"]
  },
  {
    id: "cong-nghe",
    name: "💻 Chuyển đổi số & CNTT",
    skills: ["Vận hành Cổng DVC", "Quản trị mạng", "An toàn thông tin", "Phân tích Dữ liệu", "Số hoá hồ sơ"]
  },
  {
    id: "ky-nang-mem",
    name: "🤝 Kỹ năng Bổ trợ",
    skills: ["Điều hành cuộc họp", "Xử lý khủng hoảng", "Tiếng Anh chuyên ngành", "Giao tiếp công chúng", "Tiếng Ê Đê"]
  }
];

const Profile = () => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [changingPass, setChangingPass] = useState(false);

  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [avatar, setAvatar] = useState('');
  const [skills, setSkills] = useState<Skill[]>([]);
  const [bio, setBio] = useState('');
  
  const [preferences, setPreferences] = useState<Preferences>({
    interests: [],
    preferred_task_types: [],
    max_concurrent_tasks: 3
  });
  
  const [newInterest, setNewInterest] = useState('');
  
  // Skill UI states
  const [activeCategory, setActiveCategory] = useState<string>("hanh-chinh");
  const [skillSearch, setSkillSearch] = useState('');

  // Password states
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      setName(res.data.name || '');
      setEmail(res.data.email || '');
      setAvatar(res.data.avatar || '');
      setBio(res.data.bio || '');
      setSkills(res.data.skills || []);
      if (res.data.preferences) {
        setPreferences(res.data.preferences);
      }
    } catch (error) {
      toast.error('Không thể tải thông tin cá nhân');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSkill = (skillName: string) => {
    const exists = skills.find(s => s.skill_name === skillName);
    if (exists) {
      setSkills(skills.filter(s => s.skill_name !== skillName));
    } else {
      setSkills([...skills, { skill_name: skillName, self_rating: 3 }]);
    }
  };

  const handleUpdateSkillRating = (skillName: string, rating: number) => {
    setSkills(skills.map(s => s.skill_name === skillName ? { ...s, self_rating: rating } : s));
  };

  const handleAddInterest = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && newInterest.trim() !== '') {
      e.preventDefault();
      if (!preferences.interests.includes(newInterest.trim())) {
        setPreferences({...preferences, interests: [...preferences.interests, newInterest.trim()]});
      }
      setNewInterest('');
    }
  };

  const handleRemoveInterest = (item: string) => {
    setPreferences({...preferences, interests: preferences.interests.filter(i => i !== item)});
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.put('/auth/profile', {
        name,
        email,
        avatar,
        bio,
        skills,
        preferences
      });
      toast.success('Cập nhật hồ sơ thành công');
      fetchProfile();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Lỗi cập nhật hồ sơ');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error('Mật khẩu xác nhận không khớp');
      return;
    }
    if (newPassword.length < 6) {
      toast.error('Mật khẩu mới phải có ít nhất 6 ký tự');
      return;
    }
    
    setChangingPass(true);
    try {
      await api.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
      });
      toast.success('Đổi mật khẩu thành công');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Lỗi đổi mật khẩu');
    } finally {
      setChangingPass(false);
    }
  };

  const filteredCategories = useMemo(() => {
    if (!skillSearch.trim()) return SKILL_CATEGORIES;
    const lowerSearch = skillSearch.toLowerCase();
    return SKILL_CATEGORIES.map(cat => ({
      ...cat,
      skills: cat.skills.filter(s => s.toLowerCase().includes(lowerSearch))
    })).filter(cat => cat.skills.length > 0);
  }, [skillSearch]);

  if (loading) {
    return <div className="flex items-center justify-center h-full">Đang tải dữ liệu...</div>;
  }

  const aiMetrics = user?.ai_metrics || {
    historical_quality_score: 0,
    on_time_rate: 0,
    capacity_hours_per_week: 40,
    current_workload_hours: 0
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
        <User className="text-blue-600" /> Hồ sơ Năng lực (AI Profile)
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Column: Avatar & AI Metrics */}
        <div className="col-span-1 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col items-center text-center">
            <div className="relative group mb-4">
              <div className="w-24 h-24 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-4xl font-bold overflow-hidden border-4 border-white shadow-sm">
                {avatar ? (
                  <img src={avatar} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  name ? name.charAt(0).toUpperCase() : 'U'
                )}
              </div>
              <label className="absolute inset-0 flex items-center justify-center bg-black/50 text-white rounded-full opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                <Camera size={24} />
                <input 
                  type="file" 
                  accept="image/*" 
                  className="hidden" 
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      if (file.size > 2 * 1024 * 1024) {
                        toast.error('Kích thước ảnh tối đa là 2MB');
                        return;
                      }
                      const reader = new FileReader();
                      reader.onloadend = () => {
                        setAvatar(reader.result as string);
                      };
                      reader.readAsDataURL(file);
                    }
                  }} 
                />
              </label>
            </div>
            <h2 className="text-xl font-bold text-gray-800">{name}</h2>
            <p className="text-gray-500 mb-4">{user?.role === 'admin' ? 'Quản trị viên (Admin)' : 'Cán bộ/Chuyên viên'}</p>
          </div>

          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl shadow-sm border border-indigo-100 p-6">
            <h3 className="text-md font-bold text-indigo-900 mb-4 flex items-center gap-2">
              <BrainCircuit size={20} /> Điểm Hiệu suất (AI)
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-indigo-700 flex items-center gap-1"><Star size={14}/> Điểm Chất lượng</span>
                  <span className="font-bold text-indigo-900">{aiMetrics.historical_quality_score}/100</span>
                </div>
                <div className="w-full bg-indigo-200 rounded-full h-2">
                  <div className="bg-indigo-600 h-2 rounded-full" style={{ width: `${aiMetrics.historical_quality_score}%` }}></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-indigo-700 flex items-center gap-1"><Target size={14}/> Tỷ lệ Đúng hạn</span>
                  <span className="font-bold text-indigo-900">{Math.round(aiMetrics.on_time_rate * 100)}%</span>
                </div>
                <div className="w-full bg-indigo-200 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${aiMetrics.on_time_rate * 100}%` }}></div>
                </div>
              </div>

              <div className="pt-4 border-t border-indigo-200/50">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-indigo-700 flex items-center gap-1"><Clock size={14}/> Tải công việc tuần</span>
                  <span className="font-bold text-indigo-900">{aiMetrics.current_workload_hours} / {aiMetrics.capacity_hours_per_week}h</span>
                </div>
                <div className="w-full bg-indigo-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${aiMetrics.current_workload_hours > aiMetrics.capacity_hours_per_week ? 'bg-red-500' : 'bg-amber-500'}`} 
                    style={{ width: `${Math.min((aiMetrics.current_workload_hours / aiMetrics.capacity_hours_per_week) * 100, 100)}%` }}>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Forms */}
        <div className="col-span-1 lg:col-span-3 space-y-6">
          <form onSubmit={handleUpdateProfile} className="space-y-6">
            
            {/* General Info */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Thông tin chung</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Họ và Tên</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <User size={16} className="text-gray-400" />
                    </div>
                    <input type="text" value={name} onChange={e => setName(e.target.value)} required className="pl-10 w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email công vụ</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Mail size={16} className="text-gray-400" />
                    </div>
                    <input type="email" value={email} onChange={e => setEmail(e.target.value)} required className="pl-10 w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none" />
                  </div>
                </div>
              </div>
            </div>

            {/* AI Bio Data */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2 flex items-center gap-2">
                <FileText size={20} className="text-blue-500" /> Kinh nghiệm thực tiễn (Bio cho AI)
              </h3>
              <p className="text-sm text-gray-500 mb-3">Phần này rất quan trọng. AI sẽ đọc văn bản này để hiểu sâu sắc về kinh nghiệm của bạn thay vì chỉ dựa vào Checkbox.</p>
              <textarea 
                rows={4}
                value={bio}
                onChange={e => setBio(e.target.value)}
                placeholder="Ví dụ: Đã có 5 năm kinh nghiệm làm công tác tiếp công dân tại UBND Huyện, am hiểu sâu sắc về Luật Đất đai và từng tham gia thẩm định 3 dự án giao thông trọng điểm..."
                className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 outline-none text-sm resize-none"
              ></textarea>
            </div>

            {/* Categorized Skill Matrix */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2 flex items-center gap-2">
                <Award size={20} className="text-amber-500" /> Bộ Kỹ năng Hành chính Nhà nước
              </h3>
              <p className="text-sm text-gray-500 mb-4">Lựa chọn các nghiệp vụ bạn có khả năng đảm nhận và tự đánh giá mức độ thành thạo (1-5).</p>
              
              {/* Selected Skills Badge Area */}
              {skills.length > 0 && (
                <div className="mb-6 p-4 bg-blue-50/50 rounded-xl border border-blue-100">
                  <h4 className="text-sm font-bold text-blue-800 mb-3">Đã chọn ({skills.length}):</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {skills.map((skill, idx) => (
                      <div key={idx} className="flex items-center justify-between bg-white p-2.5 rounded-lg border border-blue-200 shadow-sm">
                        <div className="font-medium text-gray-800 text-sm truncate mr-2 flex-1" title={skill.skill_name}>{skill.skill_name}</div>
                        <div className="flex items-center gap-3">
                          <input 
                            type="range" min="1" max="5" 
                            value={skill.self_rating} 
                            onChange={(e) => handleUpdateSkillRating(skill.skill_name, parseInt(e.target.value))}
                            className="w-20 accent-blue-600"
                          />
                          <span className="text-sm font-bold text-blue-600 w-4">{skill.self_rating}</span>
                          <button type="button" onClick={() => handleToggleSkill(skill.skill_name)} className="text-gray-400 hover:text-red-500">
                            <X size={16} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Filter & Search UI */}
              <div className="border border-gray-200 rounded-xl overflow-hidden flex flex-col md:flex-row">
                
                {/* Left: Search & Tabs */}
                <div className="w-full md:w-1/3 bg-gray-50 border-r border-gray-200 flex flex-col">
                  <div className="p-3 border-b border-gray-200 bg-white">
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search size={14} className="text-gray-400" />
                      </div>
                      <input 
                        type="text" 
                        placeholder="Tìm kiếm kỹ năng..." 
                        value={skillSearch}
                        onChange={e => setSkillSearch(e.target.value)}
                        className="pl-9 w-full bg-gray-100 border-none rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto max-h-[300px]">
                    {filteredCategories.map(cat => (
                      <button
                        key={cat.id}
                        type="button"
                        onClick={() => setActiveCategory(cat.id)}
                        className={`w-full text-left px-4 py-3 text-sm font-medium transition-colors border-l-4 ${activeCategory === cat.id ? 'bg-white border-blue-600 text-blue-700' : 'border-transparent text-gray-600 hover:bg-gray-100'}`}
                      >
                        {cat.name} <span className="text-xs text-gray-400 ml-1">({cat.skills.length})</span>
                      </button>
                    ))}
                    {filteredCategories.length === 0 && (
                      <div className="p-4 text-sm text-gray-500 text-center">Không tìm thấy nhóm nào</div>
                    )}
                  </div>
                </div>

                {/* Right: Checkboxes */}
                <div className="w-full md:w-2/3 bg-white p-4 max-h-[350px] overflow-y-auto">
                  {filteredCategories.find(c => c.id === activeCategory) ? (
                    <div className="space-y-2">
                      <h4 className="font-bold text-gray-800 mb-3">{filteredCategories.find(c => c.id === activeCategory)?.name}</h4>
                      {filteredCategories.find(c => c.id === activeCategory)?.skills.map(skillName => {
                        const isSelected = !!skills.find(s => s.skill_name === skillName);
                        return (
                          <label key={skillName} className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${isSelected ? 'bg-blue-50 border-blue-200' : 'border-gray-200 hover:bg-gray-50'}`}>
                            <input 
                              type="checkbox" 
                              checked={isSelected}
                              onChange={() => handleToggleSkill(skillName)}
                              className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                            />
                            <span className={`ml-3 text-sm ${isSelected ? 'font-medium text-blue-900' : 'text-gray-700'}`}>{skillName}</span>
                          </label>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center text-gray-400 text-sm">
                      Vui lòng chọn nhóm ở danh sách bên trái
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Work Preferences */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2 flex items-center gap-2">
                <TrendingUp size={20} className="text-purple-500" /> Nguyện vọng phát triển (Preferences)
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Lĩnh vực muốn học hỏi thêm</label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {preferences.interests.map(interest => (
                      <span key={interest} className="bg-purple-100 text-purple-700 px-2 py-1 rounded-md text-xs flex items-center gap-1">
                        {interest}
                        <button type="button" onClick={() => handleRemoveInterest(interest)}><X size={12} /></button>
                      </span>
                    ))}
                  </div>
                  <input 
                    type="text" value={newInterest} onChange={e => setNewInterest(e.target.value)} onKeyDown={handleAddInterest}
                    placeholder="VD: Sử dụng phần mềm dự toán (Enter)" 
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 outline-none text-sm focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Giới hạn Công việc đồng thời</label>
                  <p className="text-xs text-gray-500 mb-2">AI sẽ hạn chế giao việc vượt quá ngưỡng này.</p>
                  <input 
                    type="number" min="1" max="10"
                    value={preferences.max_concurrent_tasks} 
                    onChange={e => setPreferences({...preferences, max_concurrent_tasks: parseInt(e.target.value)})}
                    className="w-24 border border-gray-300 rounded-lg px-3 py-2 outline-none text-sm focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button type="submit" disabled={saving} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium flex items-center gap-2 transition-colors disabled:opacity-50">
                <Save size={18} /> {saving ? 'Đang lưu...' : 'Lưu Hồ sơ & Cập nhật AI'}
              </button>
            </div>
          </form>

          {/* Password Update Form */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2 flex items-center gap-2">
              <Shield size={20} className="text-emerald-500" /> Đổi Mật khẩu
            </h3>
            
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu hiện tại</label>
                <input type="password" value={oldPassword} onChange={e => setOldPassword(e.target.value)} required className="w-full border border-gray-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu mới</label>
                  <input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required className="w-full border border-gray-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Xác nhận mật khẩu mới</label>
                  <input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required className="w-full border border-gray-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500" />
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button type="submit" disabled={changingPass} className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors disabled:opacity-50">
                  <Save size={18} /> {changingPass ? 'Đang đổi...' : 'Đổi Mật khẩu'}
                </button>
              </div>
            </form>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Profile;
