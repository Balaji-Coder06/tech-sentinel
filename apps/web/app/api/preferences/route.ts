import { NextRequest, NextResponse } from 'next/server';
import { serverDb } from '../../../lib/server-db';

export const dynamic = 'force-dynamic';

const D1_API_URL = (
  process.env.WORKER_API_URL ||
  process.env.NEXT_PUBLIC_WORKER_API_URL ||
  'https://tech-sentinel-api.sbalaji06.workers.dev'
).replace(/\/$/, '');

export async function GET() {
  // 1. In production (and when Cloudflare D1 is reachable), fetch from D1
  if (D1_API_URL) {
    try {
      const res = await fetch(`${D1_API_URL}/api/preferences`, {
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
      });
      if (res.ok) {
        const json = await res.json();
        if (json.data && (json.data.categories || json.data.id)) {
          // Keep local sqlite cache consistent if available
          try {
            serverDb.updatePreferences(json.data);
          } catch (e) {}
          return NextResponse.json({ success: true, data: json.data });
        }
      }
    } catch (err) {
      console.warn('Note: Could not reach Cloudflare D1 for preferences, falling back to local SQLite:', err);
    }
  }

  // 2. Fallback to local SQLite / memory state
  const prefs = serverDb.getPreferences();
  return NextResponse.json({ success: true, data: prefs });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    let d1Result: any = null;

    // 1. Persist directly to Cloudflare D1 (Production Single Source of Truth)
    if (D1_API_URL) {
      try {
        const res = await fetch(`${D1_API_URL}/api/preferences`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (res.ok) {
          const json = await res.json();
          d1Result = json.data;
        }
      } catch (err) {
        console.warn('Note: Could not persist preferences to Cloudflare D1, writing to local SQLite:', err);
      }
    }

    // 2. Also persist to local SQLite
    const localResult = serverDb.updatePreferences(body);

    const dataToReturn = d1Result || localResult || body;
    return NextResponse.json({ success: true, data: dataToReturn });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function PUT(request: NextRequest) {
  return POST(request);
}
