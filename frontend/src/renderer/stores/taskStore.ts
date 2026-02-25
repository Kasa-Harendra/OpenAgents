import { create } from 'zustand';
import { api, TaskStatus, TaskResultsResponse, AgentExecutionRecord, TaskPlan, WebSocketMessage } from '@/lib/api';

export interface Task {
  id: string;
  description: string;
  status: TaskStatus;
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
  userId?: string;
  
  // Execution details
  plan?: TaskPlan;
  agentExecutions: AgentExecutionRecord[];
  currentAgent?: string;
  currentStep?: number;
  totalSteps?: number;
  progressPercentage: number;
  agentsCompleted: string[];
  agentsPending: string[];
  
  // Results
  finalResult?: string;
  error?: any;
  totalDurationSeconds?: number;
}

interface TaskStore {
  tasks: Task[];
  currentTask: Task | null;
  isLoading: boolean;
  launcherOpen: boolean;
  wsConnection: WebSocket | null;
  
  // Actions
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  setCurrentTask: (task: Task | null) => void;
  setLoading: (loading: boolean) => void;
  openLauncher: () => void;
  closeLauncher: () => void;
  
  // Async actions
  loadTasks: () => Promise<void>;
  startTask: (description: string, userId?: string) => Promise<Task | null>;
  refreshTask: (taskId: string) => Promise<void>;
  cancelTask: (taskId: string) => Promise<void>;
  deleteTask: (taskId: string) => Promise<void>;
  
  // WebSocket actions
  connectToTask: (taskId: string) => void;
  disconnectWebSocket: () => void;
}

// Helper to convert backend response to frontend Task
function convertToTask(response: TaskResultsResponse): Task {
  return {
    id: response.task_id,
    description: response.description,
    status: response.status,
    createdAt: new Date(response.created_at),
    updatedAt: new Date(response.updated_at),
    completedAt: response.completed_at ? new Date(response.completed_at) : undefined,
    userId: response.user_id,
    plan: response.plan,
    agentExecutions: response.agent_executions || [],
    currentAgent: undefined,
    currentStep: response.plan?.steps.length,
    totalSteps: response.plan?.steps.length,
    progressPercentage: 0,
    agentsCompleted: response.agent_executions
      ?.filter(e => e.status === 'completed')
      .map(e => e.agent_name) || [],
    agentsPending: [],
    finalResult: response.final_result,
    error: response.error,
    totalDurationSeconds: response.total_duration_seconds,
  };
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  currentTask: null,
  isLoading: false,
  launcherOpen: false,
  wsConnection: null,

  setTasks: (tasks) => set({ tasks }),
  
  addTask: (task) => set((state) => ({ 
    tasks: [task, ...state.tasks] 
  })),
  
  updateTask: (id, updates) => set((state) => {
    const tasks = state.tasks.map((task) =>
      task.id === id ? { ...task, ...updates, updatedAt: new Date() } : task
    );
    
    // Also update currentTask if it matches
    const currentTask = state.currentTask?.id === id
      ? { ...state.currentTask, ...updates, updatedAt: new Date() }
      : state.currentTask;
    
    return { tasks, currentTask };
  }),
  
  setCurrentTask: (task) => set({ currentTask: task }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  openLauncher: () => set({ launcherOpen: true }),
  
  closeLauncher: () => set({ launcherOpen: false }),

  loadTasks: async () => {
    try {
      const response = await api.listTasks({ page: 1, page_size: 50 });
      
      // Convert backend tasks to frontend format
      const tasks: Task[] = await Promise.all(
        response.tasks.map(async (taskItem) => {
          try {
            const fullTask = await api.getTaskResults(taskItem.task_id);
            return convertToTask(fullTask);
          } catch (error) {
            // Fallback to basic task info if full details fail
            return {
              id: taskItem.task_id,
              description: taskItem.description,
              status: taskItem.status,
              createdAt: new Date(taskItem.created_at),
              updatedAt: new Date(taskItem.created_at),
              completedAt: taskItem.completed_at ? new Date(taskItem.completed_at) : undefined,
              userId: taskItem.user_id,
              agentExecutions: [],
              progressPercentage: 0,
              agentsCompleted: [],
              agentsPending: [],
            };
          }
        })
      );
      
      set({ tasks });
    } catch (error) {
      console.error('Failed to load tasks:', error);
      set({ tasks: [] });
    }
  },

  startTask: async (description, userId) => {
    try {
      set({ isLoading: true });
      
      // Submit task to backend
      const response = await api.submitTask({
        description,
        user_id: userId,
        priority: 5,
      });
      
      // Create initial task object
      const task: Task = {
        id: response.task_id,
        description: response.description,
        status: response.status,
        createdAt: new Date(response.created_at),
        updatedAt: new Date(response.created_at),
        userId: response.user_id,
        agentExecutions: [],
        progressPercentage: 0,
        agentsCompleted: [],
        agentsPending: [],
      };
      
      get().addTask(task);
      set({ currentTask: task, isLoading: false });
      
      // Connect to WebSocket for real-time updates
      get().connectToTask(task.id);
      
      return task;
    } catch (error) {
      console.error('Failed to start task:', error);
      set({ isLoading: false });
      return null;
    }
  },

  refreshTask: async (taskId: string) => {
    try {
      const response = await api.getTaskResults(taskId);
      const task = convertToTask(response);
      
      get().updateTask(taskId, task);
      
      // Update currentTask if it's the same task
      if (get().currentTask?.id === taskId) {
        set({ currentTask: task });
      }
    } catch (error) {
      console.error('Failed to refresh task:', error);
    }
  },

  cancelTask: async (taskId: string) => {
    try {
      await api.cancelTask(taskId);
      get().updateTask(taskId, { status: 'cancelled' });
    } catch (error) {
      console.error('Failed to cancel task:', error);
    }
  },

  deleteTask: async (taskId: string) => {
    try {
      await api.deleteTask(taskId);
      set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== taskId),
        currentTask: state.currentTask?.id === taskId ? null : state.currentTask,
      }));
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  },

  connectToTask: (taskId: string) => {
    // Disconnect existing connection
    get().disconnectWebSocket();
    
    const ws = api.connectWebSocket(
      taskId,
      (message: WebSocketMessage) => {
        console.log('WebSocket message:', message);
        
        // Handle different message types
        switch (message.type) {
          case 'status_updated':
            get().updateTask(taskId, {
              status: message.data.status,
              progressPercentage: message.data.progress_percentage || 0,
            });
            break;
            
          case 'planning_complete':
            get().updateTask(taskId, {
              plan: message.data.plan,
              totalSteps: message.data.plan?.steps.length,
            });
            break;
            
          case 'agent_started':
            get().updateTask(taskId, {
              currentAgent: message.data.agent_name,
              currentStep: message.data.step_number,
            });
            break;
            
          case 'agent_completed':
            get().refreshTask(taskId);
            break;
            
          case 'agent_failed':
            get().refreshTask(taskId);
            break;
            
          case 'task_completed':
            get().refreshTask(taskId);
            break;
            
          case 'task_failed':
            get().updateTask(taskId, {
              status: 'failed',
              error: message.data.error,
            });
            break;
        }
      },
      (error) => {
        console.error('WebSocket error:', error);
      },
      (event) => {
        console.log('WebSocket closed:', event);
        set({ wsConnection: null });
      }
    );
    
    set({ wsConnection: ws });
  },

  disconnectWebSocket: () => {
    const ws = get().wsConnection;
    if (ws) {
      ws.close();
      set({ wsConnection: null });
    }
  },
}));
