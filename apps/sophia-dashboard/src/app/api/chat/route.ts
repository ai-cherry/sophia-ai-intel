import { NextResponse } from 'next/server';

// Import unified handler
import { POST as unifiedPost } from './unified-route';

export async function POST(request: Request) {
  // Use unified chat handler for ONE FUCKING CHAT BOX
  return unifiedPost(request);
}
