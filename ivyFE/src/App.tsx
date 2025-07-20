import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import ChatBot from './components/chat';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Alert from './components/Alert';

const App = () => {
  return (
    <Router>
      <div className="flex flex-col h-screen max-h-screen overflow-hidden bg-gray-50">
        <Navbar />
        <div className="flex flex-1 h-full max-h-full overflow-hidden">
          <Sidebar />

          <main className="max-h-full overflow-hidden w-full">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/chat/new" element={<ChatBot />} />
              <Route path="/chat/:chat_id" element={<ChatBot />} />
              <Route path="/alerts" element={<Alert />} />
              <Route
                path="/analytics"
                element={
                  <div className="p-8">
                    <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
                    <p className="mt-2 text-gray-600">Analytics page coming soon...</p>
                  </div>
                }
              />
              <Route
                path="/settings"
                element={
                  <div className="p-8">
                    <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
                    <p className="mt-2 text-gray-600">Settings page coming soon...</p>
                  </div>
                }
              />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
};

export default App;
