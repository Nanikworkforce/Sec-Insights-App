import React, { useState, useEffect, useCallback, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import BoxPlot from './BoxPlot';

const BASE_URL = 'http://127.0.0.1:8000/api';

const data = [
  { date: 'Jan 16', revenue: 15000, cost: 8000 },
  { date: 'Jul 16', revenue: 19000, cost: 8500 },
  { date: 'Jan 17', revenue: 16500, cost: 9000 },
  { date: 'Jul 17', revenue: 17500, cost: 9800 },
  { date: 'Jan 18', revenue: 19000, cost: 8500 },
  { date: 'Jul 18', revenue: 23000, cost: 9000 },
];

const peersData = [
  { date: 'Jan 16', apple: 15000, microsoft: 12000, google: 14000 },
  { date: 'Jul 16', apple: 19000, microsoft: 15000, google: 18000 },
  { date: 'Jan 17', apple: 16500, microsoft: 14500, google: 16000 },
  { date: 'Jul 17', apple: 17500, microsoft: 16000, google: 19000 },
  { date: 'Jan 18', apple: 19000, microsoft: 18000, google: 21000 },
  { date: 'Jul 18', apple: 23000, microsoft: 20000, google: 24000 },
];

const industryData = [
  { date: 'Jan 16', automotive: 12000, technology: 15000, healthcare: 13000 },
  { date: 'Jul 16', automotive: 14000, technology: 18000, healthcare: 16000 },
  { date: 'Jan 17', automotive: 13500, technology: 16500, healthcare: 15500 },
  { date: 'Jul 17', automotive: 15500, technology: 19500, healthcare: 17500 },
  { date: 'Jan 18', automotive: 16000, technology: 21000, healthcare: 19000 },
  { date: 'Jul 18', automotive: 18000, technology: 24000, healthcare: 21000 },
];

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

// Add type for period
type PeriodType = '1Y' | '2Y' | '3Y' | '5Y' | '10Y' | '15Y';

// Add interface for peer data
interface PeerDataPoint {
  name: string;
  [key: string]: string | number;
}

// Update the selectedCompanies state to store ticker objects
interface CompanyTicker {
  ticker: string;
  name: string;
}

// First, add this interface for the chart data
interface ChartDataPoint {
  name: string;
  [key: string]: string | number;
}

// Add type for the chart click event
interface ChartClickEvent {
  activePayload?: Array<{
    value: number;
    payload: any;
  }>;
  chartX?: number;
  chartY?: number;
}

// Add this interface near other interfaces
interface StickyTooltip {
  x: number;
  y: number;
  payload: any[];
}

const Dashboard: React.FC = () => {
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);
  const [activeChart, setActiveChart] = useState<'metrics' | 'peers' | 'industry'>('metrics');
  const [searchValue, setSearchValue] = useState('AAPL');
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['Revenue', 'CostOfGoodsSold']);
  const [metricInput, setMetricInput] = useState('');
  const [selectedCompanies, setSelectedCompanies] = useState<CompanyTicker[]>([
    { ticker: 'AAPL', name: 'Apple Inc.' }
  ]);
  const [companyInput, setCompanyInput] = useState('');
  const [selectedPeerMetric, setSelectedPeerMetric] = useState('');
  const [selectedMetric1, setSelectedMetric1] = useState('Revenue');
  const [selectedMetric2, setSelectedMetric2] = useState('CostOfGoodsSold');
  const [selectedSearchMetrics, setSelectedSearchMetrics] = useState<string[]>(['revenue', 'netIncome']);
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
  const [selectedIndustryCompanies, setSelectedIndustryCompanies] = useState<CompanyTicker[]>([
    { ticker: 'AAPL', name: 'Apple Inc.' }
  ]);
  const [industryCompanyInput, setIndustryCompanyInput] = useState('');
  const [selectedIndustryMetrics, setSelectedIndustryMetrics] = useState<string[]>([]);
  const [industryMetricInput, setIndustryMetricInput] = useState('');
  const [industryChartData, setIndustryChartData] = useState<{ [metric: string]: number[] }>({});
  const [industryLoading, setIndustryLoading] = useState(false);
  const [industryError, setIndustryError] = useState<string | null>(null);
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const [availableIndustries, setAvailableIndustries] = useState<{ value: string; label: string; companies: string[] }[]>([]);
  const [industryCompanyNames, setIndustryCompanyNames] = useState<{ [metric: string]: string[] }>({});
  const [selectedTicker, setSelectedTicker] = useState('');
  const [metricSearch, setMetricSearch] = useState('');
  const [isMetricDropdownOpen, setIsMetricDropdownOpen] = useState(false);
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
  const [activeTooltip, setActiveTooltip] = useState<{ x: number; y: number; payload: any } | null>(null);
  const [stickyTooltips, setStickyTooltips] = useState<StickyTooltip[]>([]);

  // Add function to handle company selection
  const handleCompanySelection = (company: string) => {
    const [ticker, name] = company.split(':').map(s => s.trim());
    if (!selectedCompanies.some(c => c.ticker === ticker)) {
      setSelectedCompanies([...selectedCompanies, { ticker, name: name || ticker }]);
    }
  };

  const fetchAvailableMetrics = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/available-metrics/');
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

      const promises = selectedSearchMetrics.map(async metric => {
        const url = `${BASE_URL}/aggregated-data/?tickers=${ticker}&metric=${metric}&period=${selectedPeriod}`;
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
      
      // Transform the data for the chart
      const transformedData: { [key: string]: ChartDataPoint } = {};
      
      results.forEach(({ metric, data }) => {
        data.forEach((item: { name: string; value: number; ticker: string }) => {
          const period = item.name;
          if (!transformedData[period]) {
            transformedData[period] = { name: period };
          }
          // Log the value being set
          console.log(`Setting ${metric} value for ${period}:`, item.value);
          transformedData[period][metric] = item.value || 0;
        });
      });

      const sortedData = Object.values(transformedData).sort((a, b) => {
        const yearA = parseInt(a.name.split('-')[0]);
        const yearB = parseInt(b.name.split('-')[0]);
        return yearA - yearB;
      });

      console.log('Final transformed chart data:', sortedData);
      setChartData(sortedData);

      if (sortedData.length > 0 && console.log(
        'Last data point:',
        sortedData[sortedData.length - 1].name,
        'Metrics:',
        selectedSearchMetrics
      )) {
        // Additional logic if needed
      }
    } catch (error) {
      console.error('Error fetching metric data:', error);
      setError('Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  }, [searchValue, selectedSearchMetrics, selectedPeriod]);

  const fetchPeerData = useCallback(async () => {
    if (!selectedCompanies.length || !selectedPeerMetric) return;
    
    setPeerLoading(true);
    setPeerError(null);
    
    try {
      // Extract tickers from selectedCompanies
      const tickers = selectedCompanies.map(company => company.ticker);
      console.log('Fetching peer data for tickers:', tickers, 'metric:', selectedPeerMetric);

      const url = `${BASE_URL}/aggregated-data/?tickers=${tickers.join(',')}&metric=${selectedPeerMetric}&period=${selectedPeriod}`;
      console.log('Fetching from URL:', url);

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch peer data');
      }
      const data = await response.json();
      console.log('Raw peer data:', data);

      // Transform the data for the chart
      const transformedData: { [key: string]: PeerDataPoint } = {};
      
      data.forEach((item: { name: string; value: number; ticker: string }) => {
        const period = item.name;
        if (!transformedData[period]) {
          transformedData[period] = { name: period };
        }
        transformedData[period][item.ticker] = item.value || 0;
      });

      const sortedData = Object.values(transformedData).sort((a, b) => {
        const yearA = parseInt(a.name.split('-')[0]);
        const yearB = parseInt(b.name.split('-')[0]);
        return yearA - yearB;
      });

      console.log('Transformed peer chart data:', sortedData);
      setPeerChartData(sortedData);
    } catch (error) {
      console.error('Error fetching peer data:', error);
      setPeerError('Failed to fetch peer data');
    } finally {
      setPeerLoading(false);
    }
  }, [selectedCompanies, selectedPeerMetric, selectedPeriod]);

  const fetchIndustryData = useCallback(async () => {
    if (selectedIndustryMetrics.length === 0 || !selectedIndustry) return;
    
    setIndustryLoading(true);
    setIndustryError(null);
    
    try {
      const metricsParams = selectedIndustryMetrics.map(m => `metric[]=${encodeURIComponent(m)}`).join('&');
      const url = `${BASE_URL}/boxplot-data/?${metricsParams}&period=${selectedPeriod}&industry=${encodeURIComponent(selectedIndustry)}`;
      console.log('Fetching from URL:', url);

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch industry data');
      }
      const data = await response.json();
      console.log('Raw industry data:', data);

      setIndustryChartData(data.values || {});
      setIndustryCompanyNames(data.companyNames || {});
      setSelectedIndustryCompanies([]);

    } catch (error) {
      console.error('Error fetching industry data:', error);
      setIndustryError('Failed to fetch industry data');
    } finally {
      setIndustryLoading(false);
    }
  }, [selectedIndustryMetrics, selectedPeriod, selectedIndustry]);

  const fetchAvailableIndustries = async () => {
    try {
      const response = await fetch(`${BASE_URL}/industries/`);
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

  const handleIndustrySelection = (industryName: string) => {
    console.log('Selected industry:', industryName);
    setSelectedIndustry(industryName);
    
    // Find the selected industry's companies but don't display them in search box
    const selectedIndustryData = availableIndustries.find(ind => ind.value === industryName);
    if (selectedIndustryData && selectedIndustryData.companies) {
      // Store companies for the box plot hover but clear the search box
      setSelectedIndustryCompanies([]);
      setIndustryCompanyInput('');
      
      if (selectedIndustryMetrics.length > 0) {
        fetchIndustryData();
      }
    }
  };

  useEffect(() => {
    fetchAvailableMetrics();
  }, []);

  useEffect(() => {
    if (activeChart === 'metrics') {
      fetchMetricData();
    }
  }, [searchValue, selectedSearchMetrics, activeChart, selectedPeriod, fetchMetricData]);

  useEffect(() => {
    if (activeChart === 'peers') {
      fetchPeerData();
    }
  }, [activeChart, selectedCompanies, selectedPeerMetric, selectedPeriod, fetchPeerData]);

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

  const toggleSidebar = () => {
    setIsSidebarVisible(!isSidebarVisible);
  };

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
              <div className="lg:mr-[33%] absolute top-1">
                <img 
                  src="/GetDeeperIcons.png" 
                  alt="Pro" 
                  className="w-28 h-28 sm:w-32 sm:h-32 lg:w-47 lg:h-31"
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
                        Annual
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('2Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '2Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        Every 2Ys
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('3Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '3Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        Every 3Ys
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('5Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '5Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        Every 5Ys
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('10Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '10Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        Every 10Ys
                      </button>
                      <button 
                        onClick={() => setSelectedPeriod('15Y')}
                        className={`px-4 py-1 rounded text-sm ${
                          selectedPeriod === '15Y' 
                            ? 'bg-[#E5F0F6] text-[#1B5A7D]' 
                            : 'text-gray-600'
                        }`}
                      >
                        Every 15Ys
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
                <div className="relative">
                <div className="flex flex-wrap gap-2 p-2 border border-gray-200 rounded min-h-[42px]">
                  {selectedCompanies.map((company, index) => (
                    <div 
                      key={index} 
                      className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded text-sm"
                    >
                      {company.ticker}
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
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && companyInput) {
                            const [ticker, name] = companyInput.split(':').map(s => s.trim());
                            if (!selectedCompanies.some(c => c.ticker === ticker)) {
                              setSelectedCompanies([...selectedCompanies, { ticker, name: name || ticker }]);
                            }
                        setCompanyInput('');
                      }
                    }}
                        placeholder="Enter ticker and press Enter..."
                    className="flex-1 min-w-[100px] outline-none text-sm"
                  />
                  </div>
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
                        .map(ticker => (
                          <div
                            key={ticker}
                            onClick={() => {
                              setSelectedTicker(ticker);
                              setCompanySearch('');
                              setShowCompanyDropdown(false);
                            }}
                            className="px-3 py-2 text-sm xl:text-base hover:bg-gray-100 cursor-pointer"
                          >
                            {ticker}
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="relative">
                  <input
                    type="text"
                    value={searchValue}
                    onChange={(e) => setSearchValue(e.target.value)}
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

                <div className="h-[300px] sm:h-[400px] xl:h-[500px]">
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
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart 
                          data={chartData}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                          <XAxis 
                            dataKey="name" 
                            tickFormatter={(name) => {
                              // Handle year ranges like "2024-2024" -> "2024"
                              if (name.includes('-')) {
                                const [startYear] = name.split('-');
                                return startYear;
                              }
                              return name;
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
                            formatter={(value: number, name, props) => [
                              new Intl.NumberFormat('en-US', {
                                notation: 'compact',
                                maximumFractionDigits: 1
                              }).format(value),
                              // Clean the metric name display
                              availableMetrics.find(m => m.value === name)?.label || name
                            ]}
                            labelFormatter={(label) => {
                              // Handle year ranges in tooltip label
                              if (typeof label === 'string' && label.includes('-')) {
                                const [startYear] = label.split('-');
                                return startYear;
                              }
                              return label;
                            }}
                            contentStyle={{ 
                              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                            }}
                            itemStyle={{ padding: 0 }}
                            filterNull={true}
                          />

                          {/* Fixed tooltip for 2024 data points */}
                          {chartData.length > 0 && chartData[chartData.length - 1].name.startsWith('2024') && (
                            <Tooltip
                              key="fixed-2024"
                              active={true}
                              position={{
                                x: document.querySelector('.recharts-cartesian-axis-ticks')?.lastElementChild?.getBoundingClientRect().x || 0,
                                y: 100
                              }}
                              payload={selectedSearchMetrics.map(metric => ({
                                name: availableMetrics.find(m => m.value === metric)?.label || metric,
                                value: Number(chartData[chartData.length - 1][metric]) || 0,
                                dataKey: metric,
                                color: metricColors[metric]?.color || '#000',
                                payload: chartData[chartData.length - 1]
                              }))}
                              formatter={(value: number) => new Intl.NumberFormat('en-US', {
                                notation: 'compact',
                                maximumFractionDigits: 1
                              }).format(value)}
                              contentStyle={{
                                backgroundColor: 'white',
                                border: '1px solid #ccc',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                zIndex: 10000
                              }}
                              wrapperStyle={{
                                visibility: 'visible !important',
                                position: 'absolute',
                                zIndex: 10000,
                                pointerEvents: 'none'
                              }}
                            />
                          )}

                          <Legend />
                          {selectedSearchMetrics.map((metric) => {
                            const metricConfig = metricColors[metric] || {
                              color: generateColorPalette(1)[0],
                              label: availableMetrics.find(m => m.value === metric)?.label || metric
                            };
                            return (
                              <Line
                                key={metric}
                                type="monotone"
                                dataKey={metric}
                                stroke={metricConfig.color}
                                name={metricConfig.label}
                                strokeWidth={2}
                                dot={{
                                  fill: metricConfig.color,
                                  r: 4
                                }}
                              />
                            );
                          })}
                        </LineChart>
                      </ResponsiveContainer>
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
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart 
                          data={peerChartData}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                          <XAxis 
                            dataKey="name" 
                            tickFormatter={(name) => {
                              // Handle year ranges like "2024-2024" -> "2024"
                              if (name.includes('-')) {
                                const [startYear] = name.split('-');
                                return startYear;
                              }
                              return name;
                            }}
                          />
                          <YAxis 
                            tickFormatter={(value) => new Intl.NumberFormat('en-US', {
                              notation: 'compact',
                              maximumFractionDigits: 1
                            }).format(value)}
                          />
                          <Tooltip 
                            formatter={(value: number) => new Intl.NumberFormat('en-US', {
                              notation: 'compact',
                              maximumFractionDigits: 1
                            }).format(value)}
                            labelFormatter={(label) => {
                              if (typeof label === 'string' && label.includes('-')) {
                                const [startYear] = label.split('-');
                                return startYear;
                              }
                              return label;
                            }}
                            contentStyle={{ 
                              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                            }}
                            itemStyle={{ padding: 0 }}
                          />
                          <Legend />
                          {selectedCompanies.map((company, index) => {
                            const color = generateColorPalette(selectedCompanies.length)[index];
                            const metricLabel = availableMetrics.find(m => m.value === selectedPeerMetric)?.label || selectedPeerMetric;
                            return (
                              <Line
                                key={company.ticker}
                                type="monotone"
                                dataKey={company.ticker}
                                stroke={color}
                                name={`${company.ticker} - ${metricLabel}`}
                                strokeWidth={2}
                                dot={{
                                  fill: color,
                                  r: 4
                                }}
                              />
                            );
                          })}
                        </LineChart>
                      </ResponsiveContainer>
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
                    ) : industryChartData.length === 0 ? (
                      <div className="flex items-center justify-center h-full text-gray-500">
                        No data available
                      </div>
                    ) : (
                      <BoxPlot
                        data={industryChartData}
                        title={selectedIndustryMetrics.map(metric => 
                          availableMetrics.find(m => m.value === metric)?.label || metric
                        ).join(' vs ')}
                        companyNames={industryCompanyNames}
                        selectedTicker={selectedTicker}
                      />
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
            </div>

            {/* Insights Generation - full width on mobile */}
            <div className="lg:col-span-4 lg:mr-[-11rem]">
              <div className="mt-0 lg:mt-2 sm:mt-3 lg:mt-4">
                <div className="bg-white rounded-lg shadow-sm">
                  <div className="p-4 xl:p-6 border-b flex justify-between items-center">
                    <div className="flex items-center gap-2 xl:gap-3">
                      <h2 className="text-lg sm:text-xl xl:text-2xl font-medium">Insights Generation</h2>
                      <button className="w-8 xl:w-10 h-8 xl:h-10 bg-[#1B5A7D] text-white rounded text-xl">+</button>
                    </div>
                    <button className="px-3 xl:px-4 py-2 text-sm xl:text-base bg-[#1B5A7D] text-white rounded">
                      Save Report
                    </button>
                  </div>
                  
                  {/* Chat Messages */}
                  <div className="h-[400px] sm:h-[500px] xl:h-[600px] overflow-y-auto p-4 xl:p-6 space-y-4">
                    {/* Message bubbles with responsive text and spacing */}
                    <div className="flex gap-3 xl:gap-4">
                      <div className="w-8 xl:w-10 h-8 xl:h-10 bg-[#1B5A7D] rounded-full flex items-center justify-center text-white text-sm xl:text-base">
                        AI
                      </div>
                      <div className="flex-1">
                        <div className="bg-[#E5F0F6] rounded-lg p-3 xl:p-4 text-sm xl:text-base">
                          I can help you analyze this data. What would you like to know?
                        </div>
                      </div>
                    </div>

                    {/* User Message */}
                    <div className="flex gap-3 justify-end xl:gap-4">
                      <div className="flex-1">
                        <div className="bg-gray-100 rounded-lg p-3 xl:p-4 text-sm xl:text-base ml-auto max-w-[80%]">
                          What's the trend in revenue growth?
                        </div>
                      </div>
                      <div className="w-8 xl:w-10 h-8 xl:h-10 bg-gray-200 rounded-full flex items-center justify-center text-sm xl:text-base">
                        AM
                      </div>
                    </div>

                    {/* AI Response */}
                    <div className="flex gap-3 xl:gap-4">
                      <div className="w-8 xl:w-10 h-8 xl:h-10 bg-[#1B5A7D] rounded-full flex items-center justify-center text-white text-sm xl:text-base">
                        AI
                      </div>
                      <div className="flex-1">
                        <div className="bg-[#E5F0F6] rounded-lg p-3 xl:p-4 text-sm xl:text-base">
                          Based on the chart, revenue shows an overall upward trend from Jan '16 to Jul '18, with notable growth from $15,000 to $23,000. There was particularly strong growth in the last period, from Jan '18 to Jul '18.
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Chat Input */}
                  <div className="p-4 xl:p-6 border-t">
                    <div className="flex gap-2 xl:gap-3">
            <input 
              type="text" 
                        placeholder="Ask Me Anything..."
                        className="flex-1 px-3 xl:px-4 py-2 xl:py-3 text-sm xl:text-base border rounded-lg"
                      />
                      <button className="p-2 xl:p-3">
                        <img src="/mic-icon.svg" alt="Voice" className="w-5 xl:w-6 h-5 xl:h-6" />
                      </button>
                      <button className="p-2 xl:p-3">
                        <img src="/send-icon.svg" alt="Send" className="w-5 xl:w-6 h-5 xl:h-6" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
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
    </div>
  );
};

export default Dashboard; 