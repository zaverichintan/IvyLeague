import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChatIcon, DashboardIcon, ReportsIcon, SettingsIcon } from './icons/dashbaord.icon';
import useChatStore from './store/chatstore';

const Sidebar: React.FC = () => {
  const location = useLocation();
  const [isChatsExpanded, setIsChatsExpanded] = useState(false);
  const { chats, setChats } = useChatStore();
  const [isLoadingChats, setIsLoadingChats] = useState(false);

  // Fetch chats on component mount
  useEffect(() => {
    if (location.pathname.startsWith('/chat')) {
      setIsChatsExpanded(true);
    }
    const fetchChats = async () => {
      setIsLoadingChats(true);
      try {
        const response = await fetch('http://localhost:8001/chats');
        if (response.ok) {
          const chatsData = await response.json();
          setChats(chatsData?.data?.chats || []);
        } else {
          console.error('Failed to fetch chats');
        }
      } catch (error) {
        console.error('Error fetching chats:', error);
      } finally {
        setIsLoadingChats(false);
      }
    };

    fetchChats();
  }, []);

  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: <DashboardIcon />,
      current: location.pathname === '/dashboard',
    },
    {
      name: 'Reports',
      href: '/reports',
      icon: <ReportsIcon />,
      current: location.pathname === '/reports',
    },
  ];

  return (
    <div className="flex flex-col w-[20vw] shrink-0 bg-white shadow-lg border-r border-gray-200 ">
      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1.5">
        <div className="space-y-2">
          {navigationItems.map(item => (
            <Link
              key={item.name}
              to={item.href}
              className={`group flex items-center px-3 py-2 text-sm font-medium rounded transition-colors duration-200 ${
                item.current
                  ? 'bg-purple-50 text-purple-700'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <span className="mr-3 w-6 h-6">{item.icon}</span>
              {item.name}
            </Link>
          ))}

          {/* Expandable Chat Section */}
          <div className="space-y-1">
            <button
              onClick={() => setIsChatsExpanded(!isChatsExpanded)}
              className={`group flex items-center justify-between w-full px-3 py-2 text-sm font-medium rounded transition-colors duration-200 ${
                location.pathname.startsWith('/chat')
                  ? 'bg-purple-50 text-purple-700'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <div className="flex items-center">
                <span className="mr-3 w-6 h-6">
                  <ChatIcon />
                </span>
                Chat
              </div>
              <svg
                className={`w-4 h-4 transition-transform duration-200 ${
                  isChatsExpanded ? 'rotate-90' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>

            {/* Chat List - Expanded */}
            {isChatsExpanded && (
              <div className="pl-3 space-y-1">
                {isLoadingChats ? (
                  <div className="flex items-center px-3 py-2 text-xs text-gray-500">
                    <svg className="animate-spin w-3 h-3 mr-2" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Loading chats...
                  </div>
                ) : chats.length > 0 ? (
                  <>
                    <Link
                      to="/chat/new"
                      className={`block px-3 py-2 text-sm font-medium rounded transition-colors duration-200 ${
                        location.pathname === '/chat/new'
                          ? 'bg-purple-50 text-purple-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      + New Chat
                    </Link>
                    {chats.map(chat => (
                      <Link
                        key={chat.chat_id}
                        to={`/chat/${chat.chat_id}`}
                        className={`block px-3 py-2 text-[14px] rounded-se transition-colors duration-200 ${
                          location.pathname === `/chat/${chat.chat_id}`
                            ? 'bg-purple-50 text-purple-700 border-l-2 font-medium border-purple-700'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 border-l-2 border-transparent'
                        }`}
                      >
                        <div className="truncate" title={chat.query}>
                          {chat.query || `Chat ${chat.chat_id}`}
                        </div>
                        {chat.timestamp && (
                          <div className="text-xs text-gray-400 mt-1">
                            {new Date(chat.timestamp).toLocaleDateString()}
                          </div>
                        )}
                      </Link>
                    ))}
                  </>
                ) : (
                  <Link
                    to="/chat"
                    className="block px-3 py-2 text-xs text-gray-500 hover:text-gray-700"
                  >
                    No chats yet. Start a new one!
                  </Link>
                )}
              </div>
            )}
          </div>
        </div>
      </nav>
      <div className="p-4">
        <Link
          key="Settings"
          to={'/settings'}
          className={`group flex items-center px-3 py-2 text-sm font-medium rounded transition-colors duration-200 ${
            location.pathname === '/settings'
              ? 'bg-purple-50 text-purple-700'
              : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
          }`}
        >
          <span className="mr-3 w-6 h-6">
            <SettingsIcon />
          </span>
          Settings
        </Link>
      </div>
    </div>
  );
};

export default Sidebar;
