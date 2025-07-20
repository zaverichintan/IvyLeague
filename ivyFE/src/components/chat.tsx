import React, { useState, useRef, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import useChatStore from './store/chatstore';
import { LoadingIcon, SendIcon } from './icons/dashbaord.icon';
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface DataRow {
  [key: string]: string | number | boolean | null;
}

interface LooseObject {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

interface MessageApiResponse {
  success: boolean;
  query: string;
  explanation: string;
  sql_query: string;
  data: DataRow[];
  summary: string;
  insights: string[];
  recommendation: string | null;
  execution_time_ms: number;
  record_count: number;
  chat_id?: string;
}

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  query?: string;
  response?: MessageApiResponse;
  loading?: boolean;
}

const ChatBot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { chats, setChats } = useChatStore();
  const { chat_id } = useParams();

  const data = [
    {
      name: 'Page A',
      uv: 4000,
      pv: 2400,
      amt: 2400,
    },
    {
      name: 'Page B',
      uv: 3000,
      pv: 1398,
      amt: 2210,
    },
    {
      name: 'Page C',
      uv: 2000,
      pv: 9800,
      amt: 2290,
    },
    {
      name: 'Page D',
      uv: 2780,
      pv: 3908,
      amt: 2000,
    },
    {
      name: 'Page E',
      uv: 1890,
      pv: 4800,
      amt: 2181,
    },
    {
      name: 'Page F',
      uv: 2390,
      pv: 3800,
      amt: 2500,
    },
    {
      name: 'Page G',
      uv: 3490,
      pv: 4300,
      amt: 2100,
    },
  ];

  const fetchChat = async (chat_id: string) => {
    const response = await fetch(`http://localhost:8001/chats/${chat_id}/history`);
    if (response.ok) {
      const data = await response.json();
      const msgs: Message[] = [];
      data.data.messages.forEach((msg: Message) => {
        const response = JSON.parse((msg.response as unknown as string) || '{}');

        msgs.push({
          id: msg.id + 'query',
          type: 'user',
          content: msg.query || '',
          timestamp: new Date(msg.timestamp),
        });
        msgs.push({
          id: msg.id + 'response',
          type: 'bot',
          content: response.summary || '',
          response: response,
          timestamp: new Date(msg.timestamp),
        });
      });
      setMessages(msgs);
    } else {
      console.error('Failed to fetch chat');
    }
  };

  useEffect(() => {
    if (chat_id) {
      fetchChat(chat_id);
    } else {
      setMessages([]);
    }
  }, [chat_id]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendQuery = async (query: string) => {
    if (!query.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: query,
      timestamp: new Date(),
    };

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'bot',
      content: '',
      timestamp: new Date(),
      loading: true,
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      let payload: LooseObject = { query };
      if (chat_id) {
        payload = { ...payload, chat_id, chat_type: 'existing' };
      } else {
        payload = { ...payload, chat_type: 'new' };
      }
      const response = await fetch('http://localhost:8001/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const data: MessageApiResponse = await response.json();

      if (payload.chat_type === 'new' && data.chat_id) {
        window.history.replaceState(null, '', `/chat/${data.chat_id}`);
        setChats([
          {
            id: data.chat_id,
            query: query,
            chat_id: data.chat_id,
            timestamp: new Date().toISOString(),
          },
          ...chats,
        ]);
      }

      setMessages(prev =>
        prev.map(msg =>
          msg.id === loadingMessage.id
            ? { ...msg, content: data.summary, response: data, loading: false }
            : msg
        )
      );
    } catch (error) {
      setMessages(prev =>
        prev.map(msg =>
          msg.id === loadingMessage.id
            ? {
                ...msg,
                content:
                  'Sorry, I encountered an error while processing your request. Please try again.',
                loading: false,
              }
            : msg
        )
      );
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendQuery(inputValue);
  };

  const formatData = (data: DataRow[]) => {
    if (!data || data.length === 0) return null;

    // Get all unique column names
    const columns = Array.from(new Set(data.flatMap(row => Object.keys(row))));

    // Convert snake_case to sentence case
    const toSentenceCase = (str: string) => {
      return str
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');
    };

    return (
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <h4 className="bg-slate-50 text-slate-800 px-4 py-3 m-0 text-sm font-semibold uppercase tracking-wide border-b border-slate-200">
          📊 Results
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-slate-200">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                {columns.map(column => (
                  <th
                    key={column}
                    className="px-3 py-2 text-left font-semibold text-slate-700 border-r border-slate-200 last:border-r-0"
                  >
                    {toSentenceCase(column)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr
                  key={index}
                  className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50"
                >
                  {columns.map(column => (
                    <td
                      key={column}
                      className="px-3 py-2 text-slate-600 border-r border-slate-200 last:border-r-0"
                    >
                      {row[column] !== null && row[column] !== undefined
                        ? String(row[column])
                        : '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  console.log(messages);

  return (
    <div className="w-full h-full flex flex-col overflow-hidden">
      {/* Messages Container */}
      <div className="flex-1 w-full max-h-full overflow-y-auto">
        <div className="h-full overflow-y-auto p-5 text-sm flex flex-col gap-4 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-slate-100">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-center">
              <div className="max-w-md">
                <h2 className="text-slate-800 text-2xl font-semibold mb-4">👋 Welcome!</h2>
                <p className="text-slate-600 text-base mb-8 leading-relaxed">
                  I'm here to help you query and analyze your data. Try asking something like:
                </p>
                <div className="flex flex-col gap-3">
                  <button
                    className="bg-gradient-to-r from-purple-600 to-purple-600 text-white border-none px-5 py-3 rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-purple-500/30"
                    onClick={() => sendQuery('Show me count of failed transactions')}
                  >
                    "Show me count of failed transactions"
                  </button>
                  <button
                    className="bg-gradient-to-r from-purple-600 to-purple-600 text-white border-none px-5 py-3 rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-purple-500/30"
                    onClick={() => sendQuery('What are the top 10 transactions by amount?')}
                  >
                    "What are the top 10 transactions by amount?"
                  </button>
                  <button
                    className="bg-gradient-to-r from-purple-600 to-purple-600 text-white border-none px-5 py-3 rounded-xl cursor-pointer text-sm font-medium transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-purple-500/30"
                    onClick={() => sendQuery('Show me transaction trends over time')}
                  >
                    "Show me transaction trends over time"
                  </button>
                </div>
              </div>
            </div>
          )}

          {messages.map(message => (
            <div
              key={message.id}
              className={`flex flex-col mb-4 ${
                message.type === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              {message.type === 'user' ? (
                <div className="max-w-[70%]">
                  <div className="bg-purple-50  border border-purple-200 text-purple-500 font-medium px-5 py-4 rounded-lg rounded-br-md mb-1 shadow-lg">
                    <p className="m-0 leading-relaxed">{message.content}</p>
                  </div>
                  <div className="text-xs text-slate-500 float-right px-2">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              ) : (
                <div className="max-w-[90%]">
                  {message.loading ? (
                    <div className="bg-slate-50 border border-slate-200 p-5 rounded-3xl rounded-bl-md flex items-center gap-3">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-purple-600 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-2 h-2 bg-purple-600 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-2 h-2 bg-purple-600 rounded-full animate-bounce"></span>
                      </div>
                      <p className="m-0">Analyzing your query...</p>
                    </div>
                  ) : (
                    <div className="bg-white border border-slate-200 p-6 rounded-3xl rounded-bl-md shadow-lg">
                      {message.content && (
                        <div className="mb-5 pb-4 border-b border-slate-200">
                          <h3 className="text-slate-800 text-lg font-semibold mb-2">📋 Summary</h3>
                          <p className="text-slate-700 leading-relaxed text-base m-0">
                            {message.content}
                          </p>
                        </div>
                      )}

                      {message.response && (
                        <div className="flex flex-col gap-5">
                          {message.response.explanation && (
                            <div className="bg-white p-4 rounded-xl border border-slate-200">
                              <h4 className="text-slate-800 text-sm font-semibold mb-3 uppercase tracking-wide">
                                💡 Explanation
                              </h4>
                              <p className="text-slate-700 leading-relaxed m-0">
                                {message.response.explanation}
                              </p>
                            </div>
                          )}

                          {message.response.sql_query && (
                            <div className="bg-white p-4 rounded-xl border border-slate-200">
                              <h4 className="text-slate-800 text-sm font-semibold mb-3 uppercase tracking-wide">
                                🔍 SQL Query
                              </h4>
                              <pre className="bg-slate-800 text-slate-200 p-4 rounded-lg font-mono text-sm leading-relaxed overflow-x-auto whitespace-pre-wrap break-all">
                                {message.response.sql_query}
                              </pre>
                            </div>
                          )}

                          {formatData(message.response.data)}

                          {message.response.insights && message.response.insights.length > 0 && (
                            <div className="bg-white p-4 rounded-xl border border-slate-200">
                              <h4 className="text-slate-800 text-sm font-semibold mb-3 uppercase tracking-wide">
                                🎯 Insights
                              </h4>
                              {/*    <div className="flex flex-col gap-4 py-6 justify-center items-center">
                              <ResponsiveContainer width={'100%'} height={300}>
                                  <BarChart
                                    width={500}
                                    height={300}
                                    data={data}
                                    margin={{ top: 0, left: 0, right: 0, bottom: 0 }}
                                  >
                                    <XAxis type="category" stroke="#6e6e6e" dataKey="name" />
                                    <YAxis type="number" stroke="#6e6e6e" dataKey="uv" />
                                    <Tooltip cursor={{ fill: '#f1f1f1' }} />
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <Bar
                                      radius={[3, 3, 0, 0]}
                                      dataKey="uv"
                                      barSize={60}
                                      fill="#f3e8ff"
                                      stroke="#ad46ff"
                                    />
                                  </BarChart>
                                </ResponsiveContainer> 
                              </div>*/}
                              <ul className="list-none p-0 m-0">
                                {message.response.insights.map((insight, index) => (
                                  <li
                                    key={index}
                                    className="bg-sky-50 border-l-4 border-sky-500 p-3 mb-2 last:mb-0 rounded-r-lg text-sky-900 leading-relaxed"
                                  >
                                    {insight}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {message.response.recommendation && (
                            <div className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-300 p-4 rounded-xl">
                              <h4 className="text-amber-800 text-sm font-semibold mb-3 uppercase tracking-wide">
                                💡 Recommendation
                              </h4>
                              <p className="text-amber-900 font-medium leading-relaxed m-0">
                                {message.response.recommendation}
                              </p>
                            </div>
                          )}

                          <div className="flex flex-wrap gap-5 mt-4 pt-4 border-t border-slate-200 text-xs text-slate-500">
                            <span className="flex items-center gap-1 font-medium">
                              ⚡ Execution: {message.response.execution_time_ms}ms
                            </span>
                            <span className="flex items-center gap-1 font-medium">
                              📄 Records: {message.response.record_count}
                            </span>
                          </div>
                        </div>
                      )}

                      <div className="text-xs text-slate-500 px-2 mt-3">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>
      <form className="p-5 border-t border-slate-200 bg-white" onSubmit={handleSubmit}>
        <div className="flex gap-3 items-center">
          <input
            type="text"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            placeholder="Ask me about your data..."
            disabled={isLoading}
            className="flex-1 px-5 py-4 border-1 border-slate-200 rounded-xl text-base outline-none transition-all duration-200 bg-slate-50 focus:border-purple-600 focus:bg-white focus:shadow-lg focus:shadow-purple-500/10 disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="w-fit h-max rounded-xl border-none bg-purple-600 p-3 text-white cursor-pointer grid place-items-center hover:scale-105 hover:shadow-lg hover:shadow-purple-500/30 disabled:bg-slate-300 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
          >
            {isLoading ? <LoadingIcon className="w-4 h-4" /> : <SendIcon className="w-7 h-7" />}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatBot;
