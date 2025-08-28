import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    results: [],
    timestamp: new Date().toISOString()
  });
}