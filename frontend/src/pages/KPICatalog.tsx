import { useState, useEffect } from 'react';
import { kpiApi } from '../lib/kpi-api';
import type { KPICatalogItem, KPICatalog } from '../lib/kpi-api';
import { Plus, Save, Check, Trash2, Target } from 'lucide-react';
import api from '../lib/api';
import { COMPLEXITY_GROUP_LABELS } from '../lib/kpi-api';

const KPICatalogPage = () => {
  const [catalogs, setCatalogs] = useState<KPICatalog[]>([]);
  const [loading, setLoading] = useState(true);
  const [userRole, setUserRole] = useState('staff');
  const [departmentId, setDepartmentId] = useState('');
  
  const [isEditing, setIsEditing] = useState(false);
  const [currentCatalog, setCurrentCatalog] = useState<Partial<KPICatalog>>({
    name: `Danh mục KPI ${new Date().getFullYear()}`,
    period_year: new Date().getFullYear(),
    items: []
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const meRes = await api.get('/auth/me');
      setUserRole(meRes.data.role);
      setDepartmentId(meRes.data.department_id);

      const catalogsRes = await kpiApi.getCatalogs({ department_id: meRes.data.department_id });
      setCatalogs(catalogsRes);
    } catch (error) {
      console.error('Failed to fetch KPI catalogs', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = () => {
    const newItem: KPICatalogItem = {
      id: Math.random().toString(36).substring(7),
      task_name: '',
      category: 'Chuyên môn',
      complexity_group: 2,
      kpi_point: 50
    };
    setCurrentCatalog({
      ...currentCatalog,
      items: [...(currentCatalog.items || []), newItem]
    });
  };

  const handleUpdateItem = (index: number, field: keyof KPICatalogItem, value: any) => {
    const newItems = [...(currentCatalog.items || [])];
    newItems[index] = { ...newItems[index], [field]: value };
    setCurrentCatalog({ ...currentCatalog, items: newItems });
  };

  const handleRemoveItem = (index: number) => {
    const newItems = [...(currentCatalog.items || [])];
    newItems.splice(index, 1);
    setCurrentCatalog({ ...currentCatalog, items: newItems });
  };

  const handleSave = async () => {
    try {
      if (!currentCatalog.department_id) {
        currentCatalog.department_id = departmentId;
      }
      await kpiApi.createCatalog(currentCatalog);
      setIsEditing(false);
      fetchData();
    } catch (error) {
      console.error('Failed to save catalog', error);
      alert('Có lỗi xảy ra khi lưu danh mục');
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await kpiApi.approveCatalog(id);
      fetchData();
    } catch (error) {
      console.error('Failed to approve catalog', error);
      alert('Có lỗi xảy ra khi phê duyệt');
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>;
  }

  const canEdit = userRole === 'director' || userRole === 'admin';

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Danh mục Nhiệm vụ & Điểm KPI</h1>
        {canEdit && !isEditing && (
          <button 
            onClick={() => setIsEditing(true)}
            className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            <Plus className="h-5 w-5 mr-2" />
            Tạo danh mục mới
          </button>
        )}
      </div>

      {isEditing ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <h2 className="text-lg font-bold text-gray-800">Tạo/Sửa Danh mục</h2>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tên danh mục</label>
                <input 
                  type="text" 
                  value={currentCatalog.name}
                  onChange={(e) => setCurrentCatalog({...currentCatalog, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Năm áp dụng</label>
                <input 
                  type="number" 
                  value={currentCatalog.period_year}
                  onChange={(e) => setCurrentCatalog({...currentCatalog, period_year: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>
          
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-gray-800">Danh sách nhiệm vụ ({currentCatalog.items?.length || 0})</h3>
              <button 
                onClick={handleAddItem}
                className="flex items-center text-sm px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100"
              >
                <Plus className="h-4 w-4 mr-1" /> Thêm nhiệm vụ
              </button>
            </div>
            
            <div className="space-y-4">
              {currentCatalog.items?.map((item, index) => (
                <div key={item.id || index} className="grid grid-cols-12 gap-4 items-start p-4 border border-gray-100 bg-gray-50 rounded-lg">
                  <div className="col-span-5">
                    <label className="block text-xs text-gray-500 mb-1">Tên nhiệm vụ</label>
                    <input 
                      type="text" 
                      value={item.task_name}
                      onChange={(e) => handleUpdateItem(index, 'task_name', e.target.value)}
                      placeholder="VD: Tham mưu xây dựng văn bản..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                  <div className="col-span-3">
                    <label className="block text-xs text-gray-500 mb-1">Mảng/Lĩnh vực</label>
                    <input 
                      type="text" 
                      value={item.category}
                      onChange={(e) => handleUpdateItem(index, 'category', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-xs text-gray-500 mb-1">Nhóm điểm (thang 100)</label>
                    <select
                      value={item.complexity_group}
                      onChange={(e) => handleUpdateItem(index, 'complexity_group', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm"
                    >
                      {([1, 2, 3] as const).map(g => (
                        <option key={g} value={g}>{COMPLEXITY_GROUP_LABELS[g]}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-1">
                    <label className="block text-xs text-gray-500 mb-1">Điểm KPI</label>
                    <input 
                      type="number" 
                      value={item.kpi_point}
                      onChange={(e) => handleUpdateItem(index, 'kpi_point', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm"
                    />
                  </div>
                  <div className="col-span-1 pt-6 text-right">
                    <button 
                      onClick={() => handleRemoveItem(index)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
              
              {(!currentCatalog.items || currentCatalog.items.length === 0) && (
                <div className="text-center py-8 text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
                  Chưa có nhiệm vụ nào. Nhấn "Thêm nhiệm vụ" để bắt đầu.
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-end space-x-3">
              <button 
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                Hủy
              </button>
              <button 
                onClick={handleSave}
                className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
              >
                <Save className="h-4 w-4 mr-2" /> Lưu danh mục
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {catalogs.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                <Target className="h-8 w-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Chưa có danh mục KPI nào</h3>
              <p className="text-gray-500 mb-6">Đơn vị của bạn chưa thiết lập danh mục điểm số KPI cho các nhiệm vụ.</p>
              {canEdit && (
                <button 
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Tạo danh mục đầu tiên
                </button>
              )}
            </div>
          ) : (
            catalogs.map(catalog => (
              <div key={catalog.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                  <div>
                    <h2 className="text-lg font-bold text-gray-800">{catalog.name}</h2>
                    <p className="text-sm text-gray-500">Năm áp dụng: {catalog.period_year} • Trạng thái: 
                      <span className={`ml-1 font-medium ${catalog.status === 'approved' ? 'text-green-600' : 'text-amber-500'}`}>
                        {catalog.status === 'approved' ? 'Đã duyệt' : 'Bản nháp'}
                      </span>
                    </p>
                  </div>
                  <div>
                    {catalog.status === 'draft' && canEdit && (
                      <button 
                        onClick={() => handleApprove(catalog.id)}
                        className="flex items-center px-3 py-1.5 bg-green-50 text-green-700 rounded hover:bg-green-100 transition-colors"
                      >
                        <Check className="h-4 w-4 mr-1" /> Phê duyệt
                      </button>
                    )}
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-white border-b border-gray-100">
                        <th className="p-4 font-medium text-gray-500 text-sm">Nhiệm vụ</th>
                        <th className="p-4 font-medium text-gray-500 text-sm">Lĩnh vực</th>
                        <th className="p-4 font-medium text-gray-500 text-sm text-center">Độ khó</th>
                        <th className="p-4 font-medium text-gray-500 text-sm text-center">Điểm KPI</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {catalog.items.map((item) => (
                        <tr key={item.id} className="hover:bg-gray-50">
                          <td className="p-4 text-sm text-gray-800">{item.task_name}</td>
                          <td className="p-4 text-sm text-gray-500">{item.category}</td>
                          <td className="p-4 text-sm text-gray-800 text-center">
                            <span className={`px-2 py-1 rounded text-xs ${
                              item.complexity_group === 1 ? 'bg-green-100 text-green-700' :
                              item.complexity_group === 2 ? 'bg-blue-100 text-blue-700' :
                              'bg-purple-100 text-purple-700'
                            }`}>
                              {COMPLEXITY_GROUP_LABELS[item.complexity_group] ?? `Nhóm ${item.complexity_group}`}
                            </span>
                          </td>
                          <td className="p-4 text-sm font-semibold text-indigo-600 text-center">{item.kpi_point} đ</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default KPICatalogPage;
