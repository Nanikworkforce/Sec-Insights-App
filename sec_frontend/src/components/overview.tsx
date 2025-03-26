import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Legend } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

const API_URL = "http://127.0.0.1:8000/api/chart-data/?ticker=AAPL";
const WS_URL = "ws://127.0.0.1:8000/ws/revenue/";

// Define an interface for your API response items
interface ChartDataPoint {
  name: string;
  revenue: number;
  profit: number;
}

export function Overview() {
  const [data, setData] = useState<ChartDataPoint[]>([]);

  // Fetch historical revenue & profit data from backend
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(API_URL);
        const result = await response.json();

        console.log("API Response:", result);

        if (!result.metrics) {
          console.error("No data returned for the company.");
          return;
        }

        // Create a map to store revenue and profit by period
        const dataMap: { [key: string]: { revenue: number; profit: number } } = {};

        result.metrics.forEach((item: { period: number; metric_name: string; value: number }) => {
          const periodName = `Period ${item.period}`; // Adjust this to your period naming convention

          if (!dataMap[periodName]) {
            dataMap[periodName] = { revenue: 0, profit: 0 };
          }

          if (item.metric_name === "Revenue") {
            dataMap[periodName].revenue = item.value;
          } else if (item.metric_name === "Profit") {
            dataMap[periodName].profit = item.value;
          }
        });

        const formattedData = Object.entries(dataMap).map(([name, values]) => ({
          name,
          revenue: values.revenue,
          profit: values.profit,
        }));

        console.log("Formatted Data:", formattedData);

        setData(formattedData);
      } catch (error) {
        console.error("Error fetching financial data:", error);
      }
    };

    fetchData();
  }, []);

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
    </ChartContainer>
  );
}

export default Overview;
