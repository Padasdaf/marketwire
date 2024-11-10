import { NextResponse } from "next/server";
import { db } from "@/utils/db/db"; // Adjust the import based on your db setup
import { companies } from "@/utils/db/schema"; // Import your schema

export async function POST(request: Request) {
    const { user_id, company_id } = await request.json();

    try {
        const newEntry = await db.insert(companies).values({
            user_id: user_id,
            company_id: company_id,
        });

        return NextResponse.json(newEntry, { status: 201 });
    } catch (error) {
        console.error("Error inserting into user_companies:", error);
        return NextResponse.json({ error: "Failed to add stock to user companies" }, { status: 500 });
    }
} 