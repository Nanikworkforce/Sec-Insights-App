import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

interface ChatboxProps {
  chartData: any[];
  searchValue: string;
  selectedPeriod: string;
  selectedMetrics: string[];
  activeChart: string;
  selectedCompanies: any[];
}

interface Message {
  role: 'assistant' | 'user';
  content: string;
}

const BASE_URL = 'http://127.0.0.1:8000/api';

export const useChat = ({
  chartData,
  searchValue,
  selectedPeriod,
  selectedMetrics,
  activeChart,
  selectedCompanies,
}: ChatboxProps) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'I can help you analyze this data. What would you like to know?'
    }
  ]);
  const [inputValue, setInputValue] = useState('');

  // Log context changes
  useEffect(() => {
    console.log('Chart Context:', {
      company: searchValue?.split(':')[0]?.trim() || '',
      metrics: selectedMetrics,
      period: selectedPeriod,
      chartType: activeChart
    });
  }, [searchValue, selectedMetrics, selectedPeriod, activeChart]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    // Determine company based on active chart
    const company = activeChart === 'peers' && selectedCompanies.length > 0
      ? selectedCompanies[0].ticker
      : searchValue.split(':')[0].trim().toUpperCase();

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: message
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const allChartData = chartData;

      // Use allChartData (full dataset) for chat, not just the displayed/filtered data
      const formattedChartData = allChartData
        .filter(point => {
          return selectedMetrics.some(metric => 
            point[metric] !== null && point[metric] !== undefined
          );
        })
        .map(point => {
          const formattedPoint: Record<string, any> = { name: point.date || point.name };
          selectedMetrics.forEach(metric => {
            if (point[metric] !== null && point[metric] !== undefined) {
              formattedPoint[metric] = point[metric];
            }
          });
          return formattedPoint;
        });

      // Prepare payload
      const getLatestYear = () => {
        // Try to find the latest year in your chart data
        const years = chartData
          .map(point => {
            // Try to extract year from date or name
            if (point.date) return parseInt(point.date);
            if (point.name) return parseInt(point.name);
            return null;
          })
          .filter(y => y && !isNaN(y));
        return years.length ? Math.max(...years) : new Date().getFullYear();
      };

      const getYearFromPeriod = (period: string) => {
        const latestYear = getLatestYear();
        if (!period) return null;
        if (period === '1Y') return latestYear;
        if (period === '2Y') return latestYear - 1;
        if (period === '3Y') return latestYear - 2;
        if (period === '4Y') return latestYear - 3;
        if (period === '5Y') return latestYear - 4;
        if (period === '10Y') return latestYear - 9;
        if (period === '15Y') return latestYear - 14;
        if (period === '20Y') return latestYear - 19;
        return null;
      };

      const payload = {
        company: company,
        metric_name: selectedMetrics, // Pass all selected metrics
        year: getYearFromPeriod(selectedPeriod), // Convert period to numeric year
        companies: selectedCompanies.map(c => c.ticker) // Pass all selected companies
      };

      const response = await fetch(`${BASE_URL}/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: message,
          payload: payload, // Pass the payload
          company,
          period: selectedPeriod || 'ALL',
          metrics: selectedMetrics || [],
          chartType: activeChart || 'line',
          chartData: formattedChartData
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const aiMessage: Message = {
        role: 'assistant',
        content: data.answer || data.error || 'No response from server'
      };
      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return {
    messages,
    inputValue,
    setInputValue,
    handleSendMessage
  };
};

export default useChat;

const NewsComponent = ({ newsContent }) => {
  return (
    <div>
      <ReactMarkdown
        components={{
          a: ({ node, ...props }) => (
            <a 
              {...props} 
              style={{ 
                color: '#007bff',  // Blue color
                textDecoration: 'none',
                cursor: 'pointer' 
              }}
              target="_blank" 
              rel="noopener noreferrer"
            />
          )
        }}
      >
        {newsContent}
      </ReactMarkdown>
    </div>
  );
};
