import { NextResponse } from 'next/server';
import { serverDb } from '../../../../lib/server-db';

export const dynamic = 'force-dynamic';

export async function GET() {
  const categories = serverDb.getCategories();
  return NextResponse.json({ success: true, count: categories.length, data: categories });
}
