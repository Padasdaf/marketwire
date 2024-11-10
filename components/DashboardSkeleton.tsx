import { Skeleton } from "@/components/ui/skeleton"

export function DashboardSkeleton() {
  return (
    
    <main className="flex-1">
    <div className="flex flex-col px-10 py-5 gap-4 ">
      
      <Skeleton className="h-20 w-1/3" />
      <Skeleton className="h-full w-full p-56" />

      {/* <DataTable columns={columns} data={tableData} onRowSelect={handleRowSelect} /> */}
    </div>
    {/* <StockChart symbol="AAPL"/> */}
  </main>
  )
}
