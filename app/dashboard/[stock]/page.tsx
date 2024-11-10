"use client";
import { StockInfoSkeleton } from "@/components/StockInfoSkeleton";
import StockChart from "@/components/Stocks/StockChart";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import Image from "next/image";
import React, { useEffect } from "react";
import { useState } from "react";

// Define the interface for the stock data
interface StockData {
  symbol: string;
  price: number;
  beta: number;
  volAvg: number;
  mktCap: number;
  lastDiv: number;
  range: string;
  changes: number;
  companyName: string;
  currency: string;
  cik: string;
  isin: string;
  cusip: string;
  exchange: string;
  exchangeShortName: string;
  industry: string;
  website: string;
  description: string;
  ceo: string;
  sector: string;
  country: string;
  fullTimeEmployees: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  dcfDiff: number;
  dcf: number;
  image: string;
  ipoDate: string;
  defaultImage: boolean;
  isEtf: boolean;
  isActivelyTrading: boolean;
  isAdr: boolean;
  isFund: boolean;
}

const StockSlugPage = ({ params }: any) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<StockData>();
  const slug = params.stock;

  useEffect(() => {
    setLoading(true); // Set loading to true when search starts
    const fetchData = async () => {
      try {
        const response = await fetch(
          `/api/stock?query=${encodeURIComponent(slug)}`
        );
        const response_data = await response.json();
        setData(response_data.response[0]);
      } catch (error) {
        console.error("Error searching stocks:", error);
      } finally {
        setLoading(false); // Set loading to false when search ends
      }
    };
    fetchData();
  }, [slug]);

  return !loading ? (
    <>
      <div className="flex flex-col gap-2 mt-3">
        <Card className="container h-40 mb-2 ml-2 my-auto shadow-xl ">
          <CardContent className=" container flex flex-row mt-5 ">
        
              {data?.image ? (
                <img
                  src={data.image}
                  alt="logo"
                  className="w-24 h-24 my-auto p-2 rounded-full"
                />
              ) : (
                <img
                  src="/default-image.jpeg"
                  alt="logo"
                  className="w-24 h-24 my-auto p-2 rounded-full"
                />
              )}

              <div className="flex flex-col gap-0 my-auto">
                <h1 className="text-4xl text-black">
                  {data?.companyName}
                </h1>
                <h2 className="text-sm">
                    {data?.address}
                </h2>
              </div>

          </CardContent>
        </Card>

        <div className="flex flex-col md:flex-row w-full gap-7 px-2">
          <StockChart symbol={slug as string} />

          <Card className="px-2 py-6 md:w-1/2 shadow-xl">
          <CardTitle className="py-6 px-6">About {data?.companyName}</CardTitle>
            <CardContent className="text-sm">{data?.description}</CardContent>
          </Card>
        </div>
      </div>
    </>
  ) : (
    <StockInfoSkeleton/>
  );
};

export default StockSlugPage;
