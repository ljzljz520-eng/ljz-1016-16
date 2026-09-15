import { ApiResponse, LoginResponse, LoginErrorData, CaptchaImage, CaptchaConfig, LoginState, DashboardStats, Server, Alert, Task, OperationLog } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token');
    }
    return null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}/api${endpoint}`;
    const token = this.getToken();

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();
      return data as ApiResponse<T>;
    } catch (error) {
      return {
        success: false,
        code: 500,
        message: '网络请求失败，请检查网络连接',
        data: null as unknown as T,
      };
    }
  }

  // 登录（可选携带验证码；失败时 data 为 LoginErrorData）
  async login(
    username: string,
    password: string,
    captchaId?: string,
    captchaCode?: string
  ): Promise<ApiResponse<LoginResponse | LoginErrorData>> {
    return this.request<LoginResponse | LoginErrorData>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({
        username,
        password,
        ...(captchaId ? { captcha_id: captchaId } : {}),
        ...(captchaCode ? { captcha_code: captchaCode } : {}),
      }),
    });
  }

  // 获取验证码图片（SVG data URI）
  async getCaptcha(): Promise<ApiResponse<CaptchaImage>> {
    return this.request<CaptchaImage>('/auth/captcha/');
  }

  // 查询指定用户名的登录状态（是否需要验证码）
  async getLoginState(username: string): Promise<ApiResponse<LoginState>> {
    return this.request<LoginState>(`/auth/login-state/?username=${encodeURIComponent(username)}`);
  }

  // 获取验证码开关配置
  async getCaptchaConfig(): Promise<ApiResponse<CaptchaConfig>> {
    return this.request<CaptchaConfig>('/auth/captcha/config/');
  }

  // 修改验证码开关配置（需管理员）
  async updateCaptchaConfig(config: Partial<CaptchaConfig>): Promise<ApiResponse<CaptchaConfig>> {
    return this.request<CaptchaConfig>('/auth/captcha/config/', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // 清空所有登录失败计数（需管理员）
  async resetLoginFails(): Promise<ApiResponse<null>> {
    return this.request<null>('/auth/captcha/reset-fails/', {
      method: 'POST',
    });
  }

  // 登出
  async logout(): Promise<ApiResponse<null>> {
    return this.request<null>('/auth/logout/', {
      method: 'POST',
    });
  }

  // 获取当前用户信息
  async getUserInfo(): Promise<ApiResponse<any>> {
    return this.request<any>('/auth/user/');
  }

  // 获取仪表板统计
  async getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
    return this.request<DashboardStats>('/dashboard/stats/');
  }

  // 获取服务器列表
  async getServers(): Promise<ApiResponse<Server[]>> {
    return this.request<Server[]>('/servers/');
  }

  // 获取告警列表
  async getAlerts(status?: string, level?: string): Promise<ApiResponse<Alert[]>> {
    let endpoint = '/alerts/';
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (level) params.append('level', level);
    if (params.toString()) endpoint += `?${params.toString()}`;
    return this.request<Alert[]>(endpoint);
  }

  // 获取任务列表
  async getTasks(status?: string, priority?: string): Promise<ApiResponse<Task[]>> {
    let endpoint = '/tasks/';
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);
    if (params.toString()) endpoint += `?${params.toString()}`;
    return this.request<Task[]>(endpoint);
  }

  // 获取操作日志
  async getOperationLogs(): Promise<ApiResponse<OperationLog[]>> {
    return this.request<OperationLog[]>('/logs/');
  }
}

export const api = new ApiClient(API_BASE_URL);
