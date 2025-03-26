"use client"

import { useState } from "react"
import { BarChart, LineChart, PieChart } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function ChartBuilder() {
  const [chartType, setChartType] = useState<string>("line")
  const [chartTitle, setChartTitle] = useState<string>("")

  const handleGenerateChart = () => {
    if (!chartTitle.trim()) {
      alert("Please enter a chart title.")
      return
    }
    // Add logic to generate the chart based on selected options
    console.log("Generating chart with title:", chartTitle)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Chart Builder</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={chartType} onValueChange={setChartType} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="line" className="flex items-center gap-2">
              <LineChart className="h-4 w-4" />
              Line
            </TabsTrigger>
            <TabsTrigger value="bar" className="flex items-center gap-2">
              <BarChart className="h-4 w-4" />
              Bar
            </TabsTrigger>
            <TabsTrigger value="pie" className="flex items-center gap-2">
              <PieChart className="h-4 w-4" />
              Pie
            </TabsTrigger>
          </TabsList>

          <TabsContent value="line" className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label htmlFor="line-x-axis">X-Axis</Label>
              <Select>
                <SelectTrigger id="line-x-axis" aria-label="Select X-Axis for Line Chart">
                  <SelectValue placeholder="Select X-Axis" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="month">Month</SelectItem>
                  <SelectItem value="quarter">Quarter</SelectItem>
                  <SelectItem value="year">Year</SelectItem>
                  <SelectItem value="category">Category</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="line-y-axis">Y-Axis</Label>
              <Select>
                <SelectTrigger id="line-y-axis" aria-label="Select Y-Axis for Line Chart">
                  <SelectValue placeholder="Select Y-Axis" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="revenue">Revenue</SelectItem>
                  <SelectItem value="profit">Profit</SelectItem>
                  <SelectItem value="margin">Profit Margin</SelectItem>
                  <SelectItem value="customers">Customer Count</SelectItem>
                  <SelectItem value="orders">Order Count</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="line-comparison">Comparison</Label>
              <Select>
                <SelectTrigger id="line-comparison" aria-label="Select Comparison for Line Chart">
                  <SelectValue placeholder="Select Comparison" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="previous_period">Previous Period</SelectItem>
                  <SelectItem value="previous_year">Previous Year</SelectItem>
                  <SelectItem value="industry">Industry Average</SelectItem>
                  <SelectItem value="forecast">Forecast</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </TabsContent>

          <TabsContent value="bar" className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label htmlFor="bar-x-axis">X-Axis</Label>
              <Select>
                <SelectTrigger id="bar-x-axis">
                  <SelectValue placeholder="Select X-Axis" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="category">Category</SelectItem>
                  <SelectItem value="product">Product</SelectItem>
                  <SelectItem value="region">Region</SelectItem>
                  <SelectItem value="month">Month</SelectItem>
                  <SelectItem value="quarter">Quarter</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="bar-y-axis">Y-Axis</Label>
              <Select>
                <SelectTrigger id="bar-y-axis">
                  <SelectValue placeholder="Select Y-Axis" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="revenue">Revenue</SelectItem>
                  <SelectItem value="profit">Profit</SelectItem>
                  <SelectItem value="margin">Profit Margin</SelectItem>
                  <SelectItem value="customers">Customer Count</SelectItem>
                  <SelectItem value="orders">Order Count</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="bar-type">Bar Type</Label>
              <Select>
                <SelectTrigger id="bar-type">
                  <SelectValue placeholder="Select Bar Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="vertical">Vertical</SelectItem>
                  <SelectItem value="horizontal">Horizontal</SelectItem>
                  <SelectItem value="stacked">Stacked</SelectItem>
                  <SelectItem value="grouped">Grouped</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </TabsContent>

          <TabsContent value="pie" className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label htmlFor="pie-data">Data Field</Label>
              <Select>
                <SelectTrigger id="pie-data">
                  <SelectValue placeholder="Select Data Field" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="revenue">Revenue</SelectItem>
                  <SelectItem value="profit">Profit</SelectItem>
                  <SelectItem value="customers">Customer Count</SelectItem>
                  <SelectItem value="orders">Order Count</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pie-segments">Segments</Label>
              <Select>
                <SelectTrigger id="pie-segments">
                  <SelectValue placeholder="Select Segments" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="category">Category</SelectItem>
                  <SelectItem value="product">Product</SelectItem>
                  <SelectItem value="region">Region</SelectItem>
                  <SelectItem value="channel">Channel</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pie-type">Chart Type</Label>
              <Select>
                <SelectTrigger id="pie-type">
                  <SelectValue placeholder="Select Chart Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pie">Pie</SelectItem>
                  <SelectItem value="donut">Donut</SelectItem>
                  <SelectItem value="radial">Radial</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </TabsContent>
        </Tabs>

        <div className="space-y-2">
          <Label htmlFor="chart-title">Chart Title</Label>
          <Input
            id="chart-title"
            placeholder="Enter chart title"
            value={chartTitle}
            onChange={(e) => setChartTitle(e.target.value)}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button className="w-full" onClick={handleGenerateChart}>
          Generate Chart
        </Button>
      </CardFooter>
    </Card>
  )
}

