import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export function RecentQueries() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Query</TableHead>
          <TableHead>Date</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell className="font-medium">Revenue by product category</TableCell>
          <TableCell>Mar 24, 2025</TableCell>
          <TableCell className="text-green-500">Completed</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">Profit margin trends</TableCell>
          <TableCell>Mar 23, 2025</TableCell>
          <TableCell className="text-green-500">Completed</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">Market share analysis</TableCell>
          <TableCell>Mar 22, 2025</TableCell>
          <TableCell className="text-green-500">Completed</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">Customer acquisition cost</TableCell>
          <TableCell>Mar 21, 2025</TableCell>
          <TableCell className="text-green-500">Completed</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="font-medium">Quarterly performance</TableCell>
          <TableCell>Mar 20, 2025</TableCell>
          <TableCell className="text-green-500">Completed</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  )
}

