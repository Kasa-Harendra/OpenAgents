import { create } from 'zustand';
import toast from 'react-hot-toast';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: any; // Can be string or JSON object for tool outputs
  timestamp: number;
  type?: 'prompt' | 'tool_output' | 'agent_response' | 'error' | 'complete' | 'status' | 'tasks_decomposed' | 'agent_start' | 'content_chunk';
  agentName?: string;
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  isTyping?: boolean;
  baseDirectory: string | null;
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
  updateLastMessage: (chatId: string, content: any, type?: Message['type'], isAppend?: boolean) => void;
  updateChatTitle: (id: string, title: string) => void;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (content: string) => void;
  cancelExecution: () => void;
  setBaseDirectory: (path: string | null) => void;
  setIsTyping: (chatId: string, isTyping: boolean) => void;
  chatMode: 'multiagent' | 'chat';
  setChatMode: (mode: 'multiagent' | 'chat') => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  chats: [],
  activeChatId: null,
  socket: null,
  isConnected: false,
  chatMode: 'multiagent',
  
  setBaseDirectory: (path) => set((state) => ({
    chats: state.chats.map((chat) =>
      chat.id === state.activeChatId ? { ...chat, baseDirectory: path } : chat
    ),
  })),
  setIsTyping: (chatId, isTyping) => set((state) => ({
    chats: state.chats.map((chat) =>
      chat.id === chatId ? { ...chat, isTyping } : chat
    ),
  })),
  setChatMode: (mode) => set({ chatMode: mode }),
  
  addChat: (title) => {
    const newChat: Chat = {
      id: crypto.randomUUID(),
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      baseDirectory: null,
      isTyping: false,
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

  updateLastMessage: (chatId, content, type, isAppend) => {
    set((state) => ({
      chats: state.chats.map((chat) => {
        if (chat.id === chatId && chat.messages.length > 0) {
          const updatedMessages = [...chat.messages];
          const lastIndex = updatedMessages.length - 1;
          const lastMessage = updatedMessages[lastIndex];
          
          const newContent = isAppend ? (lastMessage.content || '') + content : content;
          
          updatedMessages[lastIndex] = {
            ...lastMessage,
            content: newContent,
            type: type || lastMessage.type
          };
          
          return { ...chat, messages: updatedMessages };
        }
        return chat;
      }),
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
      const { activeChatId, addMessage, updateLastMessage } = get();
      if (!activeChatId) return;

      try {
        const data = JSON.parse(event.data);
        const { type, agent_name, content, chunk, session_id } = data;
        
        const targetChatId = session_id || activeChatId;
        
        const currentChat = get().chats.find(c => c.id === targetChatId);
        if (!currentChat) return;
        
        const lastMsg = currentChat.messages[currentChat.messages.length - 1];

        if (type === 'agent_error') {
          // Show agent errors as toasts and don't add to chat to avoid clutter
          toast.error(`${agent_name ? agent_name + ': ' : ''}${content}`, {
            duration: 5000,
            position: 'top-center',
          });
          get().setIsTyping(targetChatId, false);
          return;
        }

        if (type === 'tool_error') {
          // Suppress tool errors from UI as per user request
          console.error(`Tool error in ${agent_name}:`, content);
          return;
        }
        
        if (type === 'error' || type === 'complete') {
            get().setIsTyping(targetChatId, false);
            // Optionally, we could still add normal 'error'/complete messages if needed
            // But usually we don't display 'complete' to user unless we want a status update.
            if (type === 'error') {
                 addMessage(targetChatId, 'assistant', content, type, agent_name);
            }
            return;
        }

        if (type === 'content_chunk') {
          if (lastMsg && lastMsg.role === 'assistant' && (lastMsg.type === 'agent_response' || lastMsg.type === 'content_chunk')) {
            updateLastMessage(targetChatId, chunk, 'agent_response', true);
          } else {
            addMessage(targetChatId, 'assistant', chunk, 'agent_response', agent_name);
          }
        } else if (type === 'agent_response') {
          // If we were already streaming this response, update it with the final content instead of adding a duplicate
          if (lastMsg && lastMsg.role === 'assistant' && lastMsg.agentName === agent_name && (lastMsg.type === 'agent_response' || lastMsg.type === 'content_chunk')) {
            updateLastMessage(targetChatId, content, 'agent_response', false);
          } else {
            addMessage(targetChatId, 'assistant', content, 'agent_response', agent_name);
          }
        } else if (type === 'tool_output') {
          addMessage(targetChatId, 'assistant', content, 'tool_output', agent_name);
        } else if (type === 'status') {
          // Only update if the last message is already a status message, otherwise add a new one
          if (lastMsg && lastMsg.type === 'status') {
            updateLastMessage(targetChatId, content, 'status', false);
          } else {
            addMessage(targetChatId, 'assistant', content, 'status', agent_name);
          }
        } else {
          addMessage(targetChatId, 'assistant', content, type, agent_name);
        }
        
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
    get().setIsTyping(activeChatId, true);

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
      history: history,
      base_directory: currentChat?.baseDirectory,
      chat_mode: get().chatMode
    };

      socket.send(JSON.stringify(payload));
    } catch (error) {
        console.error("Failed to send message:", error);
        addMessage(activeChatId, 'assistant', "Error: Failed to send message.", 'error');
    }
  },

  cancelExecution: () => {
    const { socket, activeChatId, setIsTyping } = get();
    if (socket && socket.readyState === WebSocket.OPEN && activeChatId) {
      socket.send(JSON.stringify({
        action: 'cancel',
        session_id: activeChatId
      }));
      setIsTyping(activeChatId, false);
      toast.success("Cancellation requested...");
    } else {
        toast.error("Cannot cancel: socket not connected.");
    }
  }
}));
