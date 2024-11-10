import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu";
import { ColumnDef } from "@tanstack/react-table";
import { Button } from "../ui/button";
import { MoreHorizontal } from "lucide-react";

export interface Stock {
  id: string; // Assuming UUID is stored as a string
  symbol: string;
  company_name: string;
  sector?: string; // Sector can be optional
  created_at: string; // Assuming created_at is a timestamp string
}

export const columns: ColumnDef<Stock>[] = [
  {
    accessorKey: "symbol",
    header: "Symbol",
  },
  {
    accessorKey: "name",
    header: "Company Name",
  },
  {
    accessorKey: "price",
    header: "Current Price",
  },
  {
    accessorKey: "created_at",
    header: "Added on",
    cell: ({ getValue }) => new Date().toLocaleDateString(), // Format date
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const payment = row.original;

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="end"
            className="!bg-[#737373] rounded-xl px-5 py-2 text-white w-full  z-50"
          >
            <DropdownMenuLabel className="border-b-2 border-b-black text-left text-md w-full ">
              Actions
            </DropdownMenuLabel>

            <DropdownMenuItem
              className="text-sm hover:text-black hover:cursor-pointer"
              onClick={async (event) => {
                event.stopPropagation(); // Prevent row click
                console.log(
                  `Attempting to delete stock with ID: ${payment.id}`
                ); // Log the stock ID
                try {
                  const response = await fetch(`/api/stocks`, {
                    method: "DELETE",
                    headers: {
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                      id: payment.id
                    }),
                  });
                  if (response.ok) {
                    console.log("Successful deletion of company!");
                  } else {
                    console.error(
                      "Failed to delete company, response status:",
                      response.status
                    ); // Log the response status
                  }
                } catch (error) {
                  console.log(error);
                }
              }}
            >
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
