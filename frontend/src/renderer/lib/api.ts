import axios from 'axios';

// --- Types ---

export type TaskStatus =
  | 'pending'
  | 'planning'
  | 'executing'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type AgentStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface TaskPlanStep {
  agent_name: string;
  description: string;
  reasoning?: string;
  dependencies?: string[];
}

export interface TaskPlan {
  steps: TaskPlanStep[];
}

export interface AgentExecutionRecord {
  agent_name: string;
  task_description: string;
  status: AgentStatus;
  input_data?: Record<string, any>;
  output?: string;
  error?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
}

export interface TaskResponse {
  task_id: string;
  description: string;
  status: TaskStatus;
  created_at: string;
  updated_at: string;
  user_id?: string;
}

export interface TaskItem {
  task_id: string;
  description: string;
  status: TaskStatus;
  created_at: string;
  completed_at?: string;
  user_id?: string;
}

export interface TaskListResponse {
  tasks: TaskItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface TaskResultsResponse extends TaskResponse {
  completed_at?: string;
  plan?: TaskPlan;
  agent_executions: AgentExecutionRecord[];
  final_result?: string;
  error?: any;
  total_duration_seconds?: number;
}

export type WebSocketMessageType =
  | 'status_updated'
  | 'planning_complete'
  | 'agent_started'
  | 'agent_completed'
  | 'agent_failed'
  | 'task_completed'
  | 'task_failed'
  | 'error';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  task_id: string;
  data: any;
}

// --- API Client ---

const BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  /**
   * Submit a new task to the backend
   */
  submitTask: async (request: {
    description: string;
    user_id?: string;
    priority?: number;
  }): Promise<TaskResponse> => {
    const response = await client.post<TaskResponse>('/tasks', request);
    return response.data;
  },

  /**
   * Get the current status of a task
   */
  getTaskStatus: async (taskId: string): Promise<TaskResponse> => {
    const response = await client.get<TaskResponse>(`/tasks/${taskId}/status`);
    return response.data;
  },

  /**
   * Get full results for a task
   */
  getTaskResults: async (taskId: string): Promise<TaskResultsResponse> => {
    const response = await client.get<TaskResultsResponse>(`/tasks/${taskId}/results`);
    return response.data;
  },

  /**
   * List all tasks with optional filtering
   */
  listTasks: async (params: {
    status?: TaskStatus;
    user_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<TaskListResponse> => {
    const response = await client.get<TaskListResponse>('/tasks', { params });
    return response.data;
  },

  /**
   * Cancel a running task
   */
  cancelTask: async (taskId: string): Promise<{ status: string }> => {
    const response = await client.post<{ status: string }>(`/tasks/${taskId}/cancel`);
    return response.data;
  },

  /**
   * Delete a task
   */
  deleteTask: async (taskId: string): Promise<{ status: string }> => {
    const response = await client.delete<{ status: string }>(`/tasks/${taskId}`);
    return response.data;
  },

  /**
   * Establish a WebSocket connection for real-time updates
   */
  connectWebSocket: (
    taskId: string,
    onMessage: (message: WebSocketMessage) => void,
    onError?: (error: any) => void,
    onClose?: (event: CloseEvent) => void
  ): WebSocket => {
    const ws = new WebSocket(`${WS_BASE_URL}/tasks/ws/${taskId}`);

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        onMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    if (onError) {
      ws.onerror = onError;
    }

    if (onClose) {
      ws.onclose = onClose;
    }

    return ws;
  },

  /**
   * Check if the backend is healthy
   */
  healthCheck: async (): Promise<boolean> => {
    try {
      await axios.get(`${BASE_URL}/health`);
      return true;
    } catch {
      return false;
    }
  },
};
