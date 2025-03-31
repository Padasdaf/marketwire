"use client";

import { useEffect, useState } from "react";
import { useSupabase } from "@/app/context/SupabaseContext"; // Import the useSupabase hook
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import { StockSkeleton } from "./StockSkeleton";
import { v4 as uuidv4 } from "uuid"; // Import uuid

export const StockSearch = () => {
  const supabase = useSupabase(); // Get the Supabase client
  const [open, setOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");

  const handleSearch = async (query: string) => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/search?query=${encodeURIComponent(query)}`
      );
      const data = await response.json();
      const limitedResults = data.response.slice(0, 20);
      console.log(limitedResults);
      setSearchResults(limitedResults);
    } catch (error) {
      console.error("Error searching stocks:", error);
    } finally {
      setLoading(false); // Set loading to false when search ends
    }
  };

  const handleStockSelect = async (symbol: string, companyName: string) => {
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(); // Get the current user

    if (error || !user) {
      console.error("User not logged in");
      return;
    }

    const user_data = await supabase
      .from("users_table")
      .select("*")
      .eq("email", user.email);
    const userId =
      user_data.data && user_data.data.length > 0 ? user_data.data[0].id : null; // Ensure user_data.data is not empty
    const companyId = uuidv4();
    const response = await fetch(
      `https://financialmodelingprep.com/api/v3/quote-short/${symbol}?apikey=${process.env.NEXT_PUBLIC_FMP_API_KEY}`
    );
    const tick_data = await response.json();
    if (!userId) {
      console.error("User ID is undefined");
      return;
    }

    try {
      const response = await fetch("/api/stocks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          id: companyId,
          symbol,
          companyName,
          price: tick_data[0].price,
          user_id: userId,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to add stock");
      }

      console.log("Stock added successfully");
    } catch (error) {
      console.error("Error adding stock:", error);
    } finally {
      setOpen(false); // Close the dialog after selection
    }
  };

  return (
    <>
      <Button
        variant="outline"
        className="relative h-9 w-9 p-0 xl:h-10 xl:w-60 xl:justify-start xl:px-3 xl:py-2"
        onClick={() => setOpen(true)}
      >
        <Search className="h-4 w-4 xl:mr-2" />
        <span className="hidden xl:inline-flex">Search stocks...</span>
      </Button>
      <CommandDialog open={open} onOpenChange={setOpen}>
        <div className=" w-full ">
          <CommandInput
            placeholder="Search stocks..."
            onValueChange={(event) => {
              setQuery(event);
            }}
          />
          <Button
            onClick={() => handleSearch(query)} // Call handleSearch with the current query
            className="h-9 fixed -right-0  -top-0 dark:bg-black m-2"
          >
            Submit
          </Button>
        </div>

        <CommandList>
          {loading ? (
            <CommandGroup>
              <StockSkeleton />
            </CommandGroup>
          ) : (
            <>
              <CommandGroup heading="Stocks">
                {searchResults.map((result, index) => (
                  <CommandItem
                    key={index}
                    onSelect={() => {
                      handleStockSelect(result.symbol, result.name);
                    }}
                    className="hover:cursor-pointer"
                  >
                    <div className="flex flex-col">
                      <span>{result?.symbol}</span>
                      <span className="text-sm text-muted-foreground">
                        {result?.name}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            </>
          )}
        </CommandList>
      </CommandDialog>
    </>
  );
};
