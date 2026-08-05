import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Network, ChevronRight, ChevronDown, Building2, Users, Shield,
  AlertTriangle, Lock,
} from 'lucide-react';
import { taskApi, DEPT_LEVEL_LABELS, WORKLOAD_LABELS, WORKLOAD_BAR, CLEARANCE_LABELS } from '../lib/task-api';
import type { DepartmentNode, DepartmentMember } from '../lib/task-api';
import { KPI_GROUP_LABELS, KPI_GROUP_COLORS, ROLE_LABELS } from '../lib/kpi-api';

/** Đệ quy: tìm một nút trong cây theo id */
function findNode(nodes: DepartmentNode[], id: string): DepartmentNode | null {
  for (const n of nodes) {
    if (n._id === id) return n;
    const hit = findNode(n.children, id);
    if (hit) return hit;
  }
  return null;
}

/** Đệ quy: thu thập id của mọi nút để mở toàn bộ cây */
function allIds(nodes: DepartmentNode[]): string[] {
  return nodes.flatMap(n => [n._id, ...allIds(n.children)]);
}

const LEVEL_ICON_COLOR: Record<string, string> = {
  bo: 'text-gold-500',
  cuc: 'text-navy-500',
  phong: 'text-navy-400',
  doi: 'text-navy-300',
};

const Organization = () => {
  const [tree, setTree] = useState<DepartmentNode[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState<string>('');
  const [members, setMembers] = useState<DepartmentMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMembers, setLoadingMembers] = useState(false);

  const now = new Date();

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      setLoading(true);
      const data = await taskApi.departmentTree();
      setTree(data);
      setExpanded(new Set(allIds(data)));
      // Chọn sẵn đơn vị cơ sở đầu tiên có cán bộ
      const firstWithMembers = allIds(data)
        .map(id => findNode(data, id)!)
        .find(n => n.member_count > 0);
      if (firstWithMembers) selectDept(firstWithMembers._id);
    } catch (error) {
      console.error('Không tải được cơ cấu tổ chức', error);
    } finally {
      setLoading(false);
    }
  };

  const selectDept = async (id: string) => {
    setSelectedId(id);
    setLoadingMembers(true);
    try {
      setMembers(await taskApi.departmentMembers(id));
    } catch (error) {
      console.error('Không tải được danh sách cán bộ', error);
      setMembers([]);
    } finally {
      setLoadingMembers(false);
    }
  };

  const toggle = (id: string) => {
    const next = new Set(expanded);
    next.has(id) ? next.delete(id) : next.add(id);
    setExpanded(next);
  };

  const selected = selectedId ? findNode(tree, selectedId) : null;

  const renderNode = (node: DepartmentNode, depth = 0) => {
    const hasChildren = node.children.length > 0;
    const isOpen = expanded.has(node._id);
    const isSelected = node._id === selectedId;

    return (
      <div key={node._id}>
        <div
          onClick={() => selectDept(node._id)}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          className={`flex items-start gap-1.5 py-2 pr-2 cursor-pointer border-l-2 text-sm transition-colors ${
            isSelected
              ? 'bg-navy-50 border-navy-600 text-navy-900 font-medium'
              : 'border-transparent text-navy-700 hover:bg-navy-50/60'
          }`}
        >
          <button
            onClick={e => { e.stopPropagation(); if (hasChildren) toggle(node._id); }}
            className={`shrink-0 mt-0.5 ${hasChildren ? 'text-navy-400' : 'invisible'}`}
          >
            {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
          <Building2 size={14} className={`shrink-0 mt-0.5 ${LEVEL_ICON_COLOR[node.level] ?? 'text-navy-400'}`} />
          <div className="flex-1 min-w-0">
            {/* Tên đầy đủ của đơn vị, xuống dòng thay vì cắt bớt */}
            <p className="leading-snug">{node.name}</p>
            <p className="text-[10px] text-navy-400 mt-0.5">
              {DEPT_LEVEL_LABELS[node.level]}
              {node.total_member_count > 0 && ` · ${node.total_member_count} cán bộ`}
            </p>
          </div>
        </div>
        {isOpen && node.children.map(c => renderNode(c, depth + 1))}
      </div>
    );
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-navy-600" /></div>;
  }

  const stats = selected?.group_stats ?? { group_1: 0, group_2: 0, group_3: 0 };
  const statTotal = stats.group_1 + stats.group_2 + stats.group_3;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-navy-900 flex items-center gap-2">
          <Network className="h-5 w-5 text-navy-600" /> Cơ cấu tổ chức
        </h1>
        <p className="text-xs text-navy-500 mt-0.5">
          Đơn vị các cấp và tình hình thực hiện nhiệm vụ của cán bộ thuộc quyền.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-4">
        {/* Cây đơn vị */}
        <div className="bg-white border border-navy-200 rounded-sm overflow-hidden self-start">
          <div className="px-3 py-2 border-b border-navy-200 bg-navy-50">
            <p className="section-label">Danh sách đơn vị</p>
          </div>
          <div className="py-1 max-h-[70vh] overflow-y-auto custom-scrollbar">
            {tree.map(n => renderNode(n))}
          </div>
        </div>

        {/* Chi tiết đơn vị */}
        <div className="space-y-4 min-w-0">
          {!selected ? (
            <div className="bg-white border border-navy-200 rounded-sm p-12 text-center text-navy-400 text-sm">
              Chọn một đơn vị để xem chi tiết.
            </div>
          ) : (
            <>
              <div className="bg-white border border-navy-200 rounded-sm">
                <div className="px-4 py-3 border-b border-navy-200 bg-navy-700 text-white">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h2 className="font-semibold leading-snug">{selected.name}</h2>
                      <p className="text-[11px] text-navy-200 mt-0.5">
                        {DEPT_LEVEL_LABELS[selected.level]}
                        {selected.force_system && ` · Hệ lực lượng ${selected.force_system}`}
                      </p>
                    </div>
                    {selected.short_name && (
                      <div className="shrink-0 text-right">
                        <p className="text-[9px] text-navy-300 uppercase tracking-wide">Mã đơn vị</p>
                        <span className="inline-block px-2 py-0.5 bg-navy-800 text-gold-300 text-xs font-mono rounded-sm mt-0.5">
                          {selected.short_name}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 divide-x divide-navy-100 border-b border-navy-100">
                  <div className="p-3">
                    <p className="section-label">Cán bộ</p>
                    <p className="text-2xl font-bold text-navy-900 tabular mt-0.5">
                      {selected.total_member_count}
                    </p>
                    {selected.children.length > 0 && (
                      <p className="text-[10px] text-navy-400">gồm đơn vị cấp dưới</p>
                    )}
                  </div>
                  <div className="p-3">
                    <p className="section-label">KPI tập thể</p>
                    <p className="text-2xl font-bold text-navy-700 tabular mt-0.5">
                      {selected.collective_kpi != null ? selected.collective_kpi.toFixed(1) : '–'}
                    </p>
                    {selected.collective_kpi_group && (
                      <span className={`inline-block mt-1 px-1.5 py-0.5 text-[10px] rounded-sm border ${KPI_GROUP_COLORS[selected.collective_kpi_group] ?? ''}`}>
                        {KPI_GROUP_LABELS[selected.collective_kpi_group]}
                      </span>
                    )}
                  </div>
                  <div className="p-3">
                    <p className="section-label">Đơn vị trực thuộc</p>
                    <p className="text-2xl font-bold text-navy-900 tabular mt-0.5">
                      {selected.children.length}
                    </p>
                  </div>
                  <div className="p-3">
                    <p className="section-label">Phân bố xếp loại</p>
                    {statTotal === 0 ? (
                      <p className="text-sm text-navy-400 mt-1">Chưa có</p>
                    ) : (
                      <>
                        <div className="flex h-2 rounded-sm overflow-hidden mt-2 bg-navy-100">
                          <div className="bg-emerald-500" style={{ width: `${stats.group_1 / statTotal * 100}%` }} />
                          <div className="bg-navy-500" style={{ width: `${stats.group_2 / statTotal * 100}%` }} />
                          <div className="bg-crimson-600" style={{ width: `${stats.group_3 / statTotal * 100}%` }} />
                        </div>
                        <p className="text-[10px] text-navy-500 mt-1 tabular">
                          N1 {stats.group_1} · N2 {stats.group_2} · N3 {stats.group_3}
                        </p>
                      </>
                    )}
                  </div>
                </div>

                {selected.description && (
                  <p className="px-4 py-2 text-xs text-navy-600 bg-navy-50/50">{selected.description}</p>
                )}
              </div>

              {/* Cán bộ thuộc đơn vị */}
              <div className="bg-white border border-navy-200 rounded-sm overflow-hidden">
                <div className="px-4 py-2 border-b border-navy-200 bg-navy-50 flex items-center justify-between">
                  <p className="section-label flex items-center gap-1.5">
                    <Users size={13} /> Cán bộ thuộc đơn vị
                  </p>
                  <span className="text-xs text-navy-500 tabular">{members.length} người</span>
                </div>

                {loadingMembers ? (
                  <div className="p-10 flex justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-navy-600" />
                  </div>
                ) : members.length === 0 ? (
                  <p className="p-10 text-center text-sm text-navy-400">
                    Đơn vị này không có cán bộ trực thuộc trực tiếp.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm border-collapse">
                      <thead>
                        <tr className="bg-white border-b border-navy-200 text-navy-500 text-xs">
                          <th className="text-left px-4 py-2 font-medium">Cán bộ</th>
                          <th className="text-left px-3 py-2 font-medium">Tiếp cận</th>
                          <th className="text-left px-3 py-2 font-medium w-44">Tải việc</th>
                          <th className="text-center px-3 py-2 font-medium">NV giao</th>
                          <th className="text-center px-3 py-2 font-medium">Hoàn thành</th>
                          <th className="text-center px-3 py-2 font-medium">Quá hạn</th>
                          <th className="text-center px-3 py-2 font-medium">KPI</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-navy-100">
                        {members.map(m => (
                          <tr key={m.id} className="hover:bg-navy-50/50">
                            <td className="px-4 py-2">
                              <Link to={`/employees/${m.id}`} className="group">
                                <p className="font-medium text-navy-800 group-hover:text-navy-600 group-hover:underline">
                                  {m.name}
                                </p>
                                <p className="text-[11px] text-navy-500">
                                  {[m.rank, m.position].filter(Boolean).join(' · ') || ROLE_LABELS[m.role]}
                                </p>
                              </Link>
                            </td>
                            <td className="px-3 py-2">
                              <span className="inline-flex items-center gap-1 text-[11px] text-navy-600">
                                <Shield size={11} className={m.clearance_level > 0 ? 'text-gold-500' : 'text-navy-300'} />
                                {CLEARANCE_LABELS[m.clearance_level]}
                              </span>
                              {m.classified_tasks > 0 && (
                                <span className="ml-1 inline-flex items-center gap-0.5 text-[10px] text-crimson-700">
                                  <Lock size={9} />{m.classified_tasks}
                                </span>
                              )}
                            </td>
                            <td className="px-3 py-2">
                              <div className="flex items-center gap-2">
                                <div className="flex-1 h-1.5 bg-navy-100 rounded-sm overflow-hidden min-w-16">
                                  <div
                                    className={`h-full ${WORKLOAD_BAR[m.workload_status]}`}
                                    style={{ width: `${Math.min(m.workload_percent, 100)}%` }}
                                  />
                                </div>
                                <span className="text-[11px] text-navy-600 tabular w-11 text-right">
                                  {m.workload_percent.toFixed(0)}%
                                </span>
                              </div>
                              <p className="text-[10px] text-navy-400 mt-0.5">
                                {WORKLOAD_LABELS[m.workload_status]}
                              </p>
                            </td>
                            <td className="px-3 py-2 text-center tabular text-navy-700">{m.tasks_assigned}</td>
                            <td className="px-3 py-2 text-center tabular text-emerald-700 font-medium">{m.tasks_completed}</td>
                            <td className="px-3 py-2 text-center tabular">
                              {m.tasks_overdue > 0 ? (
                                <span className="inline-flex items-center gap-1 text-crimson-700 font-medium">
                                  <AlertTriangle size={12} />{m.tasks_overdue}
                                </span>
                              ) : (
                                <span className="text-navy-300">0</span>
                              )}
                            </td>
                            <td className="px-3 py-2 text-center">
                              {m.latest_kpi != null ? (
                                <>
                                  <p className="font-bold text-navy-800 tabular">{m.latest_kpi.toFixed(1)}</p>
                                  {m.latest_kpi_group && (
                                    <span className={`inline-block px-1 py-0.5 text-[9px] rounded-sm border ${KPI_GROUP_COLORS[m.latest_kpi_group] ?? ''}`}>
                                      {m.latest_kpi_group === 'group_1' ? 'N1' : m.latest_kpi_group === 'group_2' ? 'N2' : 'N3'}
                                    </span>
                                  )}
                                </>
                              ) : <span className="text-navy-300">–</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      <p className="text-[11px] text-navy-400">
        Tải việc = tổng điểm nhiệm vụ chưa hoàn thành / định mức điểm của cán bộ trong kỳ
        tháng {now.getMonth() + 1}/{now.getFullYear()}.
      </p>
    </div>
  );
};

export default Organization;
