import { type EmailOtpType } from '@supabase/supabase-js'
import { type NextRequest } from 'next/server'

import { createClient } from '@/utils/supabase/server'
import { redirect } from 'next/navigation'

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url)
    const token_hash = searchParams.get('token_hash')
    const type = searchParams.get('type') as EmailOtpType | null
    const next = searchParams.get('next') ?? '/'

    if (token_hash && type) {
        const supabase = createClient()

        const { error } = await supabase.auth.verifyOtp({
            type,
            token_hash,
        })
        if (!error) {
            // redirect user to specified redirect URL or root of app
            redirect(next)
        } else {
            // Handle the error case more gracefully
            // You might want to log the error or provide feedback to the user
            console.error('Error verifying OTP:', error)
            redirect('/error') // Redirect to error page if OTP verification fails
        }
    } else {
        // Redirect to error page if token_hash or type is missing
        redirect('/error')
    }

    // redirect the user to an error page with some instructions
    redirect('/error')
}