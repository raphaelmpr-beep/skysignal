/**
 * NextAuth.js v4 configuration — Credentials provider
 *
 * Delegates authentication to the SkySignal FastAPI backend.
 * On success, stores the JWT and user profile in the NextAuth session token.
 *
 * Session strategy: JWT (stateless — no database adapter required for the web layer).
 */

import NextAuth, { type NextAuthOptions } from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      id: 'credentials',
      name: 'SkySignal',
      credentials: {
        email: { label: 'Email', type: 'email', placeholder: 'analyst@org.gov' },
        password: { label: 'Password', type: 'password' },
      },

      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null

        try {
          const res = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          })

          if (!res.ok) return null

          const data = (await res.json()) as {
            access_token: string
            token_type: string
            user: {
              id: string
              email: string
              full_name?: string
              name?: string
              role: string
              org_id: string
            }
          }

          if (!data.access_token) return null

          // Return shape that NextAuth persists into the JWT
          return {
            id: data.user.id,
            email: data.user.email,
            name: data.user.full_name ?? data.user.name ?? data.user.email,
            role: data.user.role,
            org_id: data.user.org_id,
            access_token: data.access_token,
          }
        } catch {
          return null
        }
      },
    }),
  ],

  session: {
    strategy: 'jwt',
    // 8-hour session matches a typical analyst shift
    maxAge: 8 * 60 * 60,
  },

  callbacks: {
    /**
     * Persist custom fields (role, org_id, access_token) into the JWT.
     * `user` is only present on initial sign-in; `token` persists across requests.
     */
    async jwt({ token, user }) {
      if (user) {
        token.role = (user as { role?: string }).role
        token.org_id = (user as { org_id?: string }).org_id
        token.access_token = (user as { access_token?: string }).access_token
      }
      return token
    },

    /**
     * Expose custom fields to the client-side `useSession()` hook.
     */
    async session({ session, token }) {
      if (token) {
        session.user = session.user ?? {}
        ;(session.user as Record<string, unknown>).role = token.role
        ;(session.user as Record<string, unknown>).org_id = token.org_id
        ;(session.user as Record<string, unknown>).access_token = token.access_token
        ;(session.user as Record<string, unknown>).id = token.sub
      }
      return session
    },
  },

  pages: {
    signIn: '/login',
    error: '/login',
  },

  secret: process.env.NEXTAUTH_SECRET,

  debug: process.env.NODE_ENV === 'development',
}

const handler = NextAuth(authOptions)
export { handler as GET, handler as POST }
