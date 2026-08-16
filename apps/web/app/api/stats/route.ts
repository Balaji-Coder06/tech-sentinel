import { NextResponse } from 'next/server';
import { serverDb } from '../../../lib/server-db';

export const dynamic = 'force-dynamic';

export async function GET() {
  const stats = serverDb.getAgentStats();
  return NextResponse.json({ success: true, data: stats });
}
