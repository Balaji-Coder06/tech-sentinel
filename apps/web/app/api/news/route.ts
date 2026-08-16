import { NextRequest, NextResponse } from 'next/server';
import { serverDb } from '../../../lib/server-db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get('category') || undefined;
  const sortParam = searchParams.get('sort');
  const sortMode: 'intelligence' | 'chronological' = sortParam === 'chronological' ? 'chronological' : 'intelligence';
  const id = searchParams.get('id');

  if (id) {
    const item = serverDb.getNewsById(id);
    if (!item) {
      return NextResponse.json({ error: 'News item not found' }, { status: 404 });
    }
    return NextResponse.json({ success: true, data: item });
  }

  const categoriesParam = searchParams.get('categories');
  const allowedCategories = categoriesParam 
    ? categoriesParam.split(',').map(c => c.trim()).filter(Boolean)
    : undefined;

  const news = serverDb.getNews(category, sortMode, allowedCategories);
  const categories = serverDb.getCategories(allowedCategories);
  return NextResponse.json({ 
    success: true, 
    count: news.length, 
    categories, 
    data: news 
  });
}

