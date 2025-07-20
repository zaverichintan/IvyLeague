import React from 'react';
import { EyeIcon } from './icons/dashbaord.icon';
import useChatStore from './store/chatstore';

const Alert: React.FC = () => {
  const { alerts, setAlerts } = useChatStore();

  const getAlertStyles = (type: string) => {
    switch (type) {
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto max-h-full overflow-hidden">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
        <button
          onClick={() => setAlerts(alerts.map(alert => ({ ...alert, read: true })))}
          className="text-sm cursor-pointer border border-gray-300 rounded-md p-1 hover:bg-gray-100"
        >
          Mark all as read
        </button>
      </div>

      <div className="space-y-4">
        {alerts.map(alert => (
          <div
            key={alert.id}
            className={`border rounded-lg p-4 ${getAlertStyles('error')} ${
              !alert.is_seen ? 'border-l-4' : ''
            }`}
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold">
                  New alert for transaction : {alert.transaction_id}
                </h3>
                <p className="whitespace-pre-wrap mt-1 text-sm opacity-90">{alert.summary}</p>
                <p className="mt-2 text-xs opacity-75 text-gray-800">{new Date(alert.timestamp).toLocaleString()}</p>
              </div>
              <div className="flex space-x-2">
                {!alert.is_seen && (
                  <button
                    onClick={() => setAlerts(alerts.map(alert => ({ ...alert, is_seen: true })))}
                    className="text-sm text-gray-700 border cursor-pointer border-gray-300 rounded-md p-1 hover:bg-gray-100"
                    style={{ textDecoration: 'underline' }}
                  >
                    <EyeIcon className="w-4 h-4 text-gray-700 hover:text-gray-900" />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}

        {alerts.length === 0 && (
          <div className="text-center py-12 text-gray-500">No notifications to display</div>
        )}
      </div>
    </div>
  );
};

export default Alert;
