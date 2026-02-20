import { create } from 'zustand';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: any; // Can be string or JSON object for tool outputs
  timestamp: number;
  type?: 'prompt' | 'tool_output' | 'agent_response' | 'error' | 'complete' | 'status' | 'tasks_decomposed' | 'agent_start';
  agentName?: string;
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  isTyping?: boolean;
}

interface ChatState {
  chats: Chat[];
  activeChatId: string | null;
  socket: WebSocket | null;
  isConnected: boolean;
  addChat: (title: string) => void;
  removeChat: (id: string) => void;
  setActiveChat: (id: string | null) => void;
  addMessage: (chatId: string, role: 'user' | 'assistant', content: any, type?: Message['type'], agentName?: string) => void;
  updateChatTitle: (id: string, title: string) => void;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (content: string) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  chats: [],
  activeChatId: null,
  socket: null,
  isConnected: false,
  
  addChat: (title) => {
    const newChat: Chat = {
      id: crypto.randomUUID(),
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    set((state) => ({
      chats: [newChat, ...state.chats],
      activeChatId: newChat.id,
    }));
  },
  
  removeChat: (id) => {
    set((state) => ({
      chats: state.chats.filter((c) => c.id !== id),
      activeChatId: state.activeChatId === id ? null : state.activeChatId,
    }));
  },
  
  setActiveChat: (id) => set({ activeChatId: id }),
  
  addMessage: (chatId, role, content, type, agentName) => {
    const newMessage: Message = {
      id: Math.random().toString(36).substring(7),
      role,
      content,
      timestamp: Date.now(),
      type,
      agentName
    };
    set((state) => ({
      chats: state.chats.map((chat) =>
        chat.id === chatId
          ? { ...chat, messages: [...chat.messages, newMessage] }
          : chat
      ),
    }));
  },
  
  updateChatTitle: (id, title) => {
    set((state) => ({
      chats: state.chats.map((chat) =>
        chat.id === id ? { ...chat, title } : chat
      ),
    }));
  },

  connect: () => {
    const { socket: existingSocket } = get();
    if (existingSocket && (existingSocket.readyState === WebSocket.OPEN || existingSocket.readyState === WebSocket.CONNECTING)) return;

    const newSocket = new WebSocket('ws://localhost:8000/ws');

    newSocket.onopen = () => {
      console.log('WebSocket Connected');
      set({ isConnected: true });
    };

    newSocket.onclose = () => {
      console.log('WebSocket Disconnected');
      set({ isConnected: false, socket: null });
      
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        const { isConnected } = get();
        if (!isConnected) {
            console.log('Attempting to reconnect...');
            get().connect();
        }
      }, 3000);
    };

    newSocket.onmessage = (event) => {
      const { activeChatId, addMessage } = get();
      if (!activeChatId) return;

      try {
        const data = JSON.parse(event.data);
        // Map backend types to frontend logic if needed, or use directly
        // 'data' should match 'websocket_message' from backend: { type, agent_name, content, step }
        
        addMessage(activeChatId, 'assistant', data.content, data.type, data.agent_name);
        
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    set({ socket: newSocket });
  },

  disconnect: () => {
    const { socket } = get();
    if (socket) {
        socket.onclose = null; // Prevent race condition where onclose clears new socket
        socket.onmessage = null;
        socket.onopen = null;
        socket.close();
    }
    set({ socket: null, isConnected: false });
  },

  sendMessage: (content: string) => {
    const { socket, activeChatId, addMessage, chats } = get();
    console.log('sendMessage called. Socket:', socket, 'readyState:', socket?.readyState, 'isConnected:', get().isConnected);
    
    if (!socket || socket.readyState !== WebSocket.OPEN || !activeChatId) {
       console.error("Socket not connected or no active chat. ReadyState:", socket?.readyState);
       const { addMessage } = get();
       if (activeChatId) {
            addMessage(activeChatId, 'assistant', `Error: Could not send message. Connection to backend is lost. (State: ${socket?.readyState}) Please refresh or try again.`, 'error');
       }
       return;
    }

    addMessage(activeChatId, 'user', content);

    try {

    // Prepare history: last 3 prompts and ai responses (approx)
    // Filter for user/assistant roles, take last 6 messages (3 turns)
    // Truncate assistant responses to 200 chars
    const currentChat = chats.find(c => c.id === activeChatId);
    const history = currentChat?.messages
      .filter(m => m.role === 'user' || (m.role === 'assistant' && m.type === 'agent_response')) // Avoid tool outputs in history context if desired, or include them? Requirement said "no tool response"
      .slice(-6) 
      .map(m => ({
        role: m.role,
        content: m.role === 'assistant' && typeof m.content === 'string' 
          ? m.content.substring(0, 200) 
          : m.content
      })) || [];

    const payload = {
      prompt: content,
      session_id: activeChatId,
      history: history
    };

      socket.send(JSON.stringify(payload));
    } catch (error) {
        console.error("Failed to send message:", error);
        addMessage(activeChatId, 'assistant', "Error: Failed to send message.", 'error');
    }
  }
}));
