import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Legend } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

const API_URL = (ticker: string) => `http://127.0.0.1:8000/api/chart-data/?ticker=${ticker}`;
const WS_URL = "ws://127.0.0.1:8000/ws/revenue/";

interface ChartDataPoint {
  name: string;
  revenue: number;
  profit: number;
}

interface OverviewProps {
  ticker: string;
}

export function Overview({ ticker }: OverviewProps) {
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Fetch historical revenue & profit data from backend
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(API_URL(ticker));
        const result = await response.json();

        console.log("API Response:", result);

        if (!result.metrics || result.metrics.length === 0) {
          setError("No financial data available for this ticker.");
          setData([]);
          return;
        }

        // Create a map to store revenue and profit by period
        const formattedData = result.metrics.map((item: { period: string; revenue: number; profit: number }) => ({
          name: item.period, // Ensure this matches the period field from the API
          revenue: item.revenue,
          profit: item.profit,
        }));

        console.log("Formatted Data:", formattedData);

        setData(formattedData);
        setError(null);
      } catch (error) {
        console.error("Error fetching financial data:", error);
        setError("Error fetching financial data.");
      }
    };

    fetchData();
  }, [ticker]);

  // WebSocket for real-time updates
  useEffect(() => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => console.log("✅ WebSocket Connected!");
    
    ws.onerror = (e) => console.error("❌ WebSocket Error:", e);
    
    ws.onmessage = (event) => {
      try {
        const newData = JSON.parse(event.data);
        console.log("📊 Received Data:", newData);

        setData((prevData) => {
          if (prevData.length >= 12) prevData.shift();
          return [...prevData, {
            name: newData.period, 
            revenue: newData.revenue, 
            profit: newData.profit || 0,
          }];
        });
      } catch (error) {
        console.error("❌ Error parsing WebSocket data:", error);
      }
    };

    ws.onclose = (event) => console.warn(`❌ WebSocket Closed (Code: ${event.code}, Reason: ${event.reason})`);

    return () => {
      ws.close();
    };
  }, []);

  return (
    <ChartContainer
      config={{
        revenue: { label: "Revenue", color: "hsl(240 50% 50%)" },
        profit: { label: "Profit", color: "hsl(10 80% 50%)" },
      }}
      className="h-[300px]"
    >
      {error ? (
        <div className="flex items-center justify-center h-full text-center text-red-500">
          {error}
        </div>
      ) : (
        <LineChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" tickLine={false} axisLine={false} tickMargin={10} />
          <YAxis tickLine={false} axisLine={false} tickMargin={10} tickFormatter={(value) => `$${value}`} />
          <ChartTooltip content={<ChartTooltipContent />} cursor={false} />
          <Legend />
          <Line
            type="monotone"
            dataKey="revenue"
            strokeWidth={2}
            activeDot={{ r: 6, style: { fill: "hsl(240 50% 50%)", opacity: 0.25 } }}
            stroke="hsl(240 50% 50%)"
            name="Revenue"
          />
          <Line
            type="monotone"
            dataKey="profit"
            strokeWidth={2}
            activeDot={{ r: 6, style: { fill: "hsl(10 80% 50%)", opacity: 0.25 } }}
            stroke="hsl(10 80% 50%)"
            name="Profit"
          />
        </LineChart>
      )}
    </ChartContainer>
  );
}

export default Overview;
