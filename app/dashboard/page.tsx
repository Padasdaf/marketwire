import { redirect } from 'next/navigation'

import { createClient } from '@/utils/supabase/server'
import App from 'next/app'
import { AppSidebar } from '@/components/app-sidebar'
import { SidebarTrigger } from '@/components/ui/sidebar'
import { DataTable } from '@/components/Stocks/data-table'
import { columns, Stock } from '@/components/Stocks/columns'
import StockChart from '@/components/Stocks/StockChart'

async function getData(): Promise<Stock[]> {
    // Fetch data from your API here.
    return [
      {
        id: "728ed52f",
        amount: 100,
        status: "pending",
        email: "m@example.com",
      },
      // ...
    ]
  }

export default async function Dashboard() {
    const supabase = createClient()
    const table_data = await getData()

    

    const { data, error } = await supabase.auth.getUser()
    if (error || !data?.user) {
        redirect('/login')
    }

    return (
        <main className="flex-1">
            <div className="container px-10 py-5 ">
                <h1 className='text-4xl pb-8'>Your Stocks</h1>
                <DataTable columns={columns} data={table_data}/>
            </div>
            <StockChart symbol='AAPL'/>
        </main>)

}