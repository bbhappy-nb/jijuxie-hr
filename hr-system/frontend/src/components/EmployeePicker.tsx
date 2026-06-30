/** 员工选择器 — 可搜索下拉 */
import { useState, useCallback } from 'react';
import { Select, Space } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { employeeAPI } from '../services/api';

interface Props {
  value?: number | number[];
  onChange?: (v: number | number[]) => void;
  multiple?: boolean;
  placeholder?: string;
  style?: React.CSSProperties;
}

export default function EmployeePicker({ value, onChange, multiple, placeholder = '选择员工', style }: Props) {
  const [options, setOptions] = useState<{ value: number; label: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = useCallback(async (keyword: string) => {
    if (!keyword || keyword.length < 1) { setOptions([]); return; }
    setLoading(true);
    try {
      const res = await employeeAPI.list({ keyword, page_size: 50 });
      const items = (res.data?.items || []).map((e: any) => ({
        value: e.id,
        label: `${e.name} (${e.employee_no}) — ${e.department_name || ''}`,
      }));
      setOptions(items);
    } catch { setOptions([]); }
    finally { setLoading(false); }
  }, []);

  return (
    <Select
      showSearch
      value={value}
      onChange={onChange}
      mode={multiple ? 'multiple' : undefined}
      placeholder={placeholder}
      filterOption={false}
      onSearch={handleSearch}
      onFocus={() => handleSearch('')}
      options={options}
      loading={loading}
      allowClear
      style={style}
    />
  );
}
