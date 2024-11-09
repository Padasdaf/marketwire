"use client";

import { useState } from "react";
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

export const StockSearch = () => {
  const [open, setOpen] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const handleSearch = async (query: string) => {
    if (query.length < 2) return;
    
    try {
      const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
      const data = await response.json();
      const limitedResults = data.response.slice(0, 20);
      console.log(limitedResults);
      setSearchResults(limitedResults);
    } catch (error) {
      console.error("Error searching stocks:", error);
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
        <CommandInput 
          placeholder="Search stocks..." 
          onValueChange={handleSearch}
        />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          <CommandGroup heading="Stocks">
            {searchResults.map((result,index) => (
              <CommandItem
                key={index}
                onSelect={() => {
                  // Handle stock selection
                  setOpen(false);
                }}
              >
                <div className="flex flex-col">
                  <span>{result?.symbol}</span>
                  <span className="text-sm text-muted-foreground">
                    {result.name}
                  </span>
                </div>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  );
};
