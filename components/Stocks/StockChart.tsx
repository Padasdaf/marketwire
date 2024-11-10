"use client";
import React, { useState, useEffect, useRef } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from "chart.js";
import {
  CandlestickController,
  CandlestickElement,
  OhlcElement,
} from "chartjs-chart-financial";
import "chartjs-adapter-date-fns";

ChartJS.register(
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  CandlestickController,
  CandlestickElement,
  OhlcElement
);

interface StockChartProps {
  symbol: string;
}

const StockChart: React.FC<StockChartProps> = ({ symbol }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef<ChartJS | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const apiKey = process.env.NEXT_PUBLIC_FMP_API_KEY;
        console.log("Fetching data for symbol:", symbol);

        // Get historical daily price data
        const url = `https://financialmodelingprep.com/api/v3/historical-price-full/${symbol}?apikey=${apiKey}`;
        const response = await fetch(url);
        const data = await response.json();

        console.log("API Response:", data);

        if (!data.historical) {
          throw new Error("No historical data received from API");
        }

        // Get the last 30 days of data and reverse to show oldest first
        const last30Days = data.historical.slice(0, 30).reverse();

        // Convert data for candlestick chart
        const candlestickData = last30Days.map((day:any) => ({
          x: new Date(day.date).getTime(),
          o: day.open,
          h: day.high,
          l: day.low,
          c: day.close,
        }));

        // Create/Update chart
        if (canvasRef.current) {
          if (chartRef.current) {
            chartRef.current.destroy();
          }

          const ctx = canvasRef.current.getContext("2d");
          if (ctx) {
            chartRef.current = new ChartJS(ctx, {
              type: "candlestick",
              data: {
                datasets: [
                  {
                    label: `${symbol} Stock Price`,
                    data: candlestickData,
                    backgroundColors: {
                      up: "rgba(68, 139, 34,1)",
                      down: "rgba(255, 4, 34,1)",
                      unchanged: "rgba(90, 90, 90, 1)",
                    },
                  },
                ],
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: "top",
                  },
                  title: {
                    display: true,
                    text: `${symbol} Stock Price Chart`,
                  },
                  tooltip: {
                    callbacks: {
                      label: (context: any) => {
                        const point = context.raw;
                        return [
                          `Open: $${point.o.toFixed(2)}`,
                          `High: $${point.h.toFixed(2)}`,
                          `Low: $${point.l.toFixed(2)}`,
                          `Close: $${point.c.toFixed(2)}`,
                        ];
                      },
                    },
                  },
                },
                scales: {
                  x: {
                    type: "time",
                    time: {
                      unit: "day",
                    },
                    title: {
                      display: true,
                      text: "Date",
                    },
                  },
                  y: {
                    title: {
                      display: true,
                      text: "Price ($)",
                    },
                  },
                },
              },
            });
          }
        }
        setError(null);
      } catch (err) {
        console.error("Error fetching stock data:", err);
        setError(
          err instanceof Error ? err.message : "Failed to fetch stock data"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [symbol]);

  if (loading) {
    return (
      <div className="w-full h-[400px] flex items-center justify-center">
        Loading chart data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-[400px] flex items-center justify-center text-red-500">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="w-full h-[400px] p-4 bg-white rounded-lg shadow-xl">
      <canvas ref={canvasRef} />
    </div>
  );
};

export default StockChart;
