import { AlertCircle, ArrowDown, ArrowUp, TrendingDown, TrendingUp } from "lucide-react"

import { Alert, AlertDescription, AlertTitle } from "./alert"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export function InsightsPanel() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Key Insights</CardTitle>
          <CardDescription>AI-generated analysis of your financial data</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert className="border-green-200 bg-green-50 text-green-800">
            <TrendingUp className="h-4 w-4 text-green-600" aria-label="Positive Trend Icon" />
            <AlertTitle className="text-green-800">Positive Trend</AlertTitle>
            <AlertDescription className="text-green-700">
              Your Q1 revenue has increased by 15% compared to the same period last year, outperforming the industry
              average of 8%.
            </AlertDescription>
          </Alert>

          <Alert className="border-red-200 bg-red-50 text-red-800">
            <TrendingDown className="h-4 w-4 text-red-600" aria-label="Negative Trend Icon" />
            <AlertTitle className="text-red-800">Negative Trend</AlertTitle>
            <AlertDescription className="text-red-700">
              Company revenue has been declining by 2.3% annually over the last 5 years, while the industry average has
              grown by 4.1% during the same period.
            </AlertDescription>
          </Alert>

          <Alert className="border-amber-200 bg-amber-50 text-amber-800">
            <AlertCircle className="h-4 w-4 text-amber-600" aria-label="Opportunity Icon" />
            <AlertTitle className="text-amber-800">Opportunity</AlertTitle>
            <AlertDescription className="text-amber-700">
              Your profit margins in the premium product segment are 12% higher than your standard offerings. Consider
              shifting marketing focus to these higher-margin products.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Performance Metrics</CardTitle>
          <CardDescription>Comparison against benchmarks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Revenue Growth</span>
              <div className="flex items-center">
                <span className="text-sm font-medium">-2.3%</span>
                <ArrowDown className="ml-1 h-4 w-4 text-red-500" aria-label="Revenue Growth Down Icon" />
              </div>
            </div>
            <div className="h-2 w-full rounded-full bg-muted">
              <div className="h-2 w-[35%] rounded-full bg-red-500"></div>
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Your Performance</span>
              <span>Industry Average: +4.1%</span>
            </div>
          </div>

          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Profit Margin</span>
              <div className="flex items-center">
                <span className="text-sm font-medium">+1.8%</span>
                <ArrowUp className="ml-1 h-4 w-4 text-green-500" aria-label="Profit Margin Up Icon" />
              </div>
            </div>
            <div className="h-2 w-full rounded-full bg-muted">
              <div className="h-2 w-[65%] rounded-full bg-green-500"></div>
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Your Performance</span>
              <span>Industry Average: +0.5%</span>
            </div>
          </div>

          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Market Share</span>
              <div className="flex items-center">
                <span className="text-sm font-medium">-0.7%</span>
                <ArrowDown className="ml-1 h-4 w-4 text-red-500" aria-label="Market Share Down Icon" />
              </div>
            </div>
            <div className="h-2 w-full rounded-full bg-muted">
              <div className="h-2 w-[42%] rounded-full bg-red-500"></div>
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Your Performance</span>
              <span>Industry Average: +0.2%</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

