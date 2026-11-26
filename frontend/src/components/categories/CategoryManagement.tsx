import { useState, useEffect } from "react";
import { Form, Button, Input, Select, Modal, Tree, Tag, Space, Divider, Tooltip, Popconfirm, message } from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EnterOutlined,
} from "@ant-design/icons";
import { graphqlRequestWithAuth } from "@/utils/graphqlClient";
import { useCategoryStore } from "@/store/categoryStore";
import { CREATE_CATEGORY_MUTATION, UPDATE_CATEGORY_MUTATION, DELETE_CATEGORY_MUTATION } from "@/graphql/operations";


interface Category {
  id: string;
  name: string;
  color?: string;
  icon?: string;
  parentId?: string;
  isSystem: boolean;
  sortOrder: number;
  children?: Category[];
}

interface CategoryFormData {
  name: string;
  color?: string;
  icon?: string;
  parentId?: string;
}

const DEFAULT_COLORS = [
  "#6366F1", "#8B5CF6", "#EC4899", "#EF4444",
  "#F97316", "#F59E0B", "#EAB308", "#84CC16",
  "#22C55E", "#10B981", "#14B8A6", "#06B6D4",
  "#0EA5E9", "#3B82F6", "#64748B", "#78716C",
];

export function CategoryManagement() {
  const { categories, fetchCategories } = useCategoryStore();
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [form] = Form.useForm<CategoryFormData>();
  const [loading, setLoading] = useState(false);
  const [treeExpandedKeys, setTreeExpandedKeys] = useState<string[]>([]);

  // Load categories on mount
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  const handleCreate = () => {
    setIsEditing(false);
    form.resetFields();
    form.setFieldsValue({ parentId: undefined });
    setSelectedCategory(null);
    setModalOpen(true);
  };

  const handleEdit = (category: Category) => {
    setIsEditing(true);
    setSelectedCategory(category);
    form.setFieldsValue({
      name: category.name,
      color: category.color || DEFAULT_COLORS[0],
      icon: category.icon || "",
      parentId: category.parentId,
    });
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedCategory(null);
    setIsEditing(false);
    form.resetFields();
  };

  const handleSubmit = async (values: CategoryFormData) => {
    setLoading(true);
    try {
      if (isEditing && selectedCategory) {
        await graphqlRequestWithAuth<{ updateCategory: Category }>(
          UPDATE_CATEGORY_MUTATION,
          { id: selectedCategory.id, input: values }
        );
        message.success("Category updated");
      } else {
        await graphqlRequestWithAuth<{ createCategory: Category }>(
          CREATE_CATEGORY_MUTATION,
          { input: values }
        );
        message.success("Category created");
      }
      handleCloseModal();
      fetchCategories();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "Failed to save category");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (category: Category) => {
    try {
      await graphqlRequestWithAuth(DELETE_CATEGORY_MUTATION, { id: category.id });
      message.success("Category deleted");
      fetchCategories();
    } catch (error) {
      message.error(error instanceof Error ? error.message : "Failed to delete category");
    }
  };

  const renderTreeNode = (data: Category) => {
    const isSystem = data.isSystem;
    return (
      <Space>
        <Tag color={data.color || DEFAULT_COLORS[0]} style={{ fontWeight: 500 }}>
          {data.name}
        </Tag>
        {!isSystem && (
          <Space size={4}>
            <Tooltip title="Edit">
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleEdit(data)}
              />
            </Tooltip>
            <Popconfirm
              title="Delete category?"
              description="This will also delete all subcategories. Events in this category will be uncategorized."
              onConfirm={() => handleDelete(data)}
              okText="Delete"
              okType="danger"
            >
              <Tooltip title="Delete">
                <Button type="text" size="small" danger icon={<DeleteOutlined />} />
              </Tooltip>
            </Popconfirm>
            <Tooltip title="Add Subcategory">
              <Button
                type="text"
                size="small"
                icon={<PlusOutlined />}
                onClick={() => {
                  form.setFieldsValue({ parentId: data.id });
                  setIsEditing(false);
                  setSelectedCategory(null);
                  setModalOpen(true);
                }}
              />
            </Tooltip>
          </Space>
        )}
        {isSystem && <Tooltip title="System category (cannot be modified)"><EnterOutlined /></Tooltip>}
      </Space>
    );
  };

  const treeData = categories.map(cat => ({
    key: cat.id,
    title: renderTreeNode(cat),
    children: cat.children?.map(child => ({
      key: child.id,
      title: renderTreeNode(child),
      children: child.children?.map(grandchild => ({
        key: grandchild.id,
        title: renderTreeNode(grandchild),
      })),
    })),
  }));

  const availableParents = categories.flatMap(c => [
    { value: c.id, label: c.name, disabled: !!c.children.length },
    ...c.children.map(sc => ({ value: sc.id, label: `  └ ${sc.name}` })),
    ...c.children.flatMap(sc => sc.children?.map(gc => ({ value: gc.id, label: `    └ ${gc.name}` })) || []),
  ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
          Category Management
        </h3>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Add Category
        </Button>
      </div>

      <p className="text-[var(--color-text-secondary)]">
        Organize your events with custom categories. Drag to reorder, click to edit.
      </p>

      <Divider />

      <div className="space-y-4">
        <Tree
          showLine
          blockNode
          draggable
          defaultExpandAll
          treeData={treeData}
          expandedKeys={treeExpandedKeys}
          onExpand={(keys: any) => setTreeExpandedKeys(keys)}
          onDragEnd={async () => {
            // This is a simplified approach - in reality you'd need to track the tree changes
            // and send the reorder mutation. The Ant Design Tree doesn't easily expose
            // the new tree structure after drag. You might want to use a different approach.
          }}
        />
      </div>

      {/* Create/Edit Modal */}
      <Modal
        open={modalOpen}
        onCancel={handleCloseModal}
        title={isEditing ? 'Edit Category' : 'Create Category'}
        width={520}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit} className="space-y-4 p-4">
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: 'Name is required' }]}
          >
            <Input placeholder="Category name" />
          </Form.Item>

          <Form.Item name="color" label="Color">
            <div className="space-y-2">
              <Select
                placeholder="Select color"
                style={{ width: "100%" }}
                showSearch
                options={DEFAULT_COLORS.map(c => ({ value: c, label: c }))}
                dropdownRender={() => (
                  <div style={{ padding: 8 }}>
                    {DEFAULT_COLORS.map(color => (
                      <div
                        key={color}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                          padding: "8px 12px",
                          borderRadius: 6,
                          cursor: "pointer",
                          background: "transparent",
                          transition: "background 0.2s",
                        }}
                        onMouseEnter={e => { e.currentTarget.style.background = "var(--color-bg-hover)" }}
                        onMouseLeave={e => { e.currentTarget.style.background = "transparent" }}
                        onClick={() => form.setFieldsValue({ color: color })}
                      >
                        <div style={{ width: 20, height: 20, borderRadius: 4, background: color }} />
                        <span>{color}</span>
                      </div>
                    ))}
                  </div>
                )}
              />
            </div>
          </Form.Item>

          <Form.Item name="icon" label="Icon (emoji)">
            <Input placeholder="🎯" maxLength={2} />
          </Form.Item>

          <Form.Item name="parentId" label="Parent Category">
            <Select
              placeholder="Select parent (optional)"
              style={{ width: "100%" }}
              showSearch
              options={[
                { value: "", label: "— No Parent (Top Level) —" },
                ...availableParents,
              ]}
            />
          </Form.Item>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="text" onClick={handleCloseModal}>
              Cancel
            </Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              {isEditing ? 'Save Changes' : 'Create Category'}
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
}