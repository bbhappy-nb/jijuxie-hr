/** 绩效方案选择器 */
import { useState, useEffect } from 'react';
import { Select } from 'antd';
import { TrophyOutlined } from '@ant-design/icons';
import { performanceAPI } from '../services/api';

interface Props {
  value?: number;
  onChange?: (v: number) => void;
  placeholder?: string;
  style?: React.CSSProperties;
}

export default function PlanPicker({ value, onChange, placeholder = '选择考核方案', style }: Props) {
  const [options, setOptions] = useState<{ value: number; label: string }[]>([]);

  useEffect(() => {
    performanceAPI.listPlans({ page_size: 100 }).then((res) => {
      const items = (res.data?.items || []).map((p: any) => ({
        value: p.id,
        label: `${p.name} (${p.period} / ${p.year})`,
      }));
      setOptions(items);
    }).catch(() => {});
  }, []);

  return (
    <Select
      showSearch
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      optionFilterProp="label"
      options={options}
      allowClear
      style={style}
    />
  );
}
