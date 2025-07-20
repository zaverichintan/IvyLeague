
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
          src="http://10.143.44.26:13000/grafana/public-dashboards/8e2a16673e7746cba98141ac367fbb58?orgId=1&from=2025-07-20T04:43:04.547Z&to=2025-07-20T10:43:04.547Z&timezone=browser&theme=light"
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
