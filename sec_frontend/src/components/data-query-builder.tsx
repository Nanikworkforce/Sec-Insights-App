
import { useState } from "react"
import { PlusCircle, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export function DataQueryBuilder() {
  const [filters, setFilters] = useState([{ field: "", operator: "", value: "" }])
  const [dataSource, setDataSource] = useState<string>("")
  const [grouping, setGrouping] = useState<string>("none")
  const [startDate, setStartDate] = useState<string>("")
  const [endDate, setEndDate] = useState<string>("")

  const addFilter = () => {
    setFilters([...filters, { field: "", operator: "", value: "" }])
  }

  const removeFilter = (index: number) => {
    const newFilters = [...filters]
    newFilters.splice(index, 1)
    setFilters(newFilters)
  }

  const updateFilter = (index: number, key: string, value: string) => {
    const newFilters = [...filters]
    newFilters[index] = { ...newFilters[index], [key]: value }
    setFilters(newFilters)
  }

  const handleRunQuery = () => {
    if (!dataSource) {
      alert("Please select a data source.")
      return
    }
    if (!startDate || !endDate) {
      alert("Please select a valid time period.")
      return
    }
    console.log("Running query with the following parameters:", {
      dataSource,
      startDate,
      endDate,
      filters,
      grouping,
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Query Builder</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="data-source">Data Source</Label>
          <Select value={dataSource} onValueChange={setDataSource}>
            <SelectTrigger id="data-source" aria-label="Select data source">
              <SelectValue placeholder="Select data source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="revenue">Revenue Data</SelectItem>
              <SelectItem value="expenses">Expense Data</SelectItem>
              <SelectItem value="customers">Customer Data</SelectItem>
              <SelectItem value="products">Product Data</SelectItem>
              <SelectItem value="market">Market Data</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Time Period</Label>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label htmlFor="start-date" className="sr-only">
                Start Date
              </Label>
              <Input
                type="date"
                id="start-date"
                placeholder="Start date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="end-date" className="sr-only">
                End Date
              </Label>
              <Input
                type="date"
                id="end-date"
                placeholder="End date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Filters</Label>
            <Button variant="ghost" size="sm" onClick={addFilter} className="h-8 px-2">
              <PlusCircle className="mr-1 h-4 w-4" />
              Add Filter
            </Button>
          </div>

          {filters.map((filter, index) => (
            <div key={index} className="flex items-center space-x-2">
              <Select
                value={filter.field}
                onValueChange={(value) => updateFilter(index, "field", value)}
              >
                <SelectTrigger className="w-[30%]" aria-label="Select field">
                  <SelectValue placeholder="Field" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="revenue">Revenue</SelectItem>
                  <SelectItem value="profit">Profit</SelectItem>
                  <SelectItem value="margin">Margin</SelectItem>
                  <SelectItem value="region">Region</SelectItem>
                  <SelectItem value="product">Product</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={filter.operator}
                onValueChange={(value) => updateFilter(index, "operator", value)}
              >
                <SelectTrigger className="w-[30%]" aria-label="Select operator">
                  <SelectValue placeholder="Operator" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="equals">Equals</SelectItem>
                  <SelectItem value="greater_than">Greater Than</SelectItem>
                  <SelectItem value="less_than">Less Than</SelectItem>
                  <SelectItem value="contains">Contains</SelectItem>
                  <SelectItem value="starts_with">Starts With</SelectItem>
                  <SelectItem value="ends_with">Ends With</SelectItem>
                </SelectContent>
              </Select>

              <Input
                className="w-[30%]"
                placeholder="Value"
                value={filter.value}
                onChange={(e) => updateFilter(index, "value", e.target.value)}
              />

              <Button
                variant="ghost"
                size="icon"
                onClick={() => removeFilter(index)}
                disabled={filters.length === 1}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <Label htmlFor="grouping">Group By</Label>
          <Select value={grouping} onValueChange={setGrouping}>
            <SelectTrigger id="grouping" aria-label="Select grouping">
              <SelectValue placeholder="Select grouping" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem value="month">Month</SelectItem>
              <SelectItem value="quarter">Quarter</SelectItem>
              <SelectItem value="year">Year</SelectItem>
              <SelectItem value="region">Region</SelectItem>
              <SelectItem value="product">Product</SelectItem>
              <SelectItem value="category">Category</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
      <CardFooter>
        <Button className="w-full" onClick={handleRunQuery}>
          Run Query
        </Button>
      </CardFooter>
    </Card>
  )
}

