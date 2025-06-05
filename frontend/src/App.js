import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [message, setMessage] = useState('');
  const [groupName, setGroupName] = useState('Manual Input');
  const [signals, setSignals] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);

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

  const useSampleMessage = (sampleMsg) => {
    setMessage(sampleMsg);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🔍 Forex Signal Extractor
          </h1>
          <p className="text-gray-600 text-lg">
            Powered by Google Gemini AI • Extract structured signals from trading messages
          </p>
        </div>

        {/* Analytics Dashboard */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
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
                {analytics.avg_tp_sl_ratio ? analytics.avg_tp_sl_ratio.toFixed(2) : 'N/A'}
              </div>
              <div className="text-gray-600">Avg TP/SL Ratio</div>
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
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
            
            <div className="flex gap-3">
              <button
                onClick={extractSignal}
                disabled={extracting || !message.trim()}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                {extracting ? '🔄 Extracting...' : '🚀 Extract Signal'}
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

        {/* Signals Table */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800">📊 Extracted Signals</h2>
          </div>
          
          {signals.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-xl">No signals extracted yet</p>
              <p className="text-sm">Try extracting a signal from a trading message above</p>
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
                      TP1/TP2/TP3
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      SL
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Group
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Confidence
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
                        {signal.group_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {signal.confidence ? `${(signal.confidence * 100).toFixed(0)}%` : 'N/A'}
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

        {/* Symbol Distribution */}
        {analytics && Object.keys(analytics.symbols_breakdown).length > 0 && (
          <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">📈 Symbol Distribution</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(analytics.symbols_breakdown).map(([symbol, count]) => (
                <div key={symbol} className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-bold text-blue-600">{count}</div>
                  <div className="text-sm text-gray-600">{symbol}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;