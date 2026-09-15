// 用户类型
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  date_joined: string;
}

// 服务器类型
export interface Server {
  id: number;
  name: string;
  ip_address: string;
  status: 'running' | 'stopped' | 'warning' | 'error';
  status_display: string;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  os_type: string;
  location: string;
  created_at: string;
  updated_at: string;
}

// 告警类型
export interface Alert {
  id: number;
  title: string;
  description: string;
  level: 'info' | 'warning' | 'danger';
  level_display: string;
  status: 'pending' | 'processing' | 'resolved';
  status_display: string;
  server_id: number | null;
  server_name: string | null;
  created_at: string;
  resolved_at: string | null;
}

// 任务类型
export interface Task {
  id: number;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  status_display: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  priority_display: string;
  assigned_to: number | null;
  assigned_to_name: string | null;
  created_at: string;
  completed_at: string | null;
}

// 操作日志类型
export interface OperationLog {
  id: number;
  action: string;
  description: string;
  user_id: number | null;
  username: string | null;
  ip_address: string;
  created_at: string;
}

// 仪表板统计类型
export interface DashboardStats {
  total_servers: number;
  running_servers: number;
  stopped_servers: number;
  warning_servers: number;
  total_alerts: number;
  pending_alerts: number;
  danger_alerts: number;
  total_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  avg_cpu_usage: number;
  avg_memory_usage: number;
  avg_disk_usage: number;
}

// API响应类型
export interface ApiResponse<T> {
  success: boolean;
  code: number;
  message: string;
  data: T;
}

// 登录响应
export interface LoginResponse {
  token: string;
  user: User;
}

// 登录失败时后端返回的补充信息（用于区分验证码错误与账号密码错误）
export interface LoginErrorData {
  error?: 'BAD_CREDENTIALS' | 'CAPTCHA_REQUIRED' | 'CAPTCHA_INVALID';
  fail_count?: number;
  fail_threshold?: number;
  captcha_required?: boolean;
}

// 验证码图片
export interface CaptchaImage {
  captcha_id: string;
  image: string; // data:image/svg+xml;base64,... 可直接用于 <img src>
}

// 验证码开关配置
export interface CaptchaConfig {
  captcha_enabled: boolean;
  fail_threshold: number;
}

// 登录状态（某用户名当前是否需要验证码）
export interface LoginState {
  captcha_enabled: boolean;
  fail_threshold: number;
  fail_count: number;
  captcha_required: boolean;
}
