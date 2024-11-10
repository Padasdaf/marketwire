"use client";
import React from "react";
import ApexCharts from "apexcharts";

interface StockChartProps {
  symbol: string;
}

class StockChart extends React.Component<StockChartProps> {
  private chart: ApexCharts | null = null;

  constructor(props: StockChartProps) {
    super(props);
    this.state = {
      series: [{
        data: [] // Initialize with empty data
      }],
      options: {
        chart: {
          type: 'candlestick',
          height: 350,
          id: 'candlestick-chart',
        },
        title: {
          text: `${props.symbol} Stock Price Chart`,
          align: 'left',
        },
        xaxis: {
          type: 'datetime',
        },
        yaxis: {
          tooltip: {
            enabled: true,
          },
        },
      },
    };
  }

  async componentDidMount() {
    await this.fetchData();
  }

  async fetchData() {
    try {
      const apiKey = process.env.NEXT_PUBLIC_FMP_API_KEY;
      console.log("Fetching data for symbol:", this.props.symbol);

      // Get historical daily price data
      const url = `https://financialmodelingprep.com/api/v3/historical-price-full/${this.props.symbol}?apikey=${apiKey}`;
      const response = await fetch(url);
      const data = await response.json();

      console.log("API Response:", data);

      if (!data.historical) {
        throw new Error("No historical data received from API");
      }

      // Get the last 30 days of data and reverse to show oldest first
      const last30Days = data.historical.slice(0, 30).reverse();

      // Convert data for candlestick chart
      const candlestickData = last30Days.map((day: any) => ({
        x: new Date(day.date).getTime(),
        y: [day.open, day.high, day.low, day.close],
      }));

      // Update the chart with new data
      this.setState({
        series: [{ data: candlestickData }],
      }, () => {
        this.renderChart();
      });
    } catch (err) {
      console.error("Error fetching stock data:", err);
    }
  }

  renderChart() {
    if (this.chart) {
      this.chart.destroy();
    }

    this.chart = new ApexCharts(document.querySelector("#chart"), {
      ...this.state.options,
      series: this.state.series,
    });

    this.chart.render();
  }

  componentWillUnmount() {
    if (this.chart) {
      this.chart.destroy();
    }
  }

  render() {
    return (
      <div className="w-full h-[400px] p-4 bg-white rounded-lg shadow-xl">
        <div id="chart" />
      </div>
    );
  }
}

export default StockChart;
