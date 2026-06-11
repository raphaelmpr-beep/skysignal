import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const body = await request.json() as { email: string; password: string }
  
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  
  try {
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    
    const data = await res.json()
    
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status })
    }
    
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ detail: 'API connection failed' }, { status: 503 })
  }
}
