import { NextRequest, NextResponse } from 'next/server';
import { serverDb } from '../../../lib/server-db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const date = searchParams.get('date');

  if (date) {
    const report = serverDb.getReportByDate(date);
    if (!report) {
      return NextResponse.json({ error: 'Report not found for specified date' }, { status: 404 });
    }
    return NextResponse.json({ success: true, data: report });
  }

  const reports = serverDb.getDailyReports();
  return NextResponse.json({ success: true, count: reports.length, data: reports });
}
