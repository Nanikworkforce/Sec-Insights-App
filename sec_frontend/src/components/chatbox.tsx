import React, { useState, useEffect } from 'react';

interface ChatboxProps {
  chartData: any[];
  searchValue: string;
  selectedPeriod: string;
  selectedMetrics: string[];
  activeChart: string;
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

    const company = searchValue?.split(':')[0]?.trim()?.toUpperCase() || '';
    
    // Add user message
    const userMessage: Message = {
      role: 'user',
      content: message
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // Format chart data to ensure it has the correct structure
      const formattedChartData = chartData.map(point => {
        const formattedPoint: Record<string, any> = {
          name: point.date || point.name
        };
        // Only include selected metrics
        selectedMetrics.forEach(metric => {
          if (point[metric] !== undefined) {
            formattedPoint[metric] = point[metric];
          }
        });
        return formattedPoint;
      }).filter(point => Object.keys(point).length > 1); // Ensure point has more than just name

      // Log the request data
      console.log('Sending request:', {
        company,
        metrics: selectedMetrics,
        chartData: formattedChartData
      });

      const response = await fetch(`${BASE_URL}/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: message,
          company,
          period: selectedPeriod || '',
          metrics: selectedMetrics || [],
          chartType: activeChart || 'line',
          chartData: formattedChartData
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // If no company is selected, provide a specific message
      if (!company) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Please select a company first to analyze the data.'
        }]);
        return;
      }

      // If no metrics are selected, provide a specific message
      if (!selectedMetrics?.length) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Please select at least one metric to analyze.'
        }]);
        return;
      }

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
