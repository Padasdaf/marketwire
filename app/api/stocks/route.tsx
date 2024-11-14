import { NextResponse } from "next/server";
import { db } from "@/utils/db/db"; // Adjust the import based on your db setup
import { companies } from "@/utils/db/schema"; // Import your schema
import { eq } from "drizzle-orm";

export async function POST(request: Request) {
  const { id, symbol,price, companyName,user_id } = await request.json();
    console.log(user_id);
  try {
    const newStock = await db.insert(companies).values({
      id: id,
      symbol: symbol,
      company_name: companyName,
      price:price,
      user_id: user_id,
    });


    return NextResponse.json(newStock, { status: 201 });
  } catch (error) {
    console.error("Error inserting stock:", error);
    return NextResponse.json({ error: "Failed to add stock" }, { status: 500 });
  }
}


export async function DELETE(request: Request) {
    const { id } = await request.json();
    try {
        // Specify the condition for deletion
        await db.delete(companies).where(eq(companies.id,id));
        return NextResponse.json({ message: "Stock deleted successfully" }, { status: 200 });
    } catch (error) {
        console.error("Error deleting stock:", error);
        return NextResponse.json({ error: "Failed to delete stock" }, { status: 500 });
    }
}
  
  