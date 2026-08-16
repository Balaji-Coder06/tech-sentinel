import { NextRequest, NextResponse } from 'next/server';
import { serverDb } from '../../../lib/server-db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type') || undefined;
  const status = searchParams.get('status') || undefined;
  const sort = (searchParams.get('sort') as 'score' | 'expiry' | 'value') || 'score';
  const id = searchParams.get('id');

  if (id) {
    const opp = serverDb.getOpportunityById(id);
    if (!opp) {
      return NextResponse.json({ error: 'Opportunity not found' }, { status: 404 });
    }
    return NextResponse.json({ success: true, data: opp });
  }

  const opps = serverDb.getOpportunities(type, status, sort);
  return NextResponse.json({ success: true, count: opps.length, data: opps });
}

