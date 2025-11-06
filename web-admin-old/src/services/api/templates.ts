import { api } from './index';
import type {
  Template,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  TemplateListParams,
  TemplatePreviewRequest,
  TemplatePreviewResponse,
  TemplateValidationRequest,
  TemplateValidationResponse,
} from '../../types/template';

const ENDPOINTS = {
  LIST: '/api/templates',
  CREATE: '/api/templates',
  GET: (id: string) => `/api/templates/${id}`,
  UPDATE: (id: string) => `/api/templates/${id}`,
  DELETE: (id: string) => `/api/templates/${id}`,
  PREVIEW: (id: string) => `/api/templates/${id}/preview`,
  PREVIEW_CONTENT: '/api/templates/preview',
  VALIDATE: '/api/templates/validate',
  DUPLICATE: (id: string) => `/api/templates/${id}/duplicate`,
};

export const templatesAPI = {
  /**
   * Get list of templates
   */
  async list(params?: TemplateListParams): Promise<Template[]> {
    const queryParams = new URLSearchParams();

    if (params?.category) queryParams.append('category', params.category);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.is_active !== undefined) queryParams.append('is_active', String(params.is_active));
    if (params?.page) queryParams.append('page', String(params.page));
    if (params?.limit) queryParams.append('limit', String(params.limit));

    const url = queryParams.toString()
      ? `${ENDPOINTS.LIST}?${queryParams.toString()}`
      : ENDPOINTS.LIST;

    const response = await api.get(url);
    return response.data;
  },

  /**
   * Create new template
   */
  async create(data: CreateTemplateRequest): Promise<Template> {
    const response = await api.post(ENDPOINTS.CREATE, data);
    return response.data;
  },

  /**
   * Get single template by ID
   */
  async get(id: string): Promise<Template> {
    const response = await api.get(ENDPOINTS.GET(id));
    return response.data;
  },

  /**
   * Update template
   */
  async update(id: string, data: UpdateTemplateRequest): Promise<Template> {
    const response = await api.patch(ENDPOINTS.UPDATE(id), data);
    return response.data;
  },

  /**
   * Delete template
   */
  async delete(id: string): Promise<void> {
    await api.delete(ENDPOINTS.DELETE(id));
  },

  /**
   * Preview template with device context
   */
  async preview(request: TemplatePreviewRequest): Promise<TemplatePreviewResponse> {
    // If template_id is provided, use the template-specific preview endpoint
    if (request.template_id) {
      const response = await api.post(ENDPOINTS.PREVIEW(request.template_id), {
        device_id: request.device_id,
        sample_data: request.sample_data,
      });
      return response.data;
    }

    // Otherwise, use the generic preview endpoint with content
    const response = await api.post(ENDPOINTS.PREVIEW_CONTENT, request);
    return response.data;
  },

  /**
   * Validate template syntax and security
   */
  async validate(request: TemplateValidationRequest): Promise<TemplateValidationResponse> {
    const response = await api.post(ENDPOINTS.VALIDATE, request);
    return response.data;
  },

  /**
   * Duplicate template
   */
  async duplicate(id: string, newName?: string): Promise<Template> {
    const response = await api.post(ENDPOINTS.DUPLICATE(id), {
      name: newName,
    });
    return response.data;
  },

  /**
   * Toggle template active status
   */
  async toggleActive(id: string, isActive: boolean): Promise<Template> {
    return this.update(id, { is_active: isActive });
  },
};

export default templatesAPI;
