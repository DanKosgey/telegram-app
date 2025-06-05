import React, { useState, useEffect } from 'react';
import './App.css';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement,
} from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';
import { format, parseISO } from 'date-fns';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  PointElement,
  LineElement
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [message, setMessage] = useState('');
  const [groupName, setGroupName] = useState('Manual Input');
  const [signals, setSignals] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Sample forex messages for testing
  const sampleMessages = [
    "🔔 EURUSD BUY 1.0945 TP1=1.0980 TP2=1.1000 TP3=1.1020 SL=1.0920",
    "📈 GBPJPY SELL ZONE 185.50-186.00 TP1: 184.80 TP2: 184.20 TP3: 183.50 SL: 186.80",
    "⚡ XAUUSD BUY NOW @ 2025.50 🎯 TP1: 2030.00 🎯 TP2: 2035.00 🎯 TP3: 2040.00 ❌ SL: 2020.00",
    "🔥 USDJPY SELL 148.25 Take Profit 1: 147.80 Take Profit 2: 147.30 Take Profit 3: 146.80 Stop Loss: 149.00"
  ];

  useEffect(() => {
    fetchSignals();
    fetchAnalytics();
  }, []);

  const fetchSignals = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/signals`);
      const data = await response.json();
      setSignals(data.signals || []);
    } catch (error) {
      console.error('Error fetching signals:', error);
    }
  };

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/analytics`);
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
    setLoading(false);
  };

  const extractSignal = async () => {
    if (!message.trim()) return;
    
    setExtracting(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/extract-signal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message.trim(),
          group_name: groupName
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        setMessage('');
        await fetchSignals();
        await fetchAnalytics();
      } else {
        alert(result.message || 'No valid signal found');
      }
    } catch (error) {
      console.error('Error extracting signal:', error);
      alert('Error extracting signal');
    }
    setExtracting(false);
  };

  const clearAllSignals = async () => {
    if (window.confirm('Are you sure you want to clear all signals?')) {
      try {
        await fetch(`${BACKEND_URL}/api/signals`, { method: 'DELETE' });
        await fetchSignals();
        await fetchAnalytics();
      } catch (error) {
        console.error('Error clearing signals:', error);
      }
    }
  };

  const deleteSignal = async (signalId) => {
    try {
      await fetch(`${BACKEND_URL}/api/signals/${signalId}`, { method: 'DELETE' });
      await fetchSignals();
      await fetchAnalytics();
    } catch (error) {
      console.error('Error deleting signal:', error);
    }
  };

  const exportData = async (format) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/export/${format}`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `forex_signals.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(`Error exporting ${format}:`, error);
      alert(`Error exporting ${format}`);
    }
  };

  const useSampleMessage = (sampleMsg) => {
    setMessage(sampleMsg);
  };

  // Chart configurations
  const symbolsChartData = analytics ? {
    labels: Object.keys(analytics.symbols_breakdown),
    datasets: [
      {
        label: 'Signals Count',
        data: Object.values(analytics.symbols_breakdown),
        backgroundColor: [
          '#3B82F6', '#10B981', '#F59E0B', '#EF4444', 
          '#8B5CF6', '#06B6D4', '#84CC16', '#F97316'
        ],
        borderWidth: 1,
      },
    ],
  } : null;

  const sentimentChartData = analytics ? {
    labels: Object.keys(analytics.sentiment_breakdown),
    datasets: [
      {
        data: Object.values(analytics.sentiment_breakdown),
        backgroundColor: ['#10B981', '#EF4444', '#6B7280'],
        borderWidth: 2,
      },
    ],
  } : null;

  const dailyChartData = analytics ? {
    labels: Object.keys(analytics.daily_breakdown).sort(),
    datasets: [
      {
        label: 'Daily Signals',
        data: Object.keys(analytics.daily_breakdown)
          .sort()
          .map(date => analytics.daily_breakdown[date]),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
      },
    ],
  } : null;

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
    },
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🚀 Advanced Forex Signal Analyzer
          </h1>
          <p className="text-gray-600 text-lg">
            AI-Powered Signal Extraction • Advanced Analytics • Export & Tracking
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-lg p-1 shadow-md">
            {['dashboard', 'extract', 'analytics', 'signals'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-2 rounded-md font-medium capitalize transition-colors ${
                  activeTab === tab
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:text-blue-600 hover:bg-gray-50'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && analytics && (
          <div className="space-y-8">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
              <div className="bg-white rounded-xl shadow-md p-6 text-center">
                <div className="text-3xl font-bold text-blue-600">{analytics.total_signals}</div>
                <div className="text-gray-600">Total Signals</div>
              </div>
              <div className="bg-white rounded-xl shadow-md p-6 text-center">
                <div className="text-3xl font-bold text-green-600">{analytics.buy_signals}</div>
                <div className="text-gray-600">Buy Signals</div>
              </div>
              <div className="bg-white rounded-xl shadow-md p-6 text-center">
                <div className="text-3xl font-bold text-red-600">{analytics.sell_signals}</div>
                <div className="text-gray-600">Sell Signals</div>
              </div>
              <div className="bg-white rounded-xl shadow-md p-6 text-center">
                <div className="text-3xl font-bold text-purple-600">
                  {analytics.avg_quality_score ? (analytics.avg_quality_score * 100).toFixed(0) + '%' : 'N/A'}
                </div>
                <div className="text-gray-600">Avg Quality</div>
              </div>
              <div className="bg-white rounded-xl shadow-md p-6 text-center">
                <div className="text-3xl font-bold text-orange-600">
                  {analytics.avg_tp_sl_ratio ? analytics.avg_tp_sl_ratio.toFixed(2) : 'N/A'}
                </div>
                <div className="text-gray-600">TP/SL Ratio</div>
              </div>
            </div>

            {/* Export Buttons */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">📊 Export Data</h3>
              <div className="flex gap-4">
                <button
                  onClick={() => exportData('csv')}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  📄 Export CSV
                </button>
                <button
                  onClick={() => exportData('json')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  📋 Export JSON
                </button>
                <button
                  onClick={clearAllSignals}
                  className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  🗑️ Clear All
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Extract Tab */}
        {activeTab === 'extract' && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">📝 Extract Signal</h2>
            
            {/* Sample Messages */}
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Try these sample messages:</p>
              <div className="flex flex-wrap gap-2">
                {sampleMessages.map((sample, index) => (
                  <button
                    key={index}
                    onClick={() => useSampleMessage(sample)}
                    className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-lg transition-colors"
                  >
                    Sample {index + 1}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Group Name
                </label>
                <input
                  type="text"
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter group name..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Trading Message
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="4"
                  placeholder="Paste your forex trading message here..."
                />
              </div>
              
              <button
                onClick={extractSignal}
                disabled={extracting || !message.trim()}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                {extracting ? '🔄 Extracting...' : '🚀 Extract Signal'}
              </button>
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && analytics && (
          <div className="space-y-8">
            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Symbols Distribution */}
              {symbolsChartData && (
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-4">📈 Symbols Distribution</h3>
                  <Bar data={symbolsChartData} options={chartOptions} />
                </div>
              )}

              {/* Sentiment Analysis */}
              {sentimentChartData && (
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-4">🎯 Market Sentiment</h3>
                  <Pie data={sentimentChartData} options={chartOptions} />
                </div>
              )}
            </div>

            {/* Daily Activity */}
            {dailyChartData && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">📅 Daily Signal Activity</h3>
                <Line data={dailyChartData} options={chartOptions} />
              </div>
            )}

            {/* Performance Metrics */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">⚡ Performance Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {analytics.performance_metrics.total_symbols}
                  </div>
                  <div className="text-sm text-gray-600">Total Symbols</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {analytics.performance_metrics.signals_per_day.toFixed(1)}
                  </div>
                  <div className="text-sm text-gray-600">Signals/Day</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {analytics.performance_metrics.buy_sell_ratio.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-600">Buy/Sell Ratio</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {analytics.performance_metrics.avg_risk_reward ? 
                      analytics.performance_metrics.avg_risk_reward.toFixed(2) : 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Avg Risk/Reward</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Signals Tab */}
        {activeTab === 'signals' && (
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-800">📊 Extracted Signals</h2>
            </div>
            
            {signals.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-6xl mb-4">📭</div>
                <p className="text-xl">No signals extracted yet</p>
                <p className="text-sm">Go to Extract tab to add signals</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Symbol
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Entry
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        TP Levels
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        SL
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quality
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sentiment
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        R/R
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {signals.map((signal) => (
                      <tr key={signal.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {signal.symbol}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                            signal.action === 'BUY' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {signal.action}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {signal.entry || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {[signal.tp1, signal.tp2, signal.tp3].filter(Boolean).join(' / ') || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {signal.sl || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {signal.quality_score ? 
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              signal.quality_score > 0.8 ? 'bg-green-100 text-green-800' :
                              signal.quality_score > 0.6 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {(signal.quality_score * 100).toFixed(0)}%
                            </span>
                            : 'N/A'
                          }
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {signal.sentiment ? 
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              signal.sentiment === 'BULLISH' ? 'bg-green-100 text-green-800' :
                              signal.sentiment === 'BEARISH' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {signal.sentiment}
                            </span>
                            : 'N/A'
                          }
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {signal.risk_reward_ratio ? signal.risk_reward_ratio.toFixed(2) : 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <button
                            onClick={() => deleteSignal(signal.id)}
                            className="text-red-600 hover:text-red-900 text-sm"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;