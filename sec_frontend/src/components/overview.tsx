import { useEffect, useState, useCallback } from "react";
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Legend, Tooltip } from "recharts";
import { ChartContainer } from "@/components/ui/chart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import BoxPlot from './BoxPlot';

const BASE_URL = import.meta.env.VITE_API_BASE_URL + 'api';

const API_URL = (tickers: string[], metric: string, period: string) => 
  `${BASE_URL}/aggregated-data/?tickers=${tickers.join(',')}&metric=${metric}&period=${period}`;
const WS_URL = "ws://127.0.0.1:8000/ws/revenue/";
const INDUSTRY_API_URL = `${BASE_URL}/industry-comparison`;

interface MetricItem {
  period: string;
  values: {
    [key: string]: number;
  };
}

interface ChartDataPoint {
  name: string;
  [key: string]: string | number; // Allow dynamic metric keys
}

interface IndustryData {
  name: string;
  companies: string[];
}

interface OverviewProps {
  selectedTicker: string;
}

// Define available metrics
const METRICS = {
  revenue: { label: "Revenue", color: "hsl(240 50% 50%)" },
  netIncome: { label: "Net Income", color: "hsl(10 80% 50%)" },
  operatingCashFlow: { label: "Operating Cash Flow", color: "hsl(150 50% 50%)" },
  freeCashFlow: { label: "Free Cash Flow", color: "hsl(280 50% 50%)" },
  totalAssets: { label: "Total Assets", color: "hsl(200 50% 50%)" },
  TotalLiabilities: { label: "Total Liabilities", color: "hsl(170 50% 50%)" },
  currentAssets: { label: "Current Assets", color: "hsl(320 50% 50%)" },
  currentLiabilities: { label: "Current Liabilities", color: "hsl(90 50% 50%)" },
  cash: { label: "Cash", color: "hsl(45 50% 50%)" },
  inventory: { label: "Inventory", color: "hsl(120 50% 50%)" },
  receivables: { label: "Receivables", color: "hsl(200 50% 50%)" },
  grossMargin: { label: "Gross Margin", color: "hsl(250 50% 50%)" },
  operatingMargin: { label: "Operating Margin", color: "hsl(300 50% 50%)" },
  returnOnEquity: { label: "Return on Equity", color: "hsl(350 50% 50%)" },
  returnOnAssets: { label: "Return on Assets", color: "hsl(30 50% 50%)" }
} as const;

// Define ticker colors
const TICKER_COLORS = {
  'AAPL': "hsl(240 50% 50%)",
  'GOOGL': "hsl(10 80% 50%)",
  'MSFT': "hsl(150 50% 50%)",
  'AMZN': "hsl(280 50% 50%)",
  'META': "hsl(200 50% 50%)",
  'AAON': "hsl(150 70% 50%)",
  'AAP': "hsl(200 50% 80%)",
  'AAPG': "hsl(100 50% 80%)",
} as const;

type MetricKey = keyof typeof METRICS;
type TickerKey = keyof typeof TICKER_COLORS;

// Define available metrics and periods
const AVAILABLE_METRICS = ['revenue', 'netIncome', 'operatingCashFlow'];

const Overview: React.FC<OverviewProps> = ({ selectedTicker: ticker }) => {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<MetricKey>("revenue");
  const [tickers, setTickers] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState("metrics");
  const [selectedIndustries, setSelectedIndustries] = useState<string[]>([]);
  const [availableIndustries, setAvailableIndustries] = useState<IndustryData[]>([]);
  const [selectedBoxPlotMetric, setSelectedBoxPlotMetric] = useState(AVAILABLE_METRICS[0]);
  const [selectedPeriod, setSelectedPeriod] = useState('1Y');
  const [searchQueries, setSearchQueries] = useState<string[]>([]);
  const [industryCompanyNames, setIndustryCompanyNames] = useState<Record<string, string[]>>({});

  // Optional: Add sample data initialization
  useEffect(() => {
    setIndustryCompanyNames({
      automotive: ['Ford', 'GM', 'Tesla'],
      technology: ['Apple', 'Microsoft', 'Google'],
      healthcare: ['Pfizer', 'Moderna', 'Johnson & Johnson']
    });
  }, []);

  // Fetch historical data from backend
  useEffect(() => {
    const fetchData = async () => {
      try {
        if (tickers.length === 0) return;
        
        const response = await fetch(API_URL(tickers, selectedMetric, selectedPeriod));
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const result = await response.json();

        console.log('API Result:', result);

        // Process the response - result is already an array from aggregated-data endpoint
        if (Array.isArray(result)) {
          const chartData: ChartDataPoint[] = result.reduce((acc: ChartDataPoint[], item) => {
            // Find existing entry with the same name or create a new one
            let entry = acc.find(e => e.name === item.name);
            if (!entry) {
              entry = { name: item.name } as ChartDataPoint;
              acc.push(entry);
            }
            // Add the ticker's value to the entry
            entry[item.ticker] = item.value;
            return acc;
          }, []);
        
        setData(chartData);
          console.log('Chart Data:', chartData);
        } else {
          throw new Error('Unexpected response format');
        }

        setError(null);
      } catch (error) {
        setError('Failed to fetch data');
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, [tickers, selectedMetric, selectedPeriod]);

  // WebSocket for real-time updates
  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => console.log("WebSocket Connected!");
    
    ws.onerror = (e) => console.error("WebSocket Error:", e);
    
    ws.onmessage = (event) => {
      try {
        const newData = JSON.parse(event.data);
        console.log("📊 Received Data:", newData);

        setData((prevData) => {
          if (prevData.length >= 12) prevData.shift();
          return [...prevData, {
            name: newData.metric_name,
            value: newData.value,
          }];
        });
      } catch (error) {
        console.error("❌ Error parsing WebSocket data:", error);
      }
    };

    ws.onclose = (event) => console.warn(`❌ WebSocket Closed (Code: ${event.code})`);

    return () => {
      ws.close();
    };
  }, []);

  // Update the fetchIndustryData function
  const fetchIndustryData = useCallback(async () => {
    if (selectedIndustries.length === 0) return;
    
    setError(null);
    try {
      // Create URLSearchParams without pre-encoding the industry names
      const queryParams = new URLSearchParams();
      queryParams.append('industries', selectedIndustries.join(','));
      queryParams.append('metric', selectedMetric);
      queryParams.append('show_companies', 'false');

      const url = `${INDUSTRY_API_URL}/?${queryParams}`;
      console.log('Fetching from URL:', url);

      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Raw Industry Data:', result);
      
      if (!result.comparisons || result.comparisons.length === 0) {
        console.log('No comparison data received');
        return;
      }

      // Transform the data to match the expected format
      const transformedData = result.comparisons.map((item: any) => {
        const dataPoint: any = {
          name: item.period
        };
        // Add the industry values using the _total suffix
        selectedIndustries.forEach((industry: string) => {
          const key = `${industry}_total`;
          if (item[key] !== undefined) {
            dataPoint[key] = item[key];
          }
        });
        return dataPoint;
      });

      setData(transformedData);
      console.log('Transformed Industry Data:', transformedData);
    } catch (error) {
      console.error('Error fetching industry data:', error);
      setError('Failed to fetch industry data');
    }
  }, [selectedIndustries, selectedMetric]);

  // Update the useEffect to trigger data fetching
  useEffect(() => {
    // Fetch data when industries are selected
    if (selectedIndustries.length > 0) {
      fetchIndustryData();
    }
  }, [selectedIndustries, selectedMetric, fetchIndustryData]);

  // Update the fetchIndustries function
  const fetchIndustries = async () => {
    try {
      const response = await fetch(`${BASE_URL}/industries/`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Fetched industries:', data);
      setAvailableIndustries(data.industries);
    } catch (error) {
      console.error('Error fetching industries:', error);
      setError('Failed to fetch industries');
    }
  };

  // Add useEffect for fetching industries
  useEffect(() => {
    fetchIndustries();
  }, []);

  const handleAddTicker = (newTicker: string) => {
    if (!tickers.includes(newTicker)) {
      setTickers([...tickers, newTicker]);
    }
  };

  const handleRemoveTicker = (tickerToRemove: string) => {
    setTickers(tickers.filter(t => t !== tickerToRemove));
  };

  // Update industry selection handlers
  const handleAddIndustry = (industry: string) => {
    if (!selectedIndustries.includes(industry)) {
      setSelectedIndustries([...selectedIndustries, industry]);
    }
  };

  const handleRemoveIndustry = (industry: string) => {
    setSelectedIndustries(selectedIndustries.filter(i => i !== industry));
  };

  // Update the fetchCombinedData function
  useEffect(() => {
    const fetchAllData = async () => {
      if (activeTab !== "metrics" || (tickers.length === 0 && selectedIndustries.length === 0)) {
        return;
      }

      setError(null);

      try {
        // Fetch both company and industry data in parallel
        const promises = [];
        
        if (tickers.length > 0) {
          promises.push(
            fetch(API_URL(tickers, selectedMetric, selectedPeriod))
              .then(res => res.ok ? res.json() : Promise.reject(`Company data: ${res.status}`))
          );
        }
        
        if (selectedIndustries.length > 0) {
          const queryParams = new URLSearchParams({
            industries: selectedIndustries.join(','),
            metric: selectedMetric,
            show_companies: 'false'
          });
          promises.push(
            fetch(`${INDUSTRY_API_URL}/?${queryParams}`)
              .then(res => res.ok ? res.json() : Promise.reject(`Industry data: ${res.status}`))
          );
        }

        const results = await Promise.all(promises);
        
        // Process and combine the data
        const periodMap = new Map<string, any>();

        // Process company data if it exists
        if (results[0]?.metrics) {
          results[0].metrics.forEach((item: MetricItem) => {
            periodMap.set(item.period, {
              period: item.period,
              ...item.values
            });
          });
        }

        // Process industry data if it exists
        if (results[1]?.comparisons) {
          results[1].comparisons.forEach((item: any) => {
            const existingData = periodMap.get(item.period) || { period: item.period };
            
            selectedIndustries.forEach(industry => {
              if (item[`${industry}_total`] !== undefined) {
                existingData[`${industry}_avg`] = item[`${industry}_total`];
              }
            });

            periodMap.set(item.period, existingData);
          });
        }

      } catch (error) {
        console.error('Error fetching data:', error);
        setError('Failed to fetch data');
      }
    };

    fetchAllData();
  }, [activeTab, tickers, selectedIndustries, selectedMetric, selectedPeriod]);

  const handlePeriodChange = (period: string) => {
    setSelectedPeriod(period);
    // You might want to trigger data fetching here based on the selected period
  };

  // Add a new function to handle adding search queries
  const handleAddSearchQuery = (query: string) => {
    if (!searchQueries.includes(query)) {
      setSearchQueries([...searchQueries, query]);
    }
  };

  // Add a function to remove search queries
  const handleRemoveSearchQuery = (query: string) => {
    setSearchQueries(searchQueries.filter(q => q !== query));
  };

  return (
    <div className="space-y-4">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="metrics">Company Metrics</TabsTrigger>
          <TabsTrigger value="boxplot">Box Plot</TabsTrigger>
        </TabsList>

        <TabsContent value="metrics">
          <div className="flex items-center gap-2">
            {/* Ticker Search Bar */}
            <div className="flex flex-wrap items-center gap-2 border rounded-md p-1">
              {tickers.map((ticker) => (
                <div
                  key={ticker}
                  className="flex items-center gap-1 px-2 py-1 text-sm bg-gray-100 rounded"
                >
                  {ticker}
                  <button
                    onClick={() => handleRemoveTicker(ticker)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ×
                  </button>
                </div>
              ))}
              <input
                type="text"
                placeholder="Add tickers..."
                className="px-2 py-1 text-sm focus:outline-none min-w-[100px] flex-grow"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const value = e.currentTarget.value.toUpperCase();
                    if (value) {
                      handleAddTicker(value);
                      e.currentTarget.value = '';
                    }
                  }
                }}
              />
            </div>

            {/* Add Industry Selection */}
            <div className="flex flex-wrap items-center gap-2">
              {selectedIndustries.map((industry) => (
                <div
                  key={industry}
                  className="flex items-center gap-1 px-2 py-1 text-sm bg-blue-100 rounded"
                >
                  {industry}
                  <button
                    onClick={() => handleRemoveIndustry(industry)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ×
                  </button>
                </div>
              ))}
              <Select
                value=""
                onValueChange={handleAddIndustry}
              >
                <SelectTrigger className="w-[250px]">
                  <SelectValue placeholder="Add industry average..." />
                </SelectTrigger>
                <SelectContent>
                  {availableIndustries.map((industry) => (
                    <SelectItem 
                      key={industry.name} 
                      value={industry.name}
                      disabled={selectedIndustries.includes(industry.name)}
                    >
                      <span className="flex items-center justify-between w-full">
                        <span>{industry.name}</span>
                        <span className="text-gray-500 text-sm">
                          ({industry.companies.length})
                        </span>
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Spacer */}
            <div className="flex-1" />

            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Select Metric:</span>
              <Select
                value={selectedMetric}
                onValueChange={(value: MetricKey) => setSelectedMetric(value)}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select a metric" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(METRICS).map(([key, { label }]) => (
                    <SelectItem key={key} value={key}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline">Options</Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem>Option 1</DropdownMenuItem>
                  <DropdownMenuItem>Option 2</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          <div className="flex items-center gap-2 mb-4">
            {['1Y', '2Y', '3Y', '5Y', '10Y', '15Y','ALL'].map((period) => (
              <button
                key={period}
                onClick={() => handlePeriodChange(period)}
                className={`px-2 py-1 text-sm rounded ${
                  selectedPeriod === period ? 'bg-gray-300' : 'bg-gray-100'
                }`}
              >
                {period}
              </button>
            ))}
          </div>

          {(tickers.length > 0 || selectedIndustries.length > 0) ? (
            <ChartContainer
              config={{
                ...Object.fromEntries(
                  tickers.map(ticker => [
                    ticker,
                    { label: ticker, color: TICKER_COLORS[ticker as TickerKey] || '#8884d8' }
                  ])
                ),
                ...Object.fromEntries(
                  selectedIndustries.map(industry => [
                    industry,
                    { label: `${industry} Average`, color: METRICS[selectedMetric].color }
                  ])
                )
              }}
              className="h-[300px]"
            >
              {error ? (
                <div className="flex items-center justify-center h-full text-center text-red-500">
                  {error}
                </div>
              ) : (
                <LineChart width={600} height={300} data={data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
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
                    labelFormatter={(label) => `Period: ${label}`}
                  />
                  <Legend />
                  {tickers.map((ticker) => (
                    <Line
                      key={ticker}
                      type="monotone"
                      dataKey={ticker}
                      stroke={TICKER_COLORS[ticker as TickerKey] || '#8884d8'}
                      name={ticker}
                    />
                  ))}
                  {selectedIndustries.map((industry) => (
                    <Line
                      key={industry}
                      type="monotone"
                      dataKey={`${industry}_total`}  // Use the exact key from the API response
                      stroke={METRICS[selectedMetric].color}
                      name={`${industry} Average`}
                      strokeWidth={3}
                      strokeDasharray="5 5"
                    />
                  ))}
                </LineChart>
              )}
            </ChartContainer>
          ) : (
            <div className="flex items-center justify-center h-[300px] text-gray-500">
              Add tickers or industries to view chart data
            </div>
          )}
        </TabsContent>

        <TabsContent value="boxplot">
          <div className="space-y-4">
            {/* Search input with tags */}
            <div className="flex flex-wrap items-center gap-2 p-2 border rounded-md">
              {searchQueries.map((query) => (
                <div
                  key={query}
                  className="flex items-center gap-1 px-2 py-1 text-sm bg-gray-100 rounded"
                >
                  {query}
                  <button
                    onClick={() => handleRemoveSearchQuery(query)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ×
                  </button>
                </div>
              ))}
              <input
                type="text"
                placeholder="Search tickers..."
                className="flex-1 px-2 py-1 focus:outline-none min-w-[120px]"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && e.currentTarget.value) {
                    handleAddSearchQuery(e.currentTarget.value.toUpperCase());
                    e.currentTarget.value = '';
                  }
                }}
              />
            </div>

            <div className="flex items-center gap-2 mb-4">
              <span className="text-sm font-medium">Select Metric:</span>
              <Select
                value={selectedBoxPlotMetric}
                onValueChange={setSelectedBoxPlotMetric}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select a metric" />
                </SelectTrigger>
                <SelectContent>
                  {AVAILABLE_METRICS.map((metric) => (
                    <SelectItem key={metric} value={metric}>
                      {metric}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <BoxPlot
              data={{} as { [metric: string]: (number | null)[] }}
              title={selectedIndustries.map(industry => 
                availableIndustries.find(i => i.name === industry)?.name || industry
              ).join(' vs ')}
              companyNames={{
                ...Object.fromEntries(
                  selectedIndustries.map(industry => [industry, industryCompanyNames[industry] || []])
                )
              }}
              selectedTicker={ticker}
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default Overview;
