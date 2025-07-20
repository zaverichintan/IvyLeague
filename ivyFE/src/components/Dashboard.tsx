
const Dashboard = () => {
  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Compact Stats Bar */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center space-x-3 bg-slate-100 rounded-lg p-2">
            <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-medium">📊</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Total Queries</p>
              <p className="text-lg font-semibold text-gray-900">1,234</p>
            </div>
          </div>

          <div className="flex items-center space-x-3 bg-slate-100 rounded-lg p-2">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-xl font-medium">✅</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Successful</p>
              <p className="text-lg font-semibold text-gray-900">1,180</p>
            </div>
          </div>

          <div className="flex items-center space-x-3 bg-slate-100 rounded-lg p-2">
            <div className="w-10 h-10 bg-primary-400 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-medium">⏱️</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Avg Response</p>
              <p className="text-lg font-semibold text-gray-900">245ms</p>
            </div>
          </div>

          <div className="flex items-center space-x-3 bg-slate-100 rounded-lg p-2">
            <div className="w-10 h-10 bg-primary-700 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-medium">📈</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Data Points</p>
              <p className="text-lg font-semibold text-gray-900">45.2K</p>
            </div>
          </div>
        </div>
      </div>

      {/* Full-height iframe */}
      <div className="flex-1 bg-white">
        <iframe
          src="https://monit-grafana-open.cern.ch/d/XoND3VQ4k/nkn?orgId=16&from=now-24h&to=now&timezone=browser&var-source=raw&var-bin=5m&kiosk&theme=light"
          width="100%"
          height="100%"
          className="border-0"
          title="System Monitoring Dashboard"
        ></iframe>
      </div>
    </div>
  );
};

export default Dashboard;
