import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DashboardHeader } from "@/components/dashboard-header"
import { DashboardShell } from "@/components/dashboard-shell"
import Overview from "@/components/overview"
// import { RecentQueries } from "@/components/RecentQueries"
import { Search } from "@/components/search"
import { RecentQueries } from "@/components/recent-queries"
import { useState } from "react"
export default function DashboardPage() {
  const [ticker, setTicker] = useState("AAPL")

  const handleSearch = (query: string) => {
    setTicker(query)
  }

  return (
    <>
      <DashboardShell>
        <DashboardHeader
          heading="Financial Analytics Dashboard"
          text="Query financial data, create charts, and discover insights."
        >
          <Search onSearch={handleSearch} />
        </DashboardHeader>
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="custom">Custom Charts</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
          </TabsList>
          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    className="h-4 w-4 text-muted-foreground"
                    aria-hidden="true"
                  >
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">$45,231.89</div>
                  <p className="text-xs text-muted-foreground">+20.1% from last month</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Profit Margin</CardTitle>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    className="h-4 w-4 text-muted-foreground"
                  >
                    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">23.4%</div>
                  <p className="text-xs text-muted-foreground">+1.2% from last month</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Market Share</CardTitle>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    className="h-4 w-4 text-muted-foreground"
                  >
                    <rect width="20" height="14" x="2" y="5" rx="2" />
                    <path d="M2 10h20" />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">12.5%</div>
                  <p className="text-xs text-muted-foreground">+2.1% from last year</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Investments</CardTitle>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    className="h-4 w-4 text-muted-foreground"
                  >
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                  </svg>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">+573</div>
                  <p className="text-xs text-muted-foreground">+201 since last month</p>
                </CardContent>
              </Card>
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
              <Card className="col-span-4">
                <CardHeader>
                  <CardTitle>Revenue Overview</CardTitle>
                </CardHeader>
                <CardContent className="pl-2">
                  <Overview 
                    selectedTicker={ticker}
                  />
                </CardContent>
              </Card>
              <Card className="col-span-3">
                <CardHeader>
                  <CardTitle>Recent Queries</CardTitle>
                  <CardDescription>You made 10 queries this month.</CardDescription>
                </CardHeader>
                <CardContent>
                  <RecentQueries />
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          <TabsContent value="analytics" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Financial Analytics</CardTitle>
                <CardDescription>Explore standard financial charts and metrics.</CardDescription>
              </CardHeader>
              <CardContent className="pl-2">
                <div className="flex flex-col space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Button variant="outline" className="h-20 justify-start">
                      <div className="flex flex-col items-start">
                        <span className="font-medium">Revenue Analysis</span>
                        <span className="text-sm text-muted-foreground">Historical revenue trends</span>
                      </div>
                    </Button>
                    <Button variant="outline" className="h-20 justify-start">
                      <div className="flex flex-col items-start">
                        <span className="font-medium">Profit Margins</span>
                        <span className="text-sm text-muted-foreground">Gross and net profit margins</span>
                      </div>
                    </Button>
                    <Button variant="outline" className="h-20 justify-start">
                      <div className="flex flex-col items-start">
                        <span className="font-medium">Cash Flow</span>
                        <span className="text-sm text-muted-foreground">Operating and free cash flow</span>
                      </div>
                    </Button>
                    <Button variant="outline" className="h-20 justify-start">
                      <div className="flex flex-col items-start">
                        <span className="font-medium">Balance Sheet</span>
                        <span className="text-sm text-muted-foreground">Assets, liabilities, equity</span>
                      </div>
                    </Button>
                    <Button variant="outline" className="h-20 justify-start">
                      <div className="flex flex-col items-start">
                        <span className="font-medium">Market Comparison</span>
                        <span className="text-sm text-muted-foreground">Benchmark against competitors</span>
                      </div>
                    </Button>
                    <Button variant="outline" className="h-20 justify-start">
                      <div className="flex flex-col items-start">
                        <span className="font-medium">Financial Ratios</span>
                        <span className="text-sm text-muted-foreground">Key performance indicators</span>
                      </div>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="custom" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Custom Chart Builder</CardTitle>
                <CardDescription>Create your own charts by selecting data and visualization type.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Data Source</label>
                      <select className="w-full p-2 border rounded-md">
                        <option>Revenue Data</option>
                        <option>Profit Data</option>
                        <option>Market Share Data</option>
                        <option>Customer Data</option>
                        <option>Product Data</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Chart Type</label>
                      <select className="w-full p-2 border rounded-md">
                        <option>Line Chart</option>
                        <option>Bar Chart</option>
                        <option>Pie Chart</option>
                        <option>Area Chart</option>
                        <option>Scatter Plot</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Time Period</label>
                      <select className="w-full p-2 border rounded-md">
                        <option>Last 30 Days</option>
                        <option>Last Quarter</option>
                        <option>Last Year</option>
                        <option>Last 5 Years</option>
                        <option>Custom Range</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Comparison</label>
                      <select className="w-full p-2 border rounded-md">
                        <option>None</option>
                        <option>Previous Period</option>
                        <option>Industry Average</option>
                        <option>Top Competitor</option>
                        <option>Custom Benchmark</option>
                      </select>
                    </div>
                  </div>
                  <Button className="w-full">Generate Custom Chart</Button>
                  <div className="h-64 border rounded-md flex items-center justify-center text-muted-foreground">
                    Custom chart preview will appear here
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="insights" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Automated Insights</CardTitle>
                <CardDescription>AI-powered analysis of your financial data.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Card className="bg-muted/50">
                    <CardContent className="pt-6">
                      <div className="flex items-start space-x-4">
                        <div className="rounded-full bg-primary/10 p-2">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="24"
                            height="24"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="h-4 w-4 text-primary"
                          > 
                            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                            <polyline points="14 2 14 8 20 8" />
                            <path d="M16 13H8" />
                            <path d="M16 17H8" />
                            <path d="M10 9H8" />
                          </svg>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">Revenue Trend Analysis</p>
                          <p className="text-sm text-muted-foreground">
                            Company revenue has been declining by 2.3% annually over the last 5 years, while the
                            industry average has grown by 4.1% during the same period. This indicates a potential loss
                            of market share or pricing pressure.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-muted/50">
                    <CardContent className="pt-6">
                      <div className="flex items-start space-x-4">
                        <div className="rounded-full bg-primary/10 p-2">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="24"
                            height="24"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="h-4 w-4 text-primary"
                          >
                            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                            <polyline points="14 2 14 8 20 8" />
                            <path d="M16 13H8" />
                            <path d="M16 17H8" />
                            <path d="M10 9H8" />
                          </svg>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">Profit Margin Insight</p>
                          <p className="text-sm text-muted-foreground">
                            Despite declining revenue, your gross profit margin has improved by 1.8% year-over-year,
                            suggesting successful cost-cutting measures or a shift to higher-margin products. Consider
                            focusing marketing efforts on these higher-margin segments.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-muted/50">
                    <CardContent className="pt-6">
                      <div className="flex items-start space-x-4">
                        <div className="rounded-full bg-primary/10 p-2">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="24"
                            height="24"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            className="h-4 w-4 text-primary"
                          >
                            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                            <polyline points="14 2 14 8 20 8" />
                            <path d="M16 13H8" />
                            <path d="M16 17H8" />
                            <path d="M10 9H8" />
                          </svg>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">Cash Flow Warning</p>
                          <p className="text-sm text-muted-foreground">
                            Operating cash flow has decreased by 15% in the last quarter, primarily due to longer
                            accounts receivable cycles. This trend could lead to liquidity issues if not addressed.
                            Consider implementing stricter collection policies.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DashboardShell>
    </>
  )
}

