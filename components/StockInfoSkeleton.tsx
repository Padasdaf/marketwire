import { Skeleton } from "@/components/ui/skeleton"

export function StockInfoSkeleton() {
  return (
    
    <main className="flex-1">
    <div className="flex flex-col px-10 py-5 gap-4 ">
      
      <Skeleton className="h-20 w-full" />

      <div className="flex flex-row gap-10">
        <Skeleton className="h-full w-3/5 p-56" />
        <Skeleton className="h-full w-2/5 p-56" />

      </div>

      {/* <DataTable columns={columns} data={tableData} onRowSelect={handleRowSelect} /> */}
    </div>
    {/* <StockChart symbol="AAPL"/> */}
  </main>
  )
}
