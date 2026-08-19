import { NextResponse } from 'next/server';
import { serverDb } from '../../../lib/server-db';

export const dynamic = 'force-dynamic';

export async function GET() {
  const stats = serverDb.getAgentStats(false);
  return NextResponse.json({ success: true, data: stats });
}

export async function POST() {
  const stats = serverDb.getAgentStats(true);
  return NextResponse.json({ success: true, message: 'Radar live status refreshed', data: stats });
}
