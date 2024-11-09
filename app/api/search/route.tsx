import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('query');

  if (!query) {
    return NextResponse.json({ error: 'Query parameter is required' }, { status: 400 });
  }

  try {
    const apiKey = process.env.NEXT_PUBLIC_ALPHA_VANTAGE_API_KEY;
    const response = await fetch(
      `https://financialmodelingprep.com/api/v3/search?query=${query}&apikey=${apiKey}`
    );
    
    const data = await response.json();
    return NextResponse.json({ response: data }, { status: 200 });

  } catch (error) {
    console.error("Error fetching stock data:", error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}