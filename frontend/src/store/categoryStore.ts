import { create } from 'zustand';
import { graphqlRequestWithAuth } from '@/utils/graphqlClient';

interface Category {
  id: string;
  userId: string;
  parentId?: string;
  name: string;
  description?: string;
  color: string;
  icon?: string;
  isSystem: boolean;
  sortOrder: number;
  defaultReminderMinutes: number[];
  children: Category[];
  createdAt: string;
  updatedAt: string;
}

interface CategoryState {
  categories: Category[];
  flatCategories: Category[];
  isLoading: boolean;

  fetchCategories: () => Promise<void>;
  createCategory: (input: any) => Promise<Category>;
  updateCategory: (id: string, input: any) => Promise<Category>;
  deleteCategory: (id: string) => Promise<void>;
  reorderCategories: (ids: string[]) => Promise<Category[]>;
}

const CATEGORIES_QUERY = `
  query Categories {
    categories {
      categories {
        id
        userId
        parentId
        name
        description
        color
        icon
        isSystem
        sortOrder
        defaultReminderMinutes
        children {
          id
          userId
          parentId
          name
          description
          color
          icon
          isSystem
          sortOrder
          defaultReminderMinutes
          children {
            id
            name
          }
          createdAt
          updatedAt
        }
        createdAt
        updatedAt
      }
      flatList {
        id
        userId
        parentId
        name
        description
        color
        icon
        isSystem
        sortOrder
        defaultReminderMinutes
        children {
          id
          name
        }
        createdAt
        updatedAt
      }
    }
  }
`;

const CREATE_CATEGORY_MUTATION = `
  mutation CreateCategory($input: CreateCategoryInput!) {
    createCategory(input: $input) {
      id
      userId
      parentId
      name
      description
      color
      icon
      isSystem
      sortOrder
      defaultReminderMinutes
      children { id name }
      createdAt
      updatedAt
    }
  }
`;

const UPDATE_CATEGORY_MUTATION = `
  mutation UpdateCategory($id: UUID!, $input: UpdateCategoryInput!) {
    updateCategory(id: $id, input: $input) {
      id
      userId
      parentId
      name
      description
      color
      icon
      isSystem
      sortOrder
      defaultReminderMinutes
      children { id name }
      createdAt
      updatedAt
    }
  }
`;

const DELETE_CATEGORY_MUTATION = `
  mutation DeleteCategory($id: UUID!) {
    deleteCategory(id: $id)
  }
`;

const REORDER_CATEGORIES_MUTATION = `
  mutation ReorderCategories($categoryIds: [UUID!]!) {
    reorderCategories(categoryIds: $categoryIds) {
      id
      sortOrder
    }
  }
`;

function flattenCategories(categories: Category[]): Category[] {
  const result: Category[] = [];
  function traverse(cats: Category[]) {
    cats.forEach(cat => {
      result.push(cat);
      if (cat.children.length > 0) {
        traverse(cat.children);
      }
    });
  }
  traverse(categories);
  return result;
}

export const useCategoryStore = create<CategoryState>((set, get) => ({
  categories: [],
  flatCategories: [],
  isLoading: false,

  fetchCategories: async () => {
    set({ isLoading: true });
    try {
      const response = await graphqlRequestWithAuth<{ categories: { categories: Category[]; flatList: Category[] } }>(
        CATEGORIES_QUERY,
        {}
      );

      if (response.data?.categories) {
        const categories = response.data.categories.categories;
        const flatList = response.data.categories.flatList;
        set({
          categories,
          flatCategories: flatList,
          isLoading: false,
        });
      }
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      set({ isLoading: false });
    }
  },

  createCategory: async (input: any) => {
    const response = await graphqlRequestWithAuth<{ createCategory: Category }>(
      CREATE_CATEGORY_MUTATION,
      { input }
    );

    if (response.data?.createCategory) {
      const newCategory = response.data.createCategory;
      set(state => ({
        categories: [...state.categories, newCategory],
        flatCategories: [...state.flatCategories, newCategory],
      }));
      return newCategory;
    }
    throw new Error('Failed to create category');
  },

  updateCategory: async (id: string, input: any) => {
    const response = await graphqlRequestWithAuth<{ updateCategory: Category }>(
      UPDATE_CATEGORY_MUTATION,
      { id, input }
    );

    if (response.data?.updateCategory) {
      const updated = response.data.updateCategory;
      set(state => ({
        categories: state.categories.map(c => c.id === id ? updated : c),
        flatCategories: state.flatCategories.map(c => c.id === id ? updated : c),
      }));
      return updated;
    }
    throw new Error('Failed to update category');
  },

  deleteCategory: async (id: string) => {
    await graphqlRequestWithAuth(DELETE_CATEGORY_MUTATION, { id });

    set(state => ({
      categories: state.categories.filter(c => c.id !== id),
      flatCategories: state.flatCategories.filter(c => c.id !== id),
    }));
  },

  reorderCategories: async (ids: string[]) => {
    const response = await graphqlRequestWithAuth<{ reorderCategories: Category[] }>(
      REORDER_CATEGORIES_MUTATION,
      { categoryIds: ids }
    );

    if (response.data?.reorderCategories) {
      const updated = response.data.reorderCategories;
      const updatedMap = new Map(updated.map(c => [c.id, c]));

      set(state => ({
        categories: state.categories.map(c => updatedMap.get(c.id) || c),
        flatCategories: state.flatCategories.map(c => updatedMap.get(c.id) || c),
      }));
      return updated;
    }
    throw new Error('Failed to reorder categories');
  },
}));

export const useCategories = () => useCategoryStore();