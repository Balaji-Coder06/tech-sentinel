import { NextRequest, NextResponse } from 'next/server';
import { serverDb } from '../../../lib/server-db';

export const dynamic = 'force-dynamic';

export async function GET() {
  const saved = serverDb.getSavedItems();
  return NextResponse.json({ success: true, data: saved });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { type, id } = body;

    if (!type || !id || (type !== 'news' && type !== 'opportunity')) {
      return NextResponse.json({ error: 'Invalid item type or id' }, { status: 400 });
    }

    const updated = serverDb.toggleSave(type, id);
    return NextResponse.json({ success: true, data: updated });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
