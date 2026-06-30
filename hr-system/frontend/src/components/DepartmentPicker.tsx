/** 部门选择器 — 树形下拉 */
import { useState, useEffect } from 'react';
import { TreeSelect } from 'antd';
import { ApartmentOutlined } from '@ant-design/icons';
import { departmentAPI } from '../services/api';

interface DeptNode {
  value: number;
  title: string;
  children?: DeptNode[];
}

interface Props {
  value?: number | number[];
  onChange?: (v: number | number[]) => void;
  multiple?: boolean;
  placeholder?: string;
  style?: React.CSSProperties;
}

export default function DepartmentPicker({ value, onChange, multiple, placeholder = '选择部门', style }: Props) {
  const [treeData, setTreeData] = useState<DeptNode[]>([]);

  useEffect(() => {
    departmentAPI.list().then((res) => {
      const buildTree = (items: any[], parentId: number | null = null): DeptNode[] =>
        items
          .filter((d: any) => d.parent_id === parentId)
          .map((d: any) => ({
            value: d.id,
            title: `${d.name} (${d.employee_count || 0}人)`,
            children: buildTree(items, d.id),
          }));
      setTreeData(buildTree(res.data || []));
    }).catch(() => {});
  }, []);

  return (
    <TreeSelect
      treeData={treeData}
      value={value}
      onChange={onChange}
      multiple={multiple}
      placeholder={placeholder}
      treeDefaultExpandAll
      allowClear
      showSearch
      treeNodeFilterProp="title"
      style={style}
    />
  );
}
