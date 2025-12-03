import type { DataProvider } from "@refinedev/core";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

// Helper para adicionar token de autenticação
const getHeaders = (): HeadersInit => {
  const token = localStorage.getItem("access_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

// Helper para construir query params
const buildQueryParams = (
  pagination?: { current?: number; pageSize?: number; mode?: string },
  filters?: Array<{ field: string; operator: string; value: unknown }>,
  sorters?: Array<{ field: string; order: string }>
): URLSearchParams => {
  const params = new URLSearchParams();

  if (pagination && pagination.current && pagination.pageSize) {
    params.append("page", pagination.current.toString());
    params.append("page_size", pagination.pageSize.toString());
  }

  if (filters) {
    filters.forEach((filter) => {
      params.append(`filter[${filter.field}]`, String(filter.value));
    });
  }

  if (sorters && sorters.length > 0) {
    const sorter = sorters[0];
    params.append("sort", sorter.field);
    params.append("order", sorter.order);
  }

  return params;
};

export const flaskDataProvider: DataProvider = {
  getList: async ({ resource, pagination, filters, sorters }) => {
    const params = buildQueryParams(
      pagination as { current?: number; pageSize?: number; mode?: string },
      filters as Array<{ field: string; operator: string; value: unknown }>,
      sorters as Array<{ field: string; order: string }>
    );
    
    const response = await fetch(`${API_URL}/${resource}?${params}`, {
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Erro ao buscar ${resource}`);
    }

    const data = await response.json();

    return {
      data: data.items || data,
      total: data.total || data.length,
    };
  },

  getOne: async ({ resource, id }) => {
    const response = await fetch(`${API_URL}/${resource}/${id}`, {
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Erro ao buscar ${resource}/${id}`);
    }

    const data = await response.json();
    return { data };
  },

  create: async ({ resource, variables }) => {
    const response = await fetch(`${API_URL}/${resource}`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(variables),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `Erro ao criar ${resource}`);
    }

    const data = await response.json();
    return { data };
  },

  update: async ({ resource, id, variables }) => {
    const response = await fetch(`${API_URL}/${resource}/${id}`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(variables),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `Erro ao atualizar ${resource}/${id}`);
    }

    const data = await response.json();
    return { data };
  },

  deleteOne: async ({ resource, id }) => {
    const response = await fetch(`${API_URL}/${resource}/${id}`, {
      method: "DELETE",
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Erro ao deletar ${resource}/${id}`);
    }

    const data = await response.json();
    return { data };
  },

  getMany: async ({ resource, ids }) => {
    const data = await Promise.all(
      ids.map(async (id) => {
        const response = await fetch(`${API_URL}/${resource}/${id}`, {
          headers: getHeaders(),
        });
        return response.json();
      })
    );

    return { data };
  },

  getApiUrl: () => API_URL,
};
