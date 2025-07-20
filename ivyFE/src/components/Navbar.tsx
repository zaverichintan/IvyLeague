import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { UserIcon } from './icons/dashbaord.icon';
import useChatStore from './store/chatstore';

const Navbar: React.FC = () => {
  const { alerts, setAlerts } = useChatStore();

  const fetchAlerts = async () => {
    try {
      const response = await fetch('http://localhost:8001/transactions/alerts');
      if (response.ok) {
        const data = await response.json();
        // Assuming the API returns an array of alerts or an object with an alerts array
        const alerts = Array.isArray(data) ? data : data.data || [];
        setAlerts(alerts);
      } else {
        console.error('Failed to fetch alerts');
      }
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  useEffect(() => {
    // Fetch alerts immediately on component mount
    fetchAlerts();

    // Set up polling every 30 seconds
    const intervalId = setInterval(fetchAlerts, 1000);

    // Cleanup interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  console.log(alerts);

  return (
    <nav className="bg-white border-b border-gray-200 h-16">
      <div className="flex items-center px-5 justify-between">
        <img
          className="w-32 h-auto"
          src="https://images.ctfassets.net/vx9l0f5sup17/Do1qdrKEH9PaVxHLIzvZ3/52547811d72764839660015fef551827/Ivy.svg"
          alt="logo"
        />
        <div className="flex items-center">
          <Link
            to="/alerts"
            className="relative w-6 h-6 bg-primary-500 text-gray-700 rounded-full flex items-center justify-center"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="100%"
              height="100%"
              fill="currentColor"
              viewBox="0 0 256 256"
            >
              <path d="M221.8,175.94C216.25,166.38,208,139.33,208,104a80,80,0,1,0-160,0c0,35.34-8.26,62.38-13.81,71.94A16,16,0,0,0,48,200H88.81a40,40,0,0,0,78.38,0H208a16,16,0,0,0,13.8-24.06ZM128,216a24,24,0,0,1-22.62-16h45.24A24,24,0,0,1,128,216ZM48,184c7.7-13.24,16-43.92,16-80a64,64,0,1,1,128,0c0,36.05,8.28,66.73,16,80Z"></path>
            </svg>
            {alerts.length > 0 && (
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                {alerts.length > 99 ? '99+' : alerts.length}
              </span>
            )}
          </Link>

          <div className="flex items-center text-gray-700 px-4 py-4 border-t border-gray-200">
            <div className="w-7 h-7 bg-primary-500 rounded-full flex items-center justify-center">
              <UserIcon />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
