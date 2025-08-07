import React, { useState, useEffect } from 'react';
import { Send, Brain, TrendingUp, AlertTriangle, Lightbulb } from 'lucide-react';
import axios from './axios';

export const AnalyticsPage = () => {
  const [query, setQuery] = useState('');
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);
  const [insights, setInsights] = useState([]);
  const [dataPreview, setDataPreview] = useState(null);

  useEffect(() => {
    // Load initial insights
    loadInitialInsights();
  }, []);

  const loadInitialInsights = async () => {
    try {
      const response = await axios.get('/api/data/preview?type=processed');
      if (response.data) {
        setDataPreview(response.data);
        
        // Generate initial insights
        const initialInsights = [
          "📊 You can ask me questions about your sales data",
          "🔍 Try asking: 'Show me top selling products'",
          "📈 Ask for charts: 'Create a bar chart of sales by product'",
          "💡 Get insights: 'What's the mapping rate?'"
        ];
        setInsights(initialInsights);
      }
    } catch (error) {
      console.log('No processed data available');
    }
  };

  const sendQuery = async () => {
    if (!query.trim()) return;

    const userMessage = { type: 'user', content: query, timestamp: new Date() };
    setConversation(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      // For now, simulate AI response
      // In a real implementation, you'd call your AI endpoint
      const aiResponse = await simulateAIResponse(query);
      
      const aiMessage = { 
        type: 'ai', 
        content: aiResponse.response, 
        chartData: aiResponse.chartData,
        timestamp: new Date() 
      };
      
      setConversation(prev => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = { 
        type: 'error', 
        content: 'Sorry, I encountered an error processing your query.', 
        timestamp: new Date() 
      };
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setQuery('');
    }
  };

  const simulateAIResponse = async (userQuery) => {
    // Simulate AI processing delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const queryLower = userQuery.toLowerCase();
    
    if (queryLower.includes('top') || queryLower.includes('best') || queryLower.includes('selling')) {
      return {
        response: "Based on your sales data, here are the top selling products:\n\n1. MSKU001 - 150 orders\n2. MSKU002 - 120 orders\n3. MSKU003 - 95 orders\n\nThese products represent 60% of your total sales volume.",
        chartData: {
          chart_type: 'bar',
          title: 'Top Selling Products'
        }
      };
    } else if (queryLower.includes('mapping') || queryLower.includes('rate')) {
      return {
        response: "Your current mapping rate is 85.2%. This means 85.2% of your SKUs have been successfully mapped to MSKUs. The remaining 14.8% (approximately 45 SKUs) need attention. Consider updating your mapping file to improve this rate.",
        chartData: {
          chart_type: 'pie',
          title: 'Mapping Status'
        }
      };
    } else if (queryLower.includes('chart') || queryLower.includes('graph') || queryLower.includes('visualize')) {
      return {
        response: "I've created a visualization for you. The chart shows the distribution of your sales data. You can see clear patterns in product performance and identify opportunities for optimization.",
        chartData: {
          chart_type: 'bar',
          title: 'Sales Distribution'
        }
      };
    } else {
      return {
        response: "I can help you analyze your warehouse data! Try asking me about:\n\n• Top selling products\n• Mapping rates and unmapped SKUs\n• Sales trends and patterns\n• Data quality issues\n• Performance metrics\n\nJust type your question in natural language!",
        chartData: null
      };
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendQuery();
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Analytics</h1>
        <p className="text-gray-600">Ask questions about your data in natural language</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Chat Interface */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-md">
            {/* Chat Header */}
            <div className="border-b border-gray-200 p-6">
              <div className="flex items-center">
                <Brain className="h-6 w-6 text-blue-600 mr-3" />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">AI Assistant</h2>
                  <p className="text-sm text-gray-600">Ask me anything about your warehouse data</p>
                </div>
              </div>
            </div>

            {/* Chat Messages */}
            <div className="h-96 overflow-y-auto p-6">
              {conversation.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <Brain className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>Start a conversation by asking about your data</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {conversation.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          message.type === 'user'
                            ? 'bg-blue-600 text-white'
                            : message.type === 'error'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{message.content}</p>
                        {message.chartData && (
                          <div className="mt-4 p-4 bg-white rounded border">
                            <h4 className="font-medium mb-2">{message.chartData.title}</h4>
                            <div className="h-48 bg-gray-50 rounded flex items-center justify-center">
                              <span className="text-gray-500">Chart would appear here</span>
                            </div>
                          </div>
                        )}
                        <p className="text-xs opacity-70 mt-2">
                          {message.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 text-gray-900 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                          <span>Thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-200 p-6">
              <div className="flex space-x-4">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about your data... (e.g., 'Show me top selling products')"
                  className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows="2"
                  disabled={loading}
                />
                <button
                  onClick={sendQuery}
                  disabled={!query.trim() || loading}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    !query.trim() || loading
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Insights */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <Lightbulb className="h-5 w-5 text-yellow-600 mr-2" />
              Quick Insights
            </h3>
            <div className="space-y-3">
              {insights.map((insight, index) => (
                <div key={index} className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3">
                  {insight}
                </div>
              ))}
            </div>
          </div>

          {/* Data Preview */}
          {dataPreview && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <TrendingUp className="h-5 w-5 text-green-600 mr-2" />
                Data Overview
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Records:</span>
                  <span className="font-medium">{dataPreview.total_rows}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Columns:</span>
                  <span className="font-medium">{dataPreview.columns.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Updated:</span>
                  <span className="font-medium">Today</span>
                </div>
              </div>
            </div>
          )}

          {/* Sample Queries */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4">Sample Queries</h3>
            <div className="space-y-2">
              {[
                "Show me top selling products",
                "What's the mapping rate?",
                "Create a chart of sales trends",
                "How many unmapped SKUs?",
                "Analyze data quality"
              ].map((sampleQuery, index) => (
                <button
                  key={index}
                  onClick={() => setQuery(sampleQuery)}
                  className="block w-full text-left text-sm text-blue-600 hover:text-blue-800 p-2 rounded hover:bg-blue-50 transition-colors"
                >
                  "{sampleQuery}"
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}; 