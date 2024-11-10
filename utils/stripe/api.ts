import { Stripe } from 'stripe';
import { db } from '../db/db';
import { usersTable } from '../db/schema';
import { eq } from "drizzle-orm";
export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)
const PUBLIC_URL = process.env.NEXT_PUBLIC_WEBSITE_URL ? process.env.NEXT_PUBLIC_WEBSITE_URL : "http://localhost:3000"
export async function getStripePlan(email: string) {

    const user = await db.select().from(usersTable).where(eq(usersTable.email, email))
    const subscription = await stripe.subscriptions.retrieve(
        ""
    );
    const productId = subscription.items.data[0].plan.product as string
    const product = await stripe.products.retrieve(productId)
    return product.name
}

export async function createStripeCustomer(id: string, email: string, name?: string) {
    const customer = await stripe.customers.create({
        name: name ? name : "",
        email: email,
        metadata: {
            supabase_id: id
        }
    });
    // Create a new customer in Stripe
    return customer.id
}
