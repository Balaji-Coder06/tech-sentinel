import { NextRequest, NextResponse } from 'next/server';
import { serverDb } from '../../../lib/server-db';

export const dynamic = 'force-dynamic';

export async function GET() {
  const prefs = serverDb.getPreferences();
  return NextResponse.json({ success: true, data: prefs });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const updated = serverDb.updatePreferences(body);
    return NextResponse.json({ success: true, data: updated });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function PUT(request: NextRequest) {
  return POST(request);
}

