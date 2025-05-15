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
      // Only include data points that have valid values for the selected metrics
      const formattedChartData = chartData
        .filter(point => {
          // Check if any of the selected metrics have valid values
          return selectedMetrics.some(metric => 
            point[metric] !== null && point[metric] !== undefined
          );
        })
        .map(point => {
          const formattedPoint: Record<string, any> = {
            name: point.date || point.name
          };
          selectedMetrics.forEach(metric => {
            if (point[metric] !== null && point[metric] !== undefined) {
              formattedPoint[metric] = point[metric];
            }
          });
          return formattedPoint;
        });

      // Early validation
      if (!company) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Please select a company first to analyze the data.'
        }]);
        return;
      }

      if (!selectedMetrics?.length) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Please select at least one metric to analyze.'
        }]);
        return;
      }

      if (!formattedChartData.length) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `No valid data available for ${company} with the selected metrics.`
        }]);
        return;
      }

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
