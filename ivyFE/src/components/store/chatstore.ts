import { create } from 'zustand'

export interface Chat {
    id: string;
    query: string;
    chat_id?: string;
    timestamp?: string;
}

interface Alert {
    id: number;
    transaction_id: string;
    summary: string;
    is_seen: boolean;
    timestamp: string;
}

interface ChatStore {
    chats: Chat[];
    alerts: Alert[];
    setChats: (chats: Chat[]) => void;
    setAlerts: (alerts: Alert[]) => void;
}

const useChatStore = create<ChatStore>((set) => ({
    chats: [],
    alerts: [],
    setChats: (chats: Chat[]) => set({ chats }),
    setAlerts: (alerts: Alert[]) => set({ alerts }),
}));

export default useChatStore;
