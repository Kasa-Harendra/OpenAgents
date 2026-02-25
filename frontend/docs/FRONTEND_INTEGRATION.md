# Frontend Integration Guide - OpenAgents Desktop

## Overview

The OpenAgents Desktop application now features full integration with the backend task orchestration system. Users can submit tasks, monitor real-time progress, view execution plans, and see detailed results—all through an elegant Electron-based UI.

## Architecture

```
Frontend (Electron + React)
    ↓
API Client (lib/api.ts)
    ↓
FastAPI Backend (localhost:8000)
    ↓
Task Orchestrator + Agents
```

## Key Features

### ✅ Task Submission

- Submit natural language task descriptions
- Automatic task creation via backend API
- Immediate navigation to execution view

### ✅ Real-Time Updates

- WebSocket connection for live progress
- Automatic UI updates as agents execute
- No polling required

### ✅ Execution Visualization

- Step-by-step execution plan display
- Agent progress indicators
- Duration tracking
- Status icons and colors

### ✅ Results Display

- Final aggregated results
- Individual agent outputs
- Error handling and display
- Execution timeline

## File Structure

```
src/renderer/
├── lib/
│   └── api.ts                 # API client with all backend endpoints
├── stores/
│   └── taskStore.ts           # Zustand store with backend integration
├── pages/
│   ├── Home.tsx               # Task submission interface
│   └── Execution.tsx          # Real-time execution monitoring
└── components/
    └── ui/                    # Reusable UI components
```

## API Client (`lib/api.ts`)

### Methods

| Method                                | Description          | Returns               |
| ------------------------------------- | -------------------- | --------------------- |
| `submitTask(request)`                 | Submit a new task    | `TaskResponse`        |
| `getTaskStatus(taskId)`               | Get current status   | `TaskStatusResponse`  |
| `getTaskResults(taskId)`              | Get full results     | `TaskResultsResponse` |
| `listTasks(params)`                   | List all tasks       | `TaskListResponse`    |
| `cancelTask(taskId)`                  | Cancel running task  | Status object         |
| `deleteTask(taskId)`                  | Delete a task        | Status object         |
| `connectWebSocket(taskId, onMessage)` | Real-time updates    | `WebSocket`           |
| `healthCheck()`                       | Check backend status | `boolean`             |

### Example Usage

```typescript
import { api } from "@/lib/api";

// Submit a task
const response = await api.submitTask({
  description: "Analyze sales data",
  user_id: "user123",
  priority: 5,
});

// Connect to WebSocket for updates
const ws = api.connectWebSocket(response.task_id, (message) => {
  console.log("Update:", message.type, message.data);
});
```

## Task Store (`stores/taskStore.ts`)

### State

```typescript
interface TaskStore {
  tasks: Task[]; // All tasks
  currentTask: Task | null; // Currently viewing task
  isLoading: boolean; // Loading state
  launcherOpen: boolean; // Command launcher state
  wsConnection: WebSocket | null; // Active WebSocket
}
```

### Actions

| Action                           | Description                 |
| -------------------------------- | --------------------------- |
| `startTask(description, userId)` | Submit and track new task   |
| `loadTasks()`                    | Load all tasks from backend |
| `refreshTask(taskId)`            | Refresh task details        |
| `cancelTask(taskId)`             | Cancel a running task       |
| `deleteTask(taskId)`             | Delete a task               |
| `connectToTask(taskId)`          | Connect WebSocket           |
| `disconnectWebSocket()`          | Close WebSocket connection  |

### Example Usage

```typescript
import { useTaskStore } from '@/stores/taskStore';

function MyComponent() {
  const { startTask, tasks, currentTask } = useTaskStore();

  const handleSubmit = async () => {
    const task = await startTask('My task description', 'user123');
    if (task) {
      // Task created and WebSocket connected
      console.log('Task ID:', task.id);
    }
  };

  return (
    <div>
      {tasks.map(task => (
        <div key={task.id}>{task.description}</div>
      ))}
    </div>
  );
}
```

## Home Page (`pages/Home.tsx`)

### Features

- Clean, centered task input interface
- Example prompts for quick start
- Keyboard shortcuts (Cmd/Ctrl + Enter to submit)
- Loading states
- Automatic navigation to execution view

### User Flow

1. User enters task description
2. Clicks "Start Task" or presses Cmd/Ctrl + Enter
3. Task is submitted to backend
4. User is redirected to `/execution/:taskId`
5. WebSocket connection is established

## Execution Page (`pages/Execution.tsx`)

### Features

#### Status Display

- Real-time status updates (pending → planning → executing → completed)
- Progress percentage
- Current agent indicator
- Execution duration

#### Execution Plan

- Visual representation of planned steps
- Agent icons and names
- Step reasoning
- Dependencies (if any)

#### Agent Timeline

- Live progress for each agent
- Status indicators (pending, running, completed, failed)
- Individual agent outputs
- Error messages
- Execution duration per agent

#### Results

- Final aggregated result
- Complete execution history
- Error details (if failed)

### Real-Time Updates

The execution page automatically updates via WebSocket:

```typescript
// WebSocket message types handled:
-"status_updated" - // Task status changed
  "planning_complete" - // Plan created
  "agent_started" - // Agent began execution
  "agent_completed" - // Agent finished
  "agent_failed" - // Agent error
  "task_completed" - // Task finished
  "task_failed"; // Task error
```

## Type Definitions

### Task

```typescript
interface Task {
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
```

### TaskStatus

```typescript
type TaskStatus =
  | "pending" // Just created
  | "planning" // Orchestrator creating plan
  | "executing" // Agents running
  | "completed" // Successfully finished
  | "failed" // Error occurred
  | "cancelled"; // User cancelled
```

### AgentExecutionRecord

```typescript
interface AgentExecutionRecord {
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
```

## Running the Application

### Prerequisites

1. **Backend Running**

   ```bash
   cd backend
   python main.py
   ```

   Backend should be running on `http://localhost:8000`

2. **Install Frontend Dependencies**
   ```bash
   cd openagents-desktop
   npm install
   ```

### Development Mode

```bash
npm run dev
```

This starts:

- Vite dev server for React
- Electron app in development mode
- Hot reload enabled

### Production Build

```bash
npm run build
```

## Testing the Integration

### 1. Check Backend Connection

```typescript
import { api } from "@/lib/api";

const isHealthy = await api.healthCheck();
console.log("Backend healthy:", isHealthy);
```

### 2. Submit a Test Task

1. Start the desktop app
2. Enter a simple task: "List all files in the current directory"
3. Click "Start Task"
4. Watch the execution page for real-time updates

### 3. Monitor WebSocket

Open browser DevTools (Cmd/Ctrl + Shift + I) and check:

- Console for WebSocket messages
- Network tab for WebSocket connection

## Troubleshooting

### Backend Not Reachable

**Symptom**: Tasks fail to submit, health check fails

**Solutions**:

1. Verify backend is running: `curl http://localhost:8000/`
2. Check firewall settings
3. Verify port 8000 is not blocked
4. Check backend logs for errors

### WebSocket Connection Fails

**Symptom**: No real-time updates, connection errors in console

**Solutions**:

1. Verify backend WebSocket endpoint: `ws://localhost:8000/tasks/ws/{task_id}`
2. Check browser console for WebSocket errors
3. Ensure task ID is valid
4. Try refreshing the page

### Task Stuck in "Planning"

**Symptom**: Task status doesn't progress beyond planning

**Solutions**:

1. Check backend logs for orchestrator errors
2. Verify LLM provider configuration in backend `.env`
3. Check API keys are valid
4. Manually refresh task status

### UI Not Updating

**Symptom**: Status changes but UI doesn't reflect them

**Solutions**:

1. Check WebSocket connection status
2. Verify task store is receiving updates
3. Check React DevTools for state changes
4. Try disconnecting and reconnecting WebSocket

## Advanced Features

### Custom User IDs

```typescript
// In Home.tsx
const handleSubmit = async () => {
  const userId = getUserIdFromAuth(); // Your auth logic
  const task = await startTask(prompt, userId);
  // ...
};
```

### Task Filtering

```typescript
// Load only completed tasks
const completedTasks = await api.listTasks({
  status: "completed",
  page: 1,
  page_size: 20,
});
```

### Manual Refresh

```typescript
// Force refresh task data
await refreshTask(taskId);
```

### Task Cancellation

```typescript
// Cancel a running task
await cancelTask(taskId);
```

## UI Components

### Status Icons

| Status    | Icon | Color  |
| --------- | ---- | ------ |
| Pending   | ⏳   | Gray   |
| Planning  | 🧠   | Blue   |
| Executing | ⚡   | Purple |
| Completed | ✅   | Green  |
| Failed    | ❌   | Red    |
| Cancelled | ⚠️   | Orange |

### Agent Icons

| Agent            | Icon |
| ---------------- | ---- |
| TerminalAgent    | 💻   |
| FileSystemAgent  | 📁   |
| BrowserAgent     | 🌐   |
| RAGAgent         | 📚   |
| IntegrationAgent | 🔗   |
| ResearchAgent    | 🔍   |
| ScrapingAgent    | 🕷️   |

## Performance Considerations

### WebSocket Management

- Connections are automatically closed when leaving execution page
- Only one WebSocket connection per task
- Automatic reconnection on connection loss

### State Updates

- Zustand provides efficient re-renders
- Only affected components update
- Task list pagination prevents memory issues

### API Calls

- Axios instance with proper error handling
- Request/response interceptors for logging
- Automatic retry on network errors

## Future Enhancements

### Planned Features

- [ ] Task history and search
- [ ] Task templates
- [ ] Batch task submission
- [ ] Export results
- [ ] Task scheduling
- [ ] User authentication integration
- [ ] Dark/light theme toggle
- [ ] Notifications for task completion

## Summary

The frontend is now fully integrated with the backend task orchestration system, providing:

✅ Seamless task submission  
✅ Real-time progress monitoring  
✅ Beautiful execution visualization  
✅ Comprehensive error handling  
✅ WebSocket-based live updates  
✅ Type-safe API client  
✅ Reactive state management

Users can now submit complex tasks and watch as the multi-agent system plans, executes, and delivers results—all in real-time!
