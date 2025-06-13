import React, { useState, useEffect, useCallback, useRef, useLayoutEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import BoxPlot from './BoxPlot';
import { useChat } from './chatbox';
import { TooltipProps } from 'recharts';
// const BASE_URL = import.meta.env.VITE_API_BASE_URL;
// import {baseUrl} from '../api';
import baseUrl from './api';
console.log("Using baseUrl:", baseUrl);

// const data = [
//   { date: 'Jan 16', revenue: 15000, cost: 8000 },
//   { date: 'Jul 16', revenue: 19000, cost: 8500 },
//   { date: 'Jan 17', revenue: 16500, cost: 9000 },
//   { date: 'Jul 17', revenue: 17500, cost: 9800 },
//   { date: 'Jan 18', revenue: 19000, cost: 8500 },
//   { date: 'Jul 18', revenue: 23000, cost: 9000 },
// ];

// const peersData = [
//   { date: 'Jan 16', apple: 15000, microsoft: 12000, google: 14000 },
//   { date: 'Jul 16', apple: 19000, microsoft: 15000, google: 18000 },
//   { date: 'Jan 17', apple: 16500, microsoft: 14500, google: 16000 },
//   { date: 'Jul 17', apple: 17500, microsoft: 16000, google: 19000 },
//   { date: 'Jan 18', apple: 19000, microsoft: 18000, google: 21000 },
//   { date: 'Jul 18', apple: 23000, microsoft: 20000, google: 24000 }, chat
// ];

// const industryData = [
//   { date: 'Jan 16', automotive: 12000, technology: 15000, healthcare: 13000 },
//   { date: 'Jul 16', automotive: 14000, technology: 18000, healthcare: 16000 },
//   { date: 'Jan 17', automotive: 13500, technology: 16500, healthcare: 15500 },
//   { date: 'Jul 17', automotive: 15500, technology: 19500, healthcare: 17500 },
//   { date: 'Jan 18', automotive: 16000, technology: 21000, healthcare: 19000 },
//   { date: 'Jul 18', automotive: 18000, technology: 24000, healthcare: 21000 },
// ];

// Define metric colors and interface
interface MetricConfig {
  color: string;
  label: string;
}

interface MetricConfigs {
  [key: string]: MetricConfig;
}

// Add this utility function at the top of the file
function generateColorPalette(count: number): string[] {
  const baseColors = [
    '#1B5A7D', '#4CAF50', '#FFC107', '#FF6B6B', '#4ECDC4', '#45B7D1', '#FF9F43', 
    '#EC3B83', '#8884d8', '#82ca9d', '#ffc658', '#ff7300'
  ];

  const colors = [...baseColors];
  
  // Generate additional colors if needed
  while (colors.length < count) {
    const h = (colors.length * 137.508) % 360; // Use golden angle approximation
    const s = 65 + (colors.length % 3) * 10; // Vary saturation between 65-85%
    const l = 45 + (colors.length % 5) * 5; // Vary lightness between 45-65%
    colors.push(`hsl(${h}, ${s}%, ${l}%)`);
  }

  return colors;
}

// Update the PeriodType to include all available periods
type PeriodType = '1Y' | '2Y' | '3Y' | '4Y' | '5Y' | '10Y' | '15Y' | '20Y';

// Add interface for peer data
interface PeerDataPoint {
  name: string;
  [key: string]: { [ticker: string]: number } | string; // Allow metric keys to store company values
}

// Update the selectedCompanies state to store ticker objects
interface CompanyTicker {
  ticker: string;
  name: string;
}

// First, add this interface for the chart data
interface ChartDataPoint {
  name: string;
  ticker: string;
  value: number | null;  // Allow null for value
  [key: string]: string | number | null;  // Allow null for dynamic metrics
}

// Add this interface near other interfaces
// interface StickyTooltip {
//   x: number;
//   y: number;
//   payload: any[];
// }

// Add these interfaces at the top of the file
// interface YourChartDataType {
//   [metric: string]: number[];
// }

// Update the activeTooltip interface
interface ActiveTooltip {
  x: number;
  y: number;
  payload: {
    [key: string]: any;
  };
  [key: string]: any;  // Add index signature for dynamic metric access
}

// Define a mapping of tickers to company names
// const tickerToCompanyNameMap = {
//   AAPL: 'Apple Inc.',
//   META: 'Meta Platforms',
//   A: 'Agilent Technologies',
//   AA: 'Alcoa Corporation',
//   // Add more mappings as needed
// };

// function getCompanyNameFromTicker(ticker: string): string | undefined {
//   return tickerToCompanyNameMap[ticker];
// }

// Add interface for data items
interface DataItem {
  name: string;
  value: number;
}

interface TimePoint {
  name: string;
  [key: string]: any;  // Add other properties as needed
}



const Dashboard: React.FC = () => {
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);
  const [activeChart, setActiveChart] = useState<'metrics' | 'peers' | 'industry'>('metrics');
  const [searchValue, setSearchValue] = useState('');
  const [selectedCompanies, setSelectedCompanies] = useState<CompanyTicker[]>([]);
  const [companyInput, setCompanyInput] = useState('');
  const [selectedPeerMetric, setSelectedPeerMetric] = useState<string>('');
  const [selectedSearchMetrics, setSelectedSearchMetrics] = useState<string[]>([]);
  const [searchMetricInput, setSearchMetricInput] = useState('');
  const [availableMetrics, setAvailableMetrics] = useState<{ value: string; label: string }[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metricColors, setMetricColors] = useState<MetricConfigs>({});
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodType>('1Y');
  const [peerChartData, setPeerChartData] = useState<PeerDataPoint[]>([]);
  const [peerLoading, setPeerLoading] = useState(false);
  const [peerError, setPeerError] = useState<string | null>(null);
  // const [selectedIndustryCompanies, setSelectedIndustryCompanies] = useState<CompanyTicker[]>([]);
  const [selectedIndustryMetrics, setSelectedIndustryMetrics] = useState<string[]>([]);
  const [industryMetricInput, setIndustryMetricInput] = useState('');
  const [industryChartData, setIndustryChartData] = useState<Record<string, (number | null)[]>>({});
  const [industryLoading, setIndustryLoading] = useState(false);
  const [industryError, setIndustryError] = useState<string | null>(null);
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const [availableIndustries, setAvailableIndustries] = useState<{ value: string; label: string; companies: string[] }[]>([]);
  const [industryCompanyNames, setIndustryCompanyNames] = useState<{ [metric: string]: string[] }>({});
  const [selectedTicker, setSelectedTicker] = useState('');
  const [showMetricDropdown, setShowMetricDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const industryDropdownRef = useRef<HTMLDivElement>(null);
  const [industrySearch, setIndustrySearch] = useState('');
  const [showIndustryDropdown, setShowIndustryDropdown] = useState(false);
  const [companySearch, setCompanySearch] = useState('');
  const [showCompanyDropdown, setShowCompanyDropdown] = useState(false);
  const companyDropdownRef = useRef<HTMLDivElement>(null);
  const [peerMetricSearch, setPeerMetricSearch] = useState('');
  const [showPeerMetricDropdown, setShowPeerMetricDropdown] = useState(false);
  const peerDropdownRef = useRef<HTMLDivElement>(null);
  const [activeTooltip, setActiveTooltip] = useState<ActiveTooltip | null>(null);
  const [fixed2024Data, setFixed2024Data] = useState<any>(null);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [fixedTooltipPos, setFixedTooltipPos] = useState<{ left: number, top: number } | null>(null);
  const [companyMap, setCompanyMap] = useState<{ [ticker: string]: string }>({});

  // Add these lines for peer metrics
  const [selectedPeerMetrics, setSelectedPeerMetrics] = useState<string[]>([]);

  const {
    messages,
    inputValue,
    setInputValue,
    handleSendMessage,
    setMessages
  } = useChat({
    chartData: activeChart === 'peers'
      ? peerChartData
      : activeChart === 'industry'
        ? Object.entries(industryChartData).map(([metric, values]) => ({
            metric,
            values
          }))
        : chartData,
    searchValue,
    selectedPeriod,
    selectedMetrics: activeChart === 'peers' ? selectedPeerMetrics : 
                 activeChart === 'industry' ? selectedIndustryMetrics : 
                 selectedSearchMetrics,
    activeChart,
    selectedCompanies
  });

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const response = await fetch(`${baseUrl}/api/companies/`);
        if (!response.ok) {
          throw new Error(`Failed to fetch companies: ${response.status}`);
        }
        const data = await response.json();

        const map: { [ticker: string]: string } = {};
        data.forEach((company: any) => {
          map[company.ticker] = company.display_name || company.name || company.ticker;
        });

        setCompanyMap(map);
      } catch (error) {
        console.error('Error fetching companies:', error);
      }
    };

    fetchCompanies();
  }, [baseUrl]);


  const fetchAvailableMetrics = async () => {
    try {
      const response = await fetch(`${baseUrl}/api/available-metrics/`);
      if (!response.ok) {
        throw new Error('Failed to fetch metrics');
      }
      const data = await response.json();
      console.log('Fetched metrics:', data);
      
      // Format metric names for display
      const formattedMetrics = data.metrics.map((metric: string) => ({
        value: metric,
        label: metric
          .replace(/([A-Z])/g, ' $1') // Add space before capital letters
          .replace(/^./, str => str.toUpperCase()) // Capitalize first letter
          .trim()
      }));
      
      setAvailableMetrics(formattedMetrics);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const fetchMetricData = useCallback(async () => {
    if (!searchValue || selectedSearchMetrics.length === 0) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const ticker = searchValue.split(':')[0].trim().toUpperCase();
      console.log('Fetching data for ticker:', ticker, 'period:', selectedPeriod);

      // Create array of time periods based on selectedPeriod
      let timePoints: string[] = [];
      if (selectedPeriod === '1Y') {
        // For annual data, use single years
        timePoints = Array.from({ length: 20 }, (_, i) => (2005 + i).toString());
      } else {
        // For multi-year periods, use predefined ranges
        switch (selectedPeriod) {
          case '2Y':
            timePoints = [
              '2005-06', '2007-08', '2009-10', '2011-12', '2013-14',
              '2015-16', '2017-18', '2019-20', '2021-22', '2023-24'
            ];
            break;
          case '3Y':
            timePoints = [
              '2007-09', '2010-12', '2013-15', '2016-18',
              '2019-21', '2022-24'
            ];
            break;
          case '4Y':
            timePoints = [
              '2005-08', '2009-12', '2013-16', '2017-20', '2021-24'
            ];
            break;
          case '5Y':
            timePoints = [
              '2005-09', '2010-14', '2015-19', '2020-24'
            ];
            break;
          case '10Y':
            timePoints = ['2005-14', '2015-24'];
            break;
          case '15Y':
            timePoints = ['2010-24'];
            break;
          case '20Y':
            timePoints = ['2005-24'];
            break;
        }
      }

      // First check if company exists
      const companyResponse = await fetch(`${baseUrl}/api/companies/${ticker}/`);
      if (!companyResponse.ok) {
        setError(`No data available for ${ticker}. Please try another company.`);
        setChartData([]);
        return;
      }

      // Fetch data for all selected metrics
      const promises = selectedSearchMetrics.map(async metric => {
        const url = `${baseUrl}/api/aggregated-data/?tickers=${ticker}&metric=${metric}&period=${selectedPeriod}`;
        console.log('Fetching from URL:', url);

        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Failed to fetch data for ${metric}`);
        }
        const data = await response.json();
        console.log(`Raw data for ${metric}:`, data);
        return { metric, data };
      });

      const results = await Promise.all(promises);
      console.log('All results:', results);

      if (results.every(result => result.data.length === 0)) {
        setError(`No data available for ${ticker} for the selected metrics and period.`);
        setChartData([]);
        return;
      }

      // Initialize data points for all time periods
      const baseData = timePoints.map(period => ({
        name: period,
        ticker: ticker,
        value: 0
      }));

      // Transform the data for the chart
      const transformedData = results.reduce((acc, { metric, data }) => {
        // Start with the base data structure
        if (acc.length === 0) {
          acc = [...baseData];
        }

        // Create a map of existing data points
        const dataMap = new Map<string, number>(data.map((item: DataItem) => [item.name, item.value]));

        // Update all time points, using null for missing data instead of 0
        acc.forEach(point => {
          point[metric] = dataMap.get(point.name) ?? null;  // Use null coalescing
          point.ticker = ticker;
        });

        return acc;
      }, [] as ChartDataPoint[]);

      console.log('Transformed data:', transformedData);
      setChartData(transformedData);

    } catch (error) {
      console.error('Error fetching metric data:', error);
      setError('Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  }, [searchValue, selectedSearchMetrics, selectedPeriod]);

  const fetchPeerData = useCallback(async () => {
    try {
      if (!selectedCompanies.length || !selectedPeerMetric) {
        console.log('Missing required data for peer fetch:', { 
          companies: selectedCompanies, 
          metric: selectedPeerMetric 
        });
        return;
      }
      
      console.log('Fetching peer data for:', {
        companies: selectedCompanies.map(c => c.ticker),
        metric: selectedPeerMetric,
        period: selectedPeriod
      });
      
      setPeerLoading(true);
      setPeerError(null);

      // Fetch data for each company
      const promises = selectedCompanies.map(async company => {
        const url = `${baseUrl}/api/aggregated-data/?tickers=${encodeURIComponent(company.ticker)}&metric=${encodeURIComponent(selectedPeerMetric)}&period=${encodeURIComponent(selectedPeriod)}`;
        console.log('Fetching from:', url);
        const response = await fetch(url);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch data for ${company.ticker}`);
        }
        
        const data = await response.json();
        console.log(`Data for ${company.ticker}:`, data);
        return { company, data };
      });

      const results = await Promise.all(promises);
      
      if (results.length === 0 || results[0].data.length === 0) {
        console.error('No data returned from API');
        setPeerError('No data available for the selected companies and metric');
        setPeerChartData([]);
        return;
      }

      // Create a unified dataset with all companies
      const transformedData = results[0].data.map((timePoint: TimePoint) => {
        const point: PeerDataPoint = { 
          name: timePoint.name,
          // Add metric name as key with company values
          [selectedPeerMetric]: {} 
        };
        
        results.forEach(({ company, data }) => {
          const matchingPoint = data.find((d: DataItem) => d.name === timePoint.name);
          if (matchingPoint) {
            (point[selectedPeerMetric] as { [ticker: string]: number })[company.ticker] = matchingPoint.value;
          }
        });
        
        return point;
      });

      console.log('Transformed peer data:', transformedData);
      setPeerChartData(transformedData);

    } catch (error) {
      console.error('Error fetching peer data:', error);
      setPeerError(`Failed to connect to backend. Ensure it's running at ${baseUrl}`);
      setPeerChartData([]);
    } finally {
      setPeerLoading(false);
    }
  }, [selectedCompanies, selectedPeerMetric, selectedPeriod, baseUrl]);

  const fetchIndustryData = useCallback(async () => {
    if (selectedIndustryMetrics.length === 0 || !selectedIndustry) return;
    
    setIndustryLoading(true);
    setIndustryError(null);
    
    try {
      const metricsParams = selectedIndustryMetrics.map(m => `metric[]=${encodeURIComponent(m)}`).join('&');
      const url = `${baseUrl}/api/boxplot-data/?${metricsParams}&period=${selectedPeriod}&industry=${encodeURIComponent(selectedIndustry)}`;
      console.log('Fetching from URL:', url);

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch industry data');
      }
      const data = await response.json();
      console.log('Raw industry data:', data);

      // Directly use the values object
      setIndustryChartData(data.values || {});
      setIndustryCompanyNames(data.companyNames || {});

    } catch (error) {
      console.error('Error fetching industry data:', error);
      setIndustryError('Failed to fetch industry data');
    } finally {
      setIndustryLoading(false);
    }
  }, [selectedIndustryMetrics, selectedPeriod, selectedIndustry]);

  const fetchAvailableIndustries = async () => {
    try {
      const response = await fetch(`${baseUrl}/api/industries/`);
      const data = await response.json();
      console.log('Raw industries data:', data);
      
      // Format industries correctly
      const formattedIndustries = data.industries.map((industry: { name: string, companies: string[] }) => ({
        value: industry.name,
        label: industry.name,
        companies: industry.companies
      }));
      
      console.log('Formatted industries:', formattedIndustries);
      setAvailableIndustries(formattedIndustries);
    } catch (error) {
      console.error('Error fetching industries:', error);
    }
  };

  useEffect(() => {
    fetchAvailableMetrics();
  }, []);

  // Fetch metric data when dependencies change (do NOT depend on chartData)
  useEffect(() => {
    if (activeChart === 'metrics') {
      fetchMetricData();
    }
  }, [searchValue, selectedSearchMetrics, activeChart, selectedPeriod, fetchMetricData]);

  // Update the useEffect that sets fixed2024Data
  useEffect(() => {
    if (activeChart === 'metrics' && chartData.length > 0) {
      // For annual view, keep the 2024 logic
      if (selectedPeriod === '1Y') {
        const data2024 = chartData.find(d => d.name.startsWith('2024'));
        if (data2024) {
          setFixed2024Data(data2024);
        }
      } else {
        // For other periods (2Y, 3Y, etc.), use the last period
        const lastPeriod = chartData[chartData.length - 1];
        if (lastPeriod) {
          setFixed2024Data(lastPeriod);
        }
      }
    } else if (activeChart === 'peers' && peerChartData.length > 0) {
      if (selectedPeriod === '1Y') {
        const data2024 = peerChartData.find(d => d.name.startsWith('2024'));
        if (data2024) {
          setFixed2024Data(data2024);
        }
      } else {
        const lastPeriod = peerChartData[peerChartData.length - 1];
        if (lastPeriod) {
          setFixed2024Data(lastPeriod);
        }
      }
    }
  }, [chartData, peerChartData, activeChart, selectedPeriod]);

  useEffect(() => {
    if (activeChart === 'peers' && selectedPeerMetric && selectedCompanies.length > 0) {
      console.log('Triggering peer data fetch');
      fetchPeerData();
    }
  }, [activeChart, selectedPeerMetric, selectedCompanies, fetchPeerData]);

  useEffect(() => {
    if (activeChart === 'industry') {
      fetchIndustryData();
    }
  }, [activeChart, selectedIndustryMetrics, selectedPeriod, selectedIndustry, fetchIndustryData]);

  useEffect(() => {
    if (availableMetrics.length === 0) return;
    
    const colors = generateColorPalette(availableMetrics.length);
    const newMetricColors: MetricConfigs = {};
    
    availableMetrics.forEach((metric, index) => {
      newMetricColors[metric.value] = {
        color: colors[index],
        label: metric.label
      };
    });
    
    setMetricColors(newMetricColors);
  }, [availableMetrics]);

  useEffect(() => {
    fetchAvailableIndustries();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowMetricDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Add this useEffect for industry dropdown click handling
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (industryDropdownRef.current && !industryDropdownRef.current.contains(event.target as Node)) {
        setShowIndustryDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Add click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (companyDropdownRef.current && !companyDropdownRef.current.contains(event.target as Node)) {
        setShowCompanyDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Add click outside handler for peer dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (peerDropdownRef.current && !peerDropdownRef.current.contains(event.target as Node)) {
        setShowPeerMetricDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Find the position of the last tick (2024) after chart renders
  useLayoutEffect(() => {
    if (!fixed2024Data) return;
    const chartDiv = chartContainerRef.current;
    if (!chartDiv) return;
    // Find the tick element whose label is 2024
    const tick2024 = document.querySelector(`.xAxis .recharts-cartesian-axis-tick:last-child`) as HTMLElement | null;
    if (!tick2024) return;
    const tickRect = tick2024.getBoundingClientRect();
    const chartRect = chartDiv.getBoundingClientRect();
    setFixedTooltipPos({
      left: tickRect.left - chartRect.left + tickRect.width / 2,
      top: 40 // adjust as needed
    });
    console.log('Set fixedTooltipPos:', {
      left: tickRect.left - chartRect.left + tickRect.width / 2,
      top: 40
    });
  }, [fixed2024Data, chartData, activeChart]);

  // Remove this function if not used
  // const toggleSidebar = () => {
  //   setIsSidebarVisible(!isSidebarVisible);
  // };

  console.log('chartData:', chartData);
  console.log('fixed2024Data:', fixed2024Data);
  console.log('fixedTooltipPos:', fixedTooltipPos);
  console.log('peerChartData:', peerChartData);
  console.log('fixed2024Data:', fixed2024Data);

  // Update the diff calculation to handle null
  // const calculatePercentage = (current: number, previous: number | null) => {
  //   if (previous === null || previous === 0) return null;
  //   return ((current - previous) / previous) * 100;
  // };

  // Update DefaultTooltipContent usage
  // const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  //   if (!active || !payload) return null;
  //   return (
  //     <div className="custom-tooltip bg-white p-2 border rounded shadow">
  //       <p className="label">{label}</p>
  //       {payload.map((entry: any) => (
  //         <p key={entry.name} style={{ color: entry.color }}>
  //           {entry.name}: {entry.value}
  //         </p>
  //       ))}
  //     </div>
  //   );
  // };

  // Example of fetching companies
  // const fetchCompanies = async (tickers: string[]) => {
  //   try {
  //     console.log('Fetching companies for tickers:', tickers);
  //     const response = await fetch(`http://127.0.0.1:8000/api/companies?tickers=${tickers.join(',')}`);
  //     const data = await response.json();
  //     console.log('Received company data:', data);
      
  //     // Transform the data to match our expected structure
  //     const companies = data.map((company: any) => ({
  //       ticker: company.ticker,
  //       name: company.name
  //     }));
      
  //     setSelectedCompanies(companies);
  //   } catch (error) {
  //     console.error('Error fetching companies:', error);
  //   }
  // };

  useEffect(() => {
    console.log('Current selectedCompanies:', selectedCompanies);
  }, [selectedCompanies]);

  // Remove or comment out the existing useEffect that references selectedIndustryCompanies:
  // useEffect(() => {
  //   console.log('Selected Industry Companies:', selectedIndustryCompanies);
  // }, [selectedIndustryCompanies]);

  // Ensure this useEffect is called when the industry is selected
  useEffect(() => {
    if (selectedIndustry) {
      // Fetch or set selectedIndustryCompanies here
      // Example: setSelectedIndustryCompanies(fetchCompaniesForIndustry(selectedIndustry));
    }
  }, [selectedIndustry]);

  // Add effect to update selectedPeerMetrics when selectedPeerMetric changes
  useEffect(() => {
    if (selectedPeerMetric) {
      setSelectedPeerMetrics([selectedPeerMetric]);
    }
  }, [selectedPeerMetric]);

  // Update the peer metric selection handler
  // const handlePeerMetricSelection = (metric: string) => {
  //   console.log('Selected peer metric:', metric);
  //   setSelectedPeerMetric(metric);
  //   setSelectedPeerMetrics([metric]); // Update the metrics array
  //   setShowPeerMetricDropdown(false);
  // };

  useEffect(() => {
    const clearHandler = () => {
      setMessages([
        {
          role: 'assistant',
          content: 'I can help you analyze this data. What would you like to know?'
        }
      ]);
    };
    window.addEventListener('clearChat', clearHandler);
    return () => window.removeEventListener('clearChat', clearHandler);
  }, []);

  // Example usage:
  // const getChatboxPayload = () => {
  //   // ... (original implementation)
  // };

  return (
    <div className="flex flex-col lg:flex-row min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <div className="lg:hidden flex justify-between items-center p-3 sm:p-4 bg-white border-b">
        <img src="/GetDeepLogo.png" alt="GetDeep.AI" className="h-8 sm:h-10 md:h-12" />
        <button className="p-2">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      {/* Sidebar */}
      <div className={`${isSidebarVisible ? 'lg:block' : 'lg:hidden'} hidden w-64 xl:w-72 bg-white border-r transition-all duration-300`}>
        <div className="px-4 xl:px-6 h-full">
          <div className="space-y-4 mt-[9.5rem]">
            {/* Hamburger Menu Icon with onClick */}
            <button 
              onClick={() => setIsSidebarVisible(false)}
              className="flex items-center gap-2 w-full text-left p-2 hover:bg-gray-100 rounded mb-4"
            >
              <svg 
                className="w-6 h-6 text-gray-600" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>

          <div className="space-y-2">
            <button className="flex items-center gap-2 w-full text-left p-2 hover:bg-gray-100 rounded">
              <span className="text-xl">+</span>
                <span>Customize GetDeep (DIY)</span>
            </button>
            <div className="pl-8 space-y-2 text-sm text-gray-600">
              <div>Add data sources</div>
              <div>Change model</div>
            </div>
          </div>

          <div className="space-y-2">
            <button className="flex items-center gap-2 w-full text-left p-2 hover:bg-gray-100 rounded">
              <span>💡</span>
                <span>Develop Insights for you</span>
            </button>
            <div className="pl-8 space-y-2 text-sm text-gray-600">
              <div>Business/industry report</div>
              <div>Holistic business strategy</div>
            </div>
          </div>

          <div className="space-y-2">
            <button className="flex items-center gap-2 w-full text-left p-2 hover:bg-gray-100 rounded">
              <span>🛠️</span>
                <span>Build tools for your use case</span>
            </button>
            <div className="pl-8 space-y-2 text-sm text-gray-600">
              <div>Data/IT/OT foundations</div>
              <div>Decision making AI tools</div>
              <div>AI Agents & solutions</div>
            </div>
          </div>

          <div className="space-y-2">
            <button className="flex items-center gap-2 w-full text-left p-2 hover:bg-gray-100 rounded">
              <span>📄</span>
                <span>Recent charts and reports</span>
            </button>
            <div className="pl-8 space-y-2 text-sm text-gray-600">
              <div>CAT revenue chart</div>
              <div>Machinery industry report</div>
              <div>AI Agents in Industrials</div>
            </div>
          </div>
        </div>
      </div>
      </div>

      {/* Floating hamburger when sidebar is hidden */}
      {!isSidebarVisible && (
        <button 
          onClick={() => setIsSidebarVisible(true)}
          className="fixed top-[6rem] left-4 p-2 bg-white rounded-lg shadow-md hover:bg-gray-100 z-50"
        >
          <svg 
            className="w-6 h-6 text-gray-600" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      )}

      {/* Main Content */}
      <div className={`flex-1 ${isSidebarVisible ? 'lg:ml-0' : 'lg:ml-0'}`}>
        {/* Top section with both logos - full width */}
        <div className="border-b bg-white absolute left-0 right-0 h-36">
          <div className="flex items-center h-full relative">
            {/* Logo container - hide on mobile */}
            <div className="hidden lg:block w-64 xl:w-72 overflow-visible absolute -top-12">
              <img 
                src="/GetDeepLogo.png" 
                alt="GetDeep.AI" 
                className="h-56 xl:h-60"
              />
            </div>
            
            {/* GetDeeper icon container with user profile */}
            <div className="flex-1 flex justify-end items-center gap-6">
              <div className="lg:mr-[33%] absolute top-8">  
                <img 
                  src="/GetDeeperIcons.png" 
                  alt="Pro" 
                  className="w-28 h-28 sm:w-32 sm:h-32 lg:w-40 lg:h-18"
                />
              </div>
              
              {/* User Profile - hide on mobile */}
              <div className="hidden lg:block absolute right-6">
          <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-xl xl:text-2xl">
                      Anand Manthena
                    </div>
                  </div>
                  <div className="w-10 xl:w-12 h-10 xl:h-12 bg-[#1B5A7D] rounded-full flex items-center justify-center text-white text-base xl:text-lg">
                    AM
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="p-3 sm:p-4 lg:p-6 xl:p-8 mt-[95px]">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 xl:gap-6">
            {/* Chart Section - full width on mobile */}
            <div className="lg:col-span-6">
              <div className="bg-white rounded-lg p-4 xl:p-6 shadow-sm">
                {/* Chart Header with Save Button */}
                <div className="flex justify-between items-center mb-4 xl:mb-6">
                  <h2 className="text-lg sm:text-xl xl:text-2xl font-medium">Business Performance</h2>
                  <button className="px-3 xl:px-4 py-2 text-sm xl:text-base bg-[#1B5A7D] text-white rounded hover:bg-[#164964]">
                    Save chart
                  </button>
        </div>

        {/* Metrics Selector */}
                <div className="overflow-x-auto -mx-4 sm:mx-0">
                  <div className="space-y-3 xl:space-y-4 min-w-max px-4 sm:px-0">
                    <div className="flex gap-3 xl:gap-4">
                      <button 
                        onClick={() => setActiveChart('metrics')}
                        className={`px-3 xl:px-4 py-2 text-sm xl:text-base rounded ${
                          activeChart === 'metrics' ? 'bg-[#E5F0F6] text-[#1B5A7D]' : 'text-gray-600'
                        }`}
                      >
                        Across Metrics
                      </button>
                      <button 
                        onClick={() => setActiveChart('peers')}
                        className={`px-4 py-2 text-gray-600 ${
                          activeChart === 'peers' ? 'bg-[#E5F0F6] text-[#1B5A7D]' : 'text-gray-600'
                        }`}
                      >
                        Across Peers
                      </button>
                      <button 
                        onClick={() => setActiveChart('industry')}
                        className={`px-4 py-2 text-gray-600 ${
                          activeChart === 'industry' ? 'bg-[#E5F0F6] text-[#1B5A7D]' : 'text-gray-600'
                        }`}
                      >
                        Across Industry
                      </button>
          </div>
          <div className="flex gap-4">
                      <button 
                        onClick={() => setSelectedPeriod('1Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '1Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        {activeChart === 'industry' ? 'Last 1Y' : 'Annual'}
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('2Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '2Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        {activeChart === 'industry' ? 'Last 2Ys' : '2Ys'}
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('3Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '3Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        {activeChart === 'industry' ? 'Last 3Ys' : '3Ys'}
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('4Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '4Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        {activeChart === 'industry' ? 'Last 4Ys' : '4Ys'}
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('5Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '5Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        {activeChart === 'industry' ? 'Last 5Ys' : '5Ys'}
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('10Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '10Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        {activeChart === 'industry' ? 'Last 10Ys' : '10Ys'}
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('15Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '15Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        {activeChart === 'industry' ? 'Last 15Ys' : '15Ys'}
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('20Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '20Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        {activeChart === 'industry' ? 'Last 20Ys' : '20Ys'}
                      </button>
                    </div>
          </div>
        </div>

                {/* Chart Content */}
                <div className="mt-4 xl:mt-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 xl:gap-4 mb-4">
            {/* Industry selection - moved to top */}
            {activeChart === 'industry' && (
              <div className="col-span-full">
                <div className="text-sm xl:text-base text-gray-500">Industry</div>
                <div className="relative" ref={industryDropdownRef}>
                  <input
                    type="text"
                    placeholder="Search industries..."
                    value={industrySearch}
                    onChange={(e) => setIndustrySearch(e.target.value)}
                    onFocus={() => setShowIndustryDropdown(true)}
                    className="w-full font-medium text-sm xl:text-base px-3 py-2 pr-8 border border-gray-200 rounded focus:outline-none focus:border-[#1B5A7D] focus:ring-1 focus:ring-[#1B5A7D]"
                  />
                  {industrySearch && (
                    <button
                      onClick={() => setIndustrySearch('')}
                      className="absolute right-6 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  )}
                  <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                  
                  {showIndustryDropdown && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded shadow-lg max-h-60 overflow-auto">
                      {availableIndustries
                        .filter(industry => 
                          industry.label.toLowerCase().includes(industrySearch.toLowerCase()) ||
                          industry.value.toLowerCase().includes(industrySearch.toLowerCase())
                        )
                        .map(industry => (
                          <div
                            key={industry.value}
                            onClick={() => {
                              setSelectedIndustry(industry.value);
                              setIndustrySearch(industry.label);
                              setShowIndustryDropdown(false);
                            }}
                            className="px-3 py-2 text-sm xl:text-base hover:bg-gray-100 cursor-pointer"
                          >
                            {industry.label.replace(/  +/g, ' ')}
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Company Search */}
            <div>
              <div className="text-sm xl:text-base text-gray-500">Company</div>
              {activeChart === 'peers' ? (
                <div className="relative" ref={companyDropdownRef}>
                  <div className="flex flex-wrap gap-2 p-2 border border-gray-200 rounded min-h-[42px]">
                    {selectedCompanies.map((company, index) => (
                      <div 
                        key={index} 
                        className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm"
                      >
                        {company.name || company.ticker}
                        <button
                          onClick={() => setSelectedCompanies(companies => 
                            companies.filter((_, i) => i !== index)
                          )}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <svg
                            className="w-3 h-3"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M6 18L18 6M6 6l12 12"
                            />
                          </svg>
                        </button>
                      </div>
                    ))}
                    <input
                      type="text"
                      value={companyInput}
                      onChange={(e) => setCompanyInput(e.target.value)}
                      onFocus={() => setShowCompanyDropdown(true)}
                      placeholder="Search companies..."
                      className="flex-1 min-w-[100px] outline-none text-sm"
                    />
                  </div>
                  
                  {showCompanyDropdown && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded shadow-lg max-h-60 overflow-auto">
                      {availableIndustries
                        .flatMap(industry => industry.companies)
                        .filter((ticker, index, self) => self.indexOf(ticker) === index) // Remove duplicates
                        .filter(ticker => 
                          ticker.toLowerCase().includes(companyInput.toLowerCase())
                        )
                        .sort((a, b) => a.localeCompare(b))
                        .map(ticker => {
                          const displayName = companyMap[ticker] || ticker;
                          
                          return (
                            <div
                              key={ticker}
                              onClick={() => {
                                if (!selectedCompanies.some(c => c.ticker === ticker)) {
                                  setSelectedCompanies([...selectedCompanies, { ticker, name: displayName }]);
                                }
                                setCompanyInput('');
                                setShowCompanyDropdown(false);
                              }}
                              className="px-3 py-2 text-sm xl:text-base hover:bg-gray-100 cursor-pointer"
                            >
                              {displayName} ({ticker})
                            </div>
                          );
                        })}
                    </div>
                  )}
                </div>
              ) : activeChart === 'industry' ? (
                <div className="relative" ref={companyDropdownRef}>
                  <input
                    type="text"
                    placeholder="Search companies..."
                    value={selectedTicker || companySearch}
                    onChange={(e) => {
                      setCompanySearch(e.target.value);
                      setSelectedTicker(''); // Clear selection when typing
                    }}
                    onFocus={() => setShowCompanyDropdown(true)}
                    className="w-full font-medium text-sm xl:text-base px-3 py-2 pr-8 border border-gray-200 rounded focus:outline-none focus:border-[#1B5A7D] focus:ring-1 focus:ring-[#1B5A7D]"
                  />
                  {selectedTicker && (
                    <button
                      onClick={() => {
                        setSelectedTicker('');
                        setCompanySearch('');
                      }}
                      className="absolute right-8 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                  <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                  
                  {showCompanyDropdown && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded shadow-lg max-h-60 overflow-auto">
                      {availableIndustries
                        .find(ind => ind.value === selectedIndustry)
                        ?.companies
                        .filter(ticker => 
                          ticker.toLowerCase().includes(companySearch.toLowerCase())
                        )
                        .sort((a, b) => a.localeCompare(b))
                        .map(ticker => {
                          const displayName = companyMap[ticker] || ticker;

                          return (
                            <div
                              key={ticker}
                              onClick={() => {
                                setSelectedTicker(ticker);
                                setCompanySearch('');
                                setShowCompanyDropdown(false);
                              }}
                              className="px-3 py-2 text-sm xl:text-base hover:bg-gray-100 cursor-pointer"
                            >
                              {displayName} ({ticker})
                            </div>
                          );
                        })}
                    </div>
                  )}
                </div>
              ) : (
                <div className="relative" ref={companyDropdownRef}>
                  <input
                    type="text"
                    value={searchValue}
                    onChange={(e) => setSearchValue(e.target.value)}
                    onFocus={() => setShowCompanyDropdown(true)}
                    placeholder="Search company..."
                    className="w-full font-medium text-sm xl:text-base px-3 py-2 pr-8 border border-gray-200 rounded focus:outline-none focus:border-[#1B5A7D] focus:ring-1 focus:ring-[#1B5A7D]"
                  />
                  {searchValue && (
                    <button
                      onClick={() => setSearchValue('')}
                      className="absolute right-6 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  )}
                  <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>

                  {showCompanyDropdown && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded shadow-lg max-h-60 overflow-auto">
                      {availableIndustries.flatMap(industry => 
                        industry.companies.filter(ticker =>
                          ticker.toLowerCase().includes(searchValue.toLowerCase())
                        ).map(ticker => {
                          const displayName = companyMap[ticker] || ticker;
                          return (
                            <div
                              key={ticker}
                              onClick={() => {
                                setSearchValue(ticker);
                                setShowCompanyDropdown(false);
                              }}
                              className="px-3 py-2 text-sm xl:text-base hover:bg-gray-100 cursor-pointer"
                            >
                              {displayName} ({ticker})
                            </div>
                          );
                        })
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Metric Search */}
            <div>
              <div className="text-sm xl:text-base text-gray-500">Metric</div>
              {activeChart === 'peers' ? (
                <div className="relative" ref={peerDropdownRef}>
                  <input
                    type="text"
                    placeholder="Search metrics..."
                    value={peerMetricSearch || selectedPeerMetric}
                    onChange={(e) => {
                      setPeerMetricSearch(e.target.value);
                      setSelectedPeerMetric('');
                    }}
                    onFocus={() => setShowPeerMetricDropdown(true)}
                    className="w-full font-medium text-sm xl:text-base px-3 py-2 pr-8 border border-gray-200 rounded focus:outline-none focus:border-[#1B5A7D] focus:ring-1 focus:ring-[#1B5A7D]"
                  />
                  {(peerMetricSearch || selectedPeerMetric) && (
                    <button
                      onClick={() => {
                        setPeerMetricSearch('');
                        setSelectedPeerMetric('');
                      }}
                      className="absolute right-6 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                  <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                  
                  {showPeerMetricDropdown && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded shadow-lg max-h-60 overflow-auto">
                      {availableMetrics
                        .filter(metric => 
                          metric.label.toLowerCase().includes(peerMetricSearch.toLowerCase()) ||
                          metric.value.toLowerCase().includes(peerMetricSearch.toLowerCase())
                        )
                        .map(metric => (
                          <div
                            key={metric.value}
                            onClick={() => {
                              setSelectedPeerMetric(metric.value);
                              setPeerMetricSearch('');
                              setShowPeerMetricDropdown(false);
                            }}
                            className="px-3 py-2 text-sm xl:text-base hover:bg-gray-100 cursor-pointer"
                          >
                        {metric.label}
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              ) : activeChart === 'metrics' ? (
                <div className="space-y-3">
                  {/* Search box with selected metrics */}
                  <div className="flex flex-wrap gap-2 p-2 border border-gray-200 rounded min-h-[42px]">
                    {selectedSearchMetrics.map((metric, index) => (
                      <div 
                        key={index} 
                        className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm"
                      >
                        {metric}
                        <button
                          onClick={() => setSelectedSearchMetrics(metrics => 
                            metrics.filter((_, i) => i !== index)
                          )}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <svg
                            className="w-3 h-3"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M6 18L18 6M6 6l12 12"
                            />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Updated metric search dropdown */}
                  <div className="relative" ref={dropdownRef}>
                    <input
                      type="text"
                      placeholder="Search metrics..."
                      value={searchMetricInput}
                      onChange={(e) => setSearchMetricInput(e.target.value)}
                      onFocus={() => setShowMetricDropdown(true)}
                      className="w-full font-medium text-sm xl:text-base px-3 py-2 pr-8 border border-gray-200 rounded focus:outline-none focus:border-[#1B5A7D] focus:ring-1 focus:ring-[#1B5A7D]"
                    />
                    {searchMetricInput && (
                      <button
                        onClick={() => {
                          setSearchMetricInput('');
                          setShowMetricDropdown(false);
                        }}
                        className="absolute right-6 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                    <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>

                    {showMetricDropdown && (
                      <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded shadow-lg max-h-60 overflow-auto">
                        {availableMetrics
                          .filter(metric => 
                            !selectedSearchMetrics.includes(metric.value) &&
                            (metric.label.toLowerCase().includes(searchMetricInput.toLowerCase()) ||
                            metric.value.toLowerCase().includes(searchMetricInput.toLowerCase()))
                          )
                          .map(metric => (
                            <div
                              key={metric.value}
                              onClick={() => {
                                if (!selectedSearchMetrics.includes(metric.value)) {
                                  setSelectedSearchMetrics([...selectedSearchMetrics, metric.value]);
                                }
                                setSearchMetricInput('');
                                setShowMetricDropdown(false);
                              }}
                              className="px-3 py-2 text-sm xl:text-base hover:bg-gray-100 cursor-pointer"
                            >
                            {metric.label}
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {/* Selected metrics as chips */}
                  <div className="flex flex-wrap gap-2 p-2 border border-gray-200 rounded min-h-[42px]">
                    {selectedIndustryMetrics.map((metric, index) => {
                      const metricLabel = availableMetrics.find(m => m.value === metric)?.label || metric;
                      return (
                        <div 
                          key={index} 
                          className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm"
                        >
                          {metricLabel}
                          <button
                            onClick={() => setSelectedIndustryMetrics(metrics => 
                              metrics.filter((_, i) => i !== index)
                            )}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            <svg
                              className="w-3 h-3"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          </button>
                        </div>
                      );
                    })}
                  </div>
                  
                  <div className="relative" ref={dropdownRef}>
                    <input
                      type="text"
                      placeholder="Search metrics..."
                      value={industryMetricInput}
                      onChange={(e) => setIndustryMetricInput(e.target.value)}
                      onFocus={() => setShowMetricDropdown(true)}
                      className="w-full font-medium text-sm xl:text-base px-3 py-2 pr-8 border border-gray-200 rounded focus:outline-none focus:border-[#1B5A7D] focus:ring-1 focus:ring-[#1B5A7D]"
                      disabled={selectedIndustryMetrics.length >= 3}
                    />
                    {industryMetricInput && (
                      <button
                        onClick={() => {
                          if (selectedIndustryMetrics.length >= 3) {
                            alert('Maximum of 3 metrics allowed');
                            return;
                          }
                          setSelectedIndustryMetrics([...selectedIndustryMetrics, industryMetricInput]);
                          setIndustryMetricInput('');
                          setShowMetricDropdown(false);
                        }}
                        className={`px-3 py-2 text-sm xl:text-base cursor-pointer ${
                          selectedIndustryMetrics.length >= 3 
                            ? 'bg-gray-50 text-gray-400 cursor-not-allowed' 
                            : 'hover:bg-gray-100'
                        }`}
                      >
                        {industryMetricInput}
                      </button>
                    )}
                    <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                    
                    {showMetricDropdown && (
                      <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded shadow-lg max-h-60 overflow-auto">
                        {availableMetrics
                          .filter(metric => 
                            !selectedIndustryMetrics.includes(metric.value) &&
                            (metric.label.toLowerCase().includes(industryMetricInput.toLowerCase()) ||
                            metric.value.toLowerCase().includes(industryMetricInput.toLowerCase()))
                          )
                          .map(metric => (
                            <div
                              key={metric.value}
                              onClick={() => {
                                if (selectedIndustryMetrics.length >= 3) {
                                  alert('Maximum of 3 metrics allowed');
                                  return;
                                }
                                setSelectedIndustryMetrics([...selectedIndustryMetrics, metric.value]);
                                setIndustryMetricInput('');
                                setShowMetricDropdown(false);
                              }}
                              className={`px-3 py-2 text-sm xl:text-base cursor-pointer ${
                                selectedIndustryMetrics.length >= 3 
                                  ? 'bg-gray-50 text-gray-400 cursor-not-allowed' 
                                  : 'hover:bg-gray-100'
                              }`}
                            >
                              {metric.label}
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

                <div className="h-[200px] sm:h-[350px] xl:h-[400px] overflow-y-auto p-4 xl:p-6 space-y-4">
                  {activeChart === 'metrics' ? (
                    // Metrics Chart
                    isLoading ? (
                      <div className="flex items-center justify-center h-full">
                        <span>Loading...</span>
                      </div>
                    ) : error ? (
                      <div className="flex items-center justify-center h-full text-red-500">
                        {error}
                      </div>
                    ) : chartData.length === 0 ? (
                      <div className="flex items-center justify-center h-full text-gray-500">
                        No data available
                      </div>
                    ) : ( 
                      <div ref={chartContainerRef} style={{ position: 'relative', width: '100%', height: '100%' }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart 
                            data={chartData}
                            onMouseMove={e => {
                              if (e && e.activePayload && e.activePayload.length > 0) {
                                const payload = e.activePayload[0].payload;
                                const isFixedPoint = selectedPeriod === '1Y' 
                                  ? payload.name?.startsWith('2024')
                                  : payload.name === chartData[chartData.length - 1]?.name;
                                
                                if (!isFixedPoint) {
                                  setActiveTooltip(payload);
                                } else {
                                  setActiveTooltip(null);
                                }
                              } else {
                                setActiveTooltip(null);
                              }
                            }}
                            onMouseLeave={() => setActiveTooltip(null)}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                            <XAxis 
                              dataKey="name" 
                              tickFormatter={(value) => {
                                if (typeof value === 'string' && value.includes('-')) {
                                  if (selectedPeriod !== '1Y') {
                                    return value;
                                  }
                                  const [startYear] = value.split('-');
                                  return startYear;
                                }
                                return value;
                              }}
                            />
                            <YAxis 
                              tickFormatter={(value) => new Intl.NumberFormat('en-US', {
                                notation: 'compact',
                                maximumFractionDigits: 1
                              }).format(value)}
                            />
                            
                            {/* Regular hover tooltip */}
                            <Tooltip
                              formatter={((value: string | number, name: string) => {
                                // Split the name into metric and ticker
                                const [metric, ticker] = name.split('.');
                                const company = selectedCompanies.find(c => c.ticker === ticker);
                                const formattedValue =
                                  value !== null && value !== undefined
                                    ? new Intl.NumberFormat('en-US').format(Number(value))
                                    : "N/A";
                                const displayName = `${company?.name || ticker} - ${metric}`;
                                return [formattedValue, displayName];
                              }) as TooltipProps<string | number, string>['formatter']}
                              labelFormatter={(label) => {
                                if (typeof label === 'string' && label.includes('-')) {
                                  if (selectedPeriod !== '1Y') {
                                    return label;
                                  }
                                  const [startYear] = label.split('-');
                                  return startYear;
                                }
                                return label;
                              }}
                              content={({ active, payload, label }) => {
                                if (active && payload && payload.length > 0) {
                                  const point = payload[0].payload;
                                  const ticker = searchValue.split(':')[0].trim().toUpperCase(); // Define ticker here as well
                                  if ((selectedPeriod === '1Y' && point.name?.startsWith('2024')) || 
                                      (selectedPeriod !== '1Y' && point.name === chartData[chartData.length - 1]?.name)) {
                                    return null;
                                  }
                                  return (
                                    <div className="custom-tooltip bg-white p-2 border rounded shadow">
                                      <p className="label">{label}</p>
                                      {payload.map((entry: any) => (
                                        <p key={entry.name} style={{ color: entry.color }}>
                                          {`${entry.name} (${ticker})`}: {entry.value === null ? "N/A" : new Intl.NumberFormat('en-US', {
                                            notation: 'compact',
                                            maximumFractionDigits: 1
                                          }).format(entry.value)}
                                        </p>
                                      ))}
                                    </div>
                                  );
                                }
                                return null;
                              }}
                              contentStyle={{ boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}
                              itemStyle={{ padding: 0 }}
                              filterNull={false}  // Changed to false to show null values
                            />

                            <Legend />
                            {selectedSearchMetrics.map((metric, idx) => {
                              const color = generateColorPalette(selectedSearchMetrics.length)[idx];
                              const metricLabel = availableMetrics.find(m => m.value === metric)?.label || metric;
                              return (
                                <Line
                                  key={metric}
                                  type="monotone"
                                  dataKey={metric}
                                  stroke={color}
                                  name={metricLabel}
                                  strokeWidth={2}
                                  dot={{
                                    fill: color,
                                    r: 4
                                  }}
                                  connectNulls={false}  // Add this prop to each Line component
                                />
                              );
                            })}
                          </LineChart>
                        </ResponsiveContainer>
                        {/* Fixed tooltip for 2024 */}
                        {selectedSearchMetrics.length > 0 && fixed2024Data && fixedTooltipPos && (
                          <div
                            style={{
                              position: 'absolute',
                              left: fixedTooltipPos.left - 70,
                              top: fixedTooltipPos.top + 16,
                              zIndex: 99999,
                              background: '#fff',
                              border: '1px solid #ccc',
                              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                              borderRadius: 4,
                              padding: 10,
                              minWidth: 0,
                              fontSize: 'inherit',
                              pointerEvents: 'none',
                            }}
                          >
                            <div className="font-medium mb-1">
                              {selectedPeriod === '1Y' ? '2024' : fixed2024Data.name}
                            </div>
                            {selectedSearchMetrics.map((metric) => {
                              const value = fixed2024Data[metric];
                              const hoveredValue = (activeTooltip && activeTooltip[metric] != null)
                                ? Number(activeTooltip[metric])
                                : null;
                              const diff = value != null && hoveredValue != null ? value - hoveredValue : null;
                              const percent = (hoveredValue != null && hoveredValue !== 0 && diff != null)
                                ? (diff / hoveredValue) * 100
                                : null;
                              const isIncrease = percent != null && percent >= 0;
                              const color = metricColors[metric]?.color || generateColorPalette(1)[0];
                              const ticker = searchValue.split(':')[0].trim().toUpperCase(); // Define ticker here

                              return (
                                <div key={metric} className="mb-1 flex items-center">
                                  <span style={{ color, minWidth: 80, display: 'inline-block' }}>
                                    {`${metric} (${ticker})`}:  {/* Include the ticker in the fixed tooltip */}
                                  </span>
                                  <span>
                                    {value === null ? "N/A" : new Intl.NumberFormat('en-US', {
                                      notation: 'compact',
                                      maximumFractionDigits: 1
                                    }).format(value)}
                                  </span>
                                  {percent != null && (
                                    <span
                                      className={`ml-2 flex items-center text-xs font-semibold ${isIncrease ? 'text-green-600' : 'text-red-600'}`}
                                      style={{ minWidth: 50 }}
                                    >
                                      {isIncrease ? '▲' : '▼'}
                                      {Math.abs(percent).toFixed(1)}%
                                    </span>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )
                  ) : activeChart === 'peers' ? (
                    // Peers Chart
                    peerLoading ? (
                      <div className="flex items-center justify-center h-full">
                        <span>Loading...</span>
                      </div>
                    ) : peerError ? (
                      <div className="flex items-center justify-center h-full text-red-500">
                        {peerError}
                      </div>
                    ) : peerChartData.length === 0 ? (
                      <div className="flex items-center justify-center h-full text-gray-500">
                        No data available
                      </div>
                    ) : (
                      <div ref={chartContainerRef} style={{ position: 'relative', width: '100%', height: 400 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart 
                            data={peerChartData}
                            onMouseMove={e => {
                              if (e && e.activePayload && e.activePayload.length > 0) {
                                const payload = e.activePayload[0].payload;
                                const isFixedPoint = selectedPeriod === '1Y' 
                                  ? payload.name?.startsWith('2024')
                                  : payload.name === peerChartData[peerChartData.length - 1]?.name;
                                
                                if (!isFixedPoint) {
                                  setActiveTooltip(payload);
                                } else {
                                  setActiveTooltip(null);
                                }
                              } else {
                                setActiveTooltip(null);
                              }
                            }}
                            onMouseLeave={() => setActiveTooltip(null)}
                          >
                            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                            <XAxis 
                              dataKey="name" 
                              tickFormatter={(value) => {
                                if (typeof value === 'string' && value.includes('-')) {
                                  if (selectedPeriod !== '1Y') {
                                    return value;
                                  }
                                  const [startYear] = value.split('-');
                                  return startYear;
                                }
                                return value;
                              }}
                            />
                            <YAxis 
                              tickFormatter={(value) => new Intl.NumberFormat('en-US', {
                                notation: 'compact',
                                maximumFractionDigits: 1
                              }).format(value)}
                            />
                            <Tooltip 
                              content={({ active, payload, label }) => {
                                if (active && payload && payload.length > 0) {
                                  const point = payload[0].payload;
                                  const ticker = searchValue.split(':')[0].trim().toUpperCase(); // Define ticker here as well
                                  if ((selectedPeriod === '1Y' && point.name?.startsWith('2024')) || 
                                      (selectedPeriod !== '1Y' && point.name === peerChartData[peerChartData.length - 1]?.name)) {
                                    return null;
                                  }
                                  return (
                                    <div className="custom-tooltip bg-white p-2 border rounded shadow">
                                      <p className="label">{label}</p>
                                      {payload.map((entry: any) => (
                                        <p key={entry.name} style={{ color: entry.color }}>
                                          {`${entry.name} (${ticker})`}: {entry.value === null ? "N/A" : new Intl.NumberFormat('en-US', {
                                            notation: 'compact',
                                            maximumFractionDigits: 1
                                          }).format(entry.value)}
                                        </p>
                                      ))}
                                    </div>
                                  );
                                }
                                return null;
                              }}
                              contentStyle={{ boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}
                              itemStyle={{ padding: 0 }}
                              filterNull={false}
                            />
                            <Legend />
                            {selectedCompanies.map((company, idx) => {
                              const color = generateColorPalette(selectedCompanies.length)[idx];
                              return (
                                <Line
                                  key={company.ticker}
                                  type="monotone"
                                  dataKey={`${selectedPeerMetric}.${company.ticker}`}
                                  stroke={color}
                                  name={`${company.ticker} - ${selectedPeerMetric}`}
                                  strokeWidth={2}
                                  dot={{
                                    fill: color,
                                    r: 4
                                  }}
                                  connectNulls={false}
                                />
                              );
                            })}
                          </LineChart>
                        </ResponsiveContainer>
                        {/* Fixed tooltip for peers chart */}
                        {activeChart === 'peers' && fixed2024Data && fixedTooltipPos && (
                          <div
                            style={{
                              position: 'absolute',
                              left: fixedTooltipPos.left - 70,
                              top: fixedTooltipPos.top + 16,
                              zIndex: 99999,
                              background: '#fff',
                              border: '1px solid #ccc',
                              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                              borderRadius: 4,
                              padding: 10,
                              minWidth: 0,
                              fontSize: 'inherit',
                              pointerEvents: 'none',
                            }}
                          >
                            <div className="font-medium mb-1">
                              {selectedPeriod === '1Y' ? '2024' : fixed2024Data.name}
                            </div>
                            {selectedCompanies.map((company, idx) => {
                              const value = fixed2024Data[selectedPeerMetric]?.[company.ticker];
                              const hoveredValue = (activeTooltip && activeTooltip[selectedPeerMetric]?.[company.ticker] != null)
                                ? Number(activeTooltip[selectedPeerMetric][company.ticker])
                                : null;
                              const diff = value != null && hoveredValue != null ? value - hoveredValue : null;
                              const percent = (hoveredValue != null && hoveredValue !== 0 && diff != null)
                                ? (diff / hoveredValue) * 100
                                : null;
                              const isIncrease = percent != null && percent >= 0;
                              const color = generateColorPalette(selectedCompanies.length)[idx];
                              return (
                                <div key={company.ticker} className="mb-1 flex items-center">
                                  <span style={{ color, minWidth: 80, display: 'inline-block' }}>
                                    {company.ticker}:
                                  </span>
                                  <span>
                                    {value === null ? "N/A" : new Intl.NumberFormat('en-US', {
                                      notation: 'compact',
                                      maximumFractionDigits: 1
                                    }).format(value)}
                                  </span>
                                  {percent != null && (
                                    <span
                                      className={`ml-2 flex items-center text-xs font-semibold ${isIncrease ? 'text-green-600' : 'text-red-600'}`}
                                      style={{ minWidth: 50 }}
                                    >
                                      {isIncrease ? '▲' : '▼'}
                                      {Math.abs(percent).toFixed(1)}%
                                    </span>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )
                  ) : (
                    // Industry Chart
                    industryLoading ? (
                      <div className="flex items-center justify-center h-full">
                        <span>Loading...</span>
                      </div>
                    ) : industryError ? (
                      <div className="flex items-center justify-center h-full text-red-500">
                        {industryError}
                      </div>
                    ) : industryChartData && Object.keys(industryChartData).length > 0 ? (
                      <BoxPlot
                        data={industryChartData}
                        title={selectedIndustryMetrics.map(metric => 
                          availableMetrics.find(m => m.value === metric)?.label || metric
                        ).join(' vs ')}
                        companyNames={industryCompanyNames}
                        selectedTicker={selectedTicker}
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full text-gray-500">
                        No data available
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>

              {/* Search Input */}
              <div className="mt-3 xl:mt-4">
                <input 
                  type="text" 
                  placeholder="Search saved charts or reports"
                  className="w-full px-3 xl:px-4 py-2 xl:py-3 text-sm xl:text-base border rounded-lg"
                />
              </div>
              {/* Footer - adjust spacing on mobile */}
              <div className="mt-2 sm:mt-2 xl:mt-2 px-3 sm:px-4 lg:px-6 xl:px-8">
                <div className="flex flex-wrap gap-3 sm:gap-4 xl:gap-6 text-xs sm:text-sm xl:text-base text-gray-600">
                  <a href="#" className="hover:text-gray-800">Customer Stories</a>
                  <a href="#" className="hover:text-gray-800">About Us</a>
                  <a href="#" className="hover:text-gray-800">Careers</a>
                  <a href="#" className="hover:text-gray-800">Contact Us</a>
                </div>
              </div>
            </div>

            {/* Insights Generation - full width on mobile */}
            <div className="lg:col-span-4 lg:mr-[-11rem]">
              <div className="mt-0 sm:mt-3 lg:mt-4">
                <div className="bg-white rounded-lg shadow-sm">
                  <div className="p-4 xl:p-6 border-b flex justify-between items-center">
                    <div className="flex items-center gap-2 xl:gap-3">
                      <h2 className="text-lg sm:text-xl xl:text-2xl font-medium">Insights Generation</h2>
                      <button className="w-8 xl:w-10 h-8 xl:h-10 bg-[#1B5A7D] text-white rounded text-xl">+</button>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Clear Chat Button */}
                      <button
                        className="px-2 py-2 text-sm xl:text-base bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                        title="Clear Chat"
                        onClick={() => {
                          const event = new CustomEvent('clearChat');
                          window.dispatchEvent(event);
                        }}
                        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                      >
                        <svg width="18" height="18" fill="none" viewBox="0 0 20 20">
                          <path d="M6 6l8 8M6 14L14 6" stroke="#1B5A7D" strokeWidth="2" strokeLinecap="round"/>
                        </svg>
                      </button>
                      {/* Save Report Button */}
                      <button className="px-3 xl:px-4 py-2 text-sm xl:text-base bg-[#1B5A7D] text-white rounded">
                        Save Report
                      </button>
                    </div>
                  </div>
                  
                  {/* Chat Messages */}
                  <div className="h-[300px] sm:h-[350px] xl:h-[550px] overflow-y-auto p-4 xl:p-6 space-y-4">
                    {messages.map((message, index) => 
                      message.role === 'assistant' ? (
                        <div key={index} className="flex gap-3 xl:gap-4">
                          <div className="w-8 xl:w-10 h-8 xl:h-10 bg-[#1B5A7D] rounded-full flex items-center justify-center text-white text-sm xl:text-base">
                            AI
                          </div>
                          <div className="flex-1">
                            <div className="bg-[#E5F0F6] rounded-lg p-3 xl:p-4 text-sm xl:text-base">
                              {message.content}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div key={index} className="flex gap-3 justify-end xl:gap-4">
                          <div className="flex-1">
                            <div className="bg-gray-100 rounded-lg p-3 xl:p-4 text-sm xl:text-base ml-auto max-w-[80%]">
                              {message.content}
                            </div>
                          </div>
                          <div className="w-8 xl:w-10 h-8 xl:h-10 bg-gray-200 rounded-full flex items-center justify-center text-sm xl:text-base">
                            AM
                          </div>
                        </div>
                      )
                    )}
                  </div>

                  {/* Chat Input */}
                  <div className="p-4 xl:p-6 border-t">
                    <form 
                      className="flex gap-2 xl:gap-3"
                      onSubmit={(e) => {
                        e.preventDefault();
                        handleSendMessage(inputValue);
                        setInputValue('');
                      }}
                    >
                      <input 
                        type="text" 
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Ask Me Anything..."
                        className="flex-1 px-3 xl:px-4 py-2 xl:py-3 text-sm xl:text-base border rounded-lg"
                      />
                      <button type="button" className="p-2 xl:p-3">
                        <img src="/mic-icon.svg" alt="Voice" className="w-5 xl:w-6 h-5 xl:h-6" />
                      </button>
                      <button 
                        type="submit" 
                        className="p-2 xl:p-3"
                        disabled={!inputValue.trim()}
                      >
                        <img src="/send-icon.svg" alt="Send" className="w-5 xl:w-6 h-5 xl:h-6" />
                      </button>
                    </form>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard; 