import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'operational',
    services: {
      chat: 'online',
      agents: 'online',
      research: 'online',
      code: 'online'
    },
    timestamp: new Date().toISOString()
  });
}