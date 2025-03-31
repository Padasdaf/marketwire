"use server"
import { createClient } from '@/utils/supabase/server'
import { redirect } from "next/navigation"
import { revalidatePath } from 'next/cache'
import { db } from '@/utils/db/db'
import { usersTable } from '@/utils/db/schema'
import { eq } from 'drizzle-orm'
const PUBLIC_URL = process.env.NEXT_PUBLIC_WEBSITE_URL ? process.env.NEXT_PUBLIC_WEBSITE_URL : "http://localhost:3000"
export async function resetPassword(currentState: { message: string }, formData: FormData) {

    const supabase = createClient()
    const passwordData = {
        password: formData.get('password') as string,
        confirm_password: formData.get('confirm_password') as string,
        code: formData.get('code') as string
    }
    if (passwordData.password !== passwordData.confirm_password) {
        return { message: "Passwords do not match" }
    }

    const { data } = await supabase.auth.exchangeCodeForSession(passwordData.code)

    let { error } = await supabase.auth.updateUser({
        password: passwordData.password

    })
    if (error) {
        return { message: error.message }
    }
    redirect(`/forgot-password/reset/success`)
}

export async function forgotPassword(currentState: { message: string }, formData: FormData) {

    const supabase = createClient()
    const email = formData.get('email') as string
    const { data, error } = await supabase.auth.resetPasswordForEmail(email, { redirectTo: `${PUBLIC_URL}/forgot-password/reset` })

    if (error) {
        return { message: error.message }
    }
    redirect(`/forgot-password/success`)

}
export async function signup(currentState: { message: string }, formData: FormData) {
    const supabase = createClient()

    const data = {
        email: formData.get('email') as string,
        password: formData.get('password') as string,
    }

    const { data: signUpData, error: signUpError } = await supabase.auth.signUp(data)

    if (signUpError) {
        return { message: signUpError.message }
    }

    if (!signUpData.user) {
        return { message: "No user data returned after signup" }
    }

    // Use the user data directly from the signUp response
    const user = signUpData.user
    
    // create Stripe Customer Record
    
    // Create record in DB
    await db.insert(usersTable).values({ 
        name: "", 
        email: user.email!, 
        plan: "default_plan",
        stripe_id: "default_stripe_id"
    })

    revalidatePath('/', 'layout')
    redirect('/dashboard')
}

export async function loginUser(currentState: { message: string }, formData: FormData) {
    const supabase = createClient()

    const data = {
        email: formData.get('email') as string,
        password: formData.get('password') as string,
    }

    const { error } = await supabase.auth.signInWithPassword(data)

    if (error) {
        return { message: error.message }
    }

    revalidatePath('/', 'layout')
    redirect('/dashboard')
}



export async function logout() {
    const supabase = createClient()
    const { error } = await supabase.auth.signOut()
    redirect('/login')
}

export async function signInWithGoogle() {
    const supabase = createClient()
    const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: `${PUBLIC_URL}/auth/callback`,
            queryParams: {
                access_type: 'offline',
                prompt: 'consent',
            },
        },
    })

    if (data.url) {
        redirect(data.url)
    }
    if(error){
        console.log(error)
    }
}

export async function signInWithGithub() {
    const supabase = createClient()
    const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'github',
        options: {
            redirectTo: `${PUBLIC_URL}/auth/callback`,
        },
    })

    if (data.url) {
        redirect(data.url)
    }
}

export async function handleAuthCallback() {
    const supabase = createClient()
    
    const {
        data: { user },
        error,
    } = await supabase.auth.getUser()

    if (error || !user) {
        console.error('Auth callback error:', error)
        redirect('/login')
    }

    try {
        // Check if user already exists in our database
        const existingUser = await db
            .select()
            .from(usersTable)
            .where(eq(usersTable.email, user.email!))
            .limit(1)

        if (!existingUser.length) {
            // Create Stripe Customer Record
            
            // Create record in DB
            await db.insert(usersTable).values({ 
                name: user.user_metadata?.full_name || "",
                email: user.email!,
                plan: "default_plan",
                stripe_id: "default_stripe_id"
            })

            revalidatePath('/', 'layout')
            redirect('/dashboard')
        }

        // If user exists, just redirect to dashboard
        redirect('/dashboard')
    } catch (error) {
        console.error('Error in auth callback:', error)
        redirect('/error')
    }
}