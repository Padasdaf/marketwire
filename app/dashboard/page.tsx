"use client";
import dynamic from "next/dynamic";

import { useRouter } from "next/navigation";
import { redirect } from "next/navigation";
import { useSupabase } from "../context/SupabaseContext";
import { DataTable } from "@/components/Stocks/data-table";
import { columns, Stock } from "@/components/Stocks/columns";
import { useEffect, useState } from "react";
const StockChart = dynamic(() => import("@/components/Stocks/StockChart"), {
  ssr: false, // ensures the component only renders on the client
});
import { DashboardSkeleton } from "@/components/DashboardSkeleton";
import NewsBlocks, { Article } from "@/components/NewsBlocks";

export default function Page() {
  const router = useRouter();

  const supabase = useSupabase();
  const [tableData, setTableData] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState<string | null>(null);
  const [articles, setArticles] = useState<Article[]>([]);

  useEffect(() => {
    const fetchUserData = async () => {
      const {
        data: { user },
        error,
      } = await supabase.auth.getUser();

      if (error || !user) {
        console.error("User not logged in");
        return;
      }

      const user_data = await supabase
        .from("users_table")
        .select("*")
        .eq("email", user.email);

      if (!user_data.data || user_data.data.length === 0) {
        console.error("No user data found");
        return;
      }

      const { data, error: fetchError } = await supabase
        .from("companies")
        .select("*")
        .eq("user_id", user_data.data[0].id);

      if (fetchError) {
        console.error("Error fetching user stocks:", fetchError);
        return;
      }

      const articles_response = await fetch(
        `https://financialmodelingprep.com/api/v3/fmp/articles?page=0&size=5&apikey=${process.env.NEXT_PUBLIC_FMP_API_KEY}`
      );
      const articles_data = await articles_response.json();
      setArticles(articles_data.content);
      setTableData(data);
      setLoading(false);
    };
    fetchUserData();
  }, [supabase]);

  const handleRowSelect = (stock: Stock) => {
    const slug = stock.symbol;
    router.push(`/dashboard/${slug}?stock=${slug}`);
  };

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <main className="flex-1">
      <div className="container px-10 py-5 ">
        <h1 className="text-4xl pb-8 text-[#438B22] text-pretty font-semibold drop-shadow-md ">
          Your Stocks
        </h1>
        <DataTable
          columns={columns}
          data={tableData}
          onRowSelect={handleRowSelect}
        />
      </div>
      <div className="container px-10 py-5 text-center gap-5">
        <h1 className="text-4xl pb-8 text-[#438B22] drop-shadow-md">
          Whats on the News?
        </h1>
        <NewsBlocks articles={articles} />
      </div>
    </main>
  );
}
