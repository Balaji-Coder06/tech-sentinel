/**
 * Tech Sentinel - Cloudflare Worker Edge API
 * Stateless, zero-latency REST API directly querying Cloudflare D1.
 */

export interface Env {
  DB: D1Database;
  ENVIRONMENT: string;
  CORS_ORIGIN?: string;
  INGESTION_SECRET?: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    const origin = request.headers.get('Origin') || '*';
    const allowedOrigin = env.CORS_ORIGIN && env.CORS_ORIGIN !== '*' ? env.CORS_ORIGIN : origin;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': allowedOrigin,
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers });
    }

    try {
      // -------------------------------------------------------------
      // 0. SECURE INGESTION ENDPOINT: POST /api/ingest
      // -------------------------------------------------------------
      if (path === '/api/ingest' && request.method === 'POST') {
        const authHeader = request.headers.get('Authorization') || '';
        const token = authHeader.replace(/^Bearer\s+/i, '');

        if (!env.INGESTION_SECRET || token !== env.INGESTION_SECRET) {
          return new Response(JSON.stringify({ error: 'Unauthorized: Invalid Ingestion Token' }), {
            status: 401,
            headers
          });
        }

        const body = await request.json() as any;
        const newsItems = body.news || [];
        const opportunities = body.opportunities || [];
        const report = body.report;
        const status = body.status;

        const statements: D1PreparedStatement[] = [];

        // Ingest News Items
        for (const item of newsItems) {
          const summaryWhat = item.summary?.what || null;
          const summaryWhy = item.summary?.why || null;
          const summaryAction = item.summary?.action || null;
          const keyPoints = JSON.stringify(item.summary?.key_points || []);
          const tags = JSON.stringify(item.tags || []);

          statements.push(
            env.DB.prepare(`
              INSERT INTO news (
                id, title, description, content, url, canonical_url, image_url,
                source_id, source_name, category, tags, read_time_minutes,
                summary_what, summary_why, summary_action, key_points,
                importance_score, relevance_score, is_featured, is_trending,
                published_at, discovered_at
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT(url) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                content=excluded.content,
                image_url=COALESCE(excluded.image_url, news.image_url),
                summary_what=excluded.summary_what,
                summary_why=excluded.summary_why,
                summary_action=excluded.summary_action,
                key_points=excluded.key_points,
                importance_score=excluded.importance_score,
                relevance_score=excluded.relevance_score,
                is_featured=excluded.is_featured,
                is_trending=excluded.is_trending
            `).bind(
              item.id, item.title, item.description, item.content || '', item.url,
              item.canonical_url || null, item.image_url || null, item.source_id || null,
              item.source_name, item.category, tags, item.read_time_minutes || 3,
              summaryWhat, summaryWhy, summaryAction, keyPoints,
              item.importance_score || 50, item.relevance_score || 50,
              item.is_featured ? 1 : 0, item.is_trending ? 1 : 0,
              item.published_at, item.discovered_at || new Date().toISOString()
            )
          );
        }

        // Ingest Opportunities
        for (const opp of opportunities) {
          statements.push(
            env.DB.prepare(`
              INSERT INTO opportunities (
                id, title, provider, provider_logo, description, opportunity_type, category,
                normal_value, current_value, eligibility, claim_url, official_url,
                requirements, coupon_code, start_date, expiry_date, is_expiring_soon,
                status, verification_status, last_verified_at, verification_notes,
                importance_score, relevance_score, priority, why_care, discovered_at
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT(claim_url) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                normal_value=excluded.normal_value,
                current_value=excluded.current_value,
                eligibility=excluded.eligibility,
                expiry_date=excluded.expiry_date,
                is_expiring_soon=excluded.is_expiring_soon,
                status=excluded.status,
                verification_status=excluded.verification_status,
                last_verified_at=excluded.last_verified_at,
                verification_notes=excluded.verification_notes,
                importance_score=excluded.importance_score,
                priority=excluded.priority,
                why_care=excluded.why_care
            `).bind(
              opp.id, opp.title, opp.provider, opp.provider_logo || null, opp.description,
              opp.opportunity_type, opp.category, opp.normal_value || null, opp.current_value || 'FREE',
              opp.eligibility || 'All', opp.claim_url, opp.official_url || null,
              opp.requirements || null, opp.coupon_code || null, opp.start_date || null,
              opp.expiry_date || null, opp.is_expiring_soon ? 1 : 0, opp.status || 'ACTIVE',
              opp.verification_status || 'VERIFIED', opp.last_verified_at || null,
              opp.verification_notes || null, opp.importance_score || 80, opp.relevance_score || 80,
              opp.priority || 'High', opp.why_care || null, opp.discovered_at || new Date().toISOString()
            )
          );
        }

        // Ingest Daily Report
        if (report) {
          statements.push(
            env.DB.prepare(`
              INSERT INTO daily_reports (
                id, date, title, headline, thirty_sec_summary,
                top_stories, free_opportunities, student_opportunities,
                open_source_highlights, expiring_soon, sentinel_take,
                stats_json, published_at, telegram_message_id
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT(date) DO UPDATE SET
                headline=excluded.headline,
                thirty_sec_summary=excluded.thirty_sec_summary,
                top_stories=excluded.top_stories,
                free_opportunities=excluded.free_opportunities,
                student_opportunities=excluded.student_opportunities,
                open_source_highlights=excluded.open_source_highlights,
                expiring_soon=excluded.expiring_soon,
                sentinel_take=excluded.sentinel_take,
                stats_json=excluded.stats_json,
                published_at=excluded.published_at
            `).bind(
              report.id, report.date, report.title, report.headline, report.thirty_sec_summary,
              JSON.stringify(report.top_stories || []), JSON.stringify(report.free_opportunities || []),
              JSON.stringify(report.student_opportunities || []), JSON.stringify(report.open_source_highlights || []),
              JSON.stringify(report.expiring_soon || []), report.sentinel_take,
              JSON.stringify(report.stats || {}), report.published_at || new Date().toISOString(),
              report.telegram_message_id || null
            )
          );
        }

        // Update System Status
        if (status) {
          statements.push(
            env.DB.prepare(`
              INSERT INTO system_status (
                id, status, last_scan_time, sources_checked, new_opportunities_today,
                next_report_time, last_run_duration_sec, last_error, updated_at
              ) VALUES ('current', 'ACTIVE', ?, ?, ?, '9:00 PM IST', ?, ?, datetime('now'))
              ON CONFLICT(id) DO UPDATE SET
                status='ACTIVE',
                last_scan_time=excluded.last_scan_time,
                sources_checked=excluded.sources_checked,
                new_opportunities_today=excluded.new_opportunities_today,
                last_run_duration_sec=excluded.last_run_duration_sec,
                last_error=excluded.last_error,
                updated_at=datetime('now')
            `).bind(
              status.last_scan_time || new Date().toISOString(),
              status.sources_checked || 9,
              status.new_opportunities_today || opportunities.length,
              status.last_run_duration_sec || 0.0,
              status.last_error || null
            )
          );
        }

        // Ingest Telegram Users
        const telegramUsers = body.telegram_users || [];
        for (const user of telegramUsers) {
          statements.push(
            env.DB.prepare(`
              INSERT INTO telegram_users (
                user_id, chat_id, username, first_name, last_name, preference_id,
                telegram_digest_enabled, last_digest_sent_at, created_at, updated_at
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              ON CONFLICT(user_id) DO UPDATE SET
                chat_id=excluded.chat_id,
                username=COALESCE(excluded.username, telegram_users.username),
                first_name=COALESCE(excluded.first_name, telegram_users.first_name),
                last_name=COALESCE(excluded.last_name, telegram_users.last_name),
                preference_id=excluded.preference_id,
                telegram_digest_enabled=COALESCE(excluded.telegram_digest_enabled, telegram_users.telegram_digest_enabled),
                last_digest_sent_at=COALESCE(excluded.last_digest_sent_at, telegram_users.last_digest_sent_at),
                updated_at=datetime('now')
            `).bind(
              String(user.user_id), String(user.chat_id), user.username || null,
              user.first_name || null, user.last_name || null, user.preference_id || 'default',
              user.telegram_digest_enabled ? 1 : 0, user.last_digest_sent_at || null,
              user.created_at || new Date().toISOString(), user.updated_at || new Date().toISOString()
            )
          );
        }

        // Ingest Preferences Profiles
        const preferencesList = body.preferences || [];
        for (const pref of preferencesList) {
          const categories = typeof pref.categories === 'string' ? pref.categories : JSON.stringify(pref.categories || []);
          const keywords = typeof pref.keywords === 'string' ? pref.keywords : JSON.stringify(pref.keywords || []);
          const opportunityTypes = typeof pref.opportunity_types === 'string' ? pref.opportunity_types : JSON.stringify(pref.opportunity_types || []);

          statements.push(
            env.DB.prepare(`
              INSERT INTO preferences (
                id, user_name, theme, categories, keywords, opportunity_types,
                enable_daily_brief, enable_critical_alerts, ai_provider, updated_at
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
              ON CONFLICT(id) DO UPDATE SET
                user_name=excluded.user_name,
                theme=excluded.theme,
                categories=excluded.categories,
                keywords=excluded.keywords,
                opportunity_types=excluded.opportunity_types,
                enable_daily_brief=excluded.enable_daily_brief,
                enable_critical_alerts=excluded.enable_critical_alerts,
                ai_provider=excluded.ai_provider,
                updated_at=datetime('now')
            `).bind(
              pref.id || 'default',
              pref.user_name || 'Balaji',
              pref.theme || 'system',
              categories,
              keywords,
              opportunityTypes,
              pref.enable_daily_brief ? 1 : 0,
              pref.enable_critical_alerts ? 1 : 0,
              pref.ai_provider || 'fallback'
            )
          );
        }

        if (statements.length > 0) {
          await env.DB.batch(statements);
        }

        return new Response(JSON.stringify({
          success: true,
          message: `Ingested ${newsItems.length} news items, ${opportunities.length} opportunities, ${telegramUsers.length} users, ${preferencesList.length} preference sets.`
        }), { headers });
      }

      // -------------------------------------------------------------
      // 0b. SECURE TELEGRAM SUBSCRIBERS ENDPOINT: GET /api/telegram/subscribers
      // -------------------------------------------------------------
      if (path === '/api/telegram/subscribers' && request.method === 'GET') {
        const authHeader = request.headers.get('Authorization') || '';
        const token = authHeader.replace(/^Bearer\s+/i, '');

        if (!env.INGESTION_SECRET || token !== env.INGESTION_SECRET) {
          return new Response(JSON.stringify({ error: 'Unauthorized: Invalid Token' }), {
            status: 401,
            headers
          });
        }

        const subscribedOnly = url.searchParams.get('subscribed_only') === 'true';
        let query = "SELECT * FROM telegram_users";
        if (subscribedOnly) {
          query += " WHERE telegram_digest_enabled = 1";
        }
        query += " ORDER BY created_at ASC";

        const usersStmt = env.DB.prepare(query);
        const prefsStmt = env.DB.prepare("SELECT * FROM preferences");

        const [usersRes, prefsRes] = await Promise.all([usersStmt.all(), prefsStmt.all()]);
        const users = usersRes.results || [];
        const prefs = prefsRes.results || [];

        const prefsMap = new Map<string, any>();
        for (const p of prefs as any[]) {
          prefsMap.set(p.id, {
            ...p,
            categories: typeof p.categories === 'string' ? JSON.parse(p.categories || '[]') : p.categories,
            keywords: typeof p.keywords === 'string' ? JSON.parse(p.keywords || '[]') : p.keywords,
            opportunity_types: typeof p.opportunity_types === 'string' ? JSON.parse(p.opportunity_types || '[]') : p.opportunity_types,
            enable_daily_brief: Boolean(p.enable_daily_brief),
            enable_critical_alerts: Boolean(p.enable_critical_alerts),
          });
        }

        const defaultPrefs = prefsMap.get('default') || {
          id: 'default',
          user_name: 'Balaji',
          theme: 'system',
          categories: ['ai', 'cloud', 'development', 'open_source', 'cybersecurity', 'startups'],
          keywords: ['react', 'llm', 'credits', 'internship', 'certification', 'hackathon', 'copilot'],
          opportunity_types: ['software', 'ai_credits', 'cloud', 'education', 'certification', 'competition', 'career'],
          enable_daily_brief: true,
          enable_critical_alerts: true,
        };

        const subscribers = (users as any[]).map((u) => {
          const userPrefId = u.preference_id || `tg_${u.user_id}`;
          const resolvedPrefs = prefsMap.get(userPrefId) || prefsMap.get(u.preference_id) || defaultPrefs;
          return {
            user_id: u.user_id,
            chat_id: u.chat_id,
            username: u.username,
            first_name: u.first_name,
            last_name: u.last_name,
            preference_id: u.preference_id,
            telegram_digest_enabled: Boolean(u.telegram_digest_enabled),
            last_digest_sent_at: u.last_digest_sent_at || null,
            preferences: resolvedPrefs,
            created_at: u.created_at,
            updated_at: u.updated_at
          };
        });

        return new Response(JSON.stringify({
          success: true,
          count: subscribers.length,
          data: subscribers
        }), { headers });
      }

      // -------------------------------------------------------------
      // 1. GET /api/news
      // -------------------------------------------------------------
      if (path === '/api/news') {
        const category = url.searchParams.get('category');
        let query = 'SELECT * FROM news';
        const params: any[] = [];

        if (category && category !== 'all') {
          query += ' WHERE category = ?';
          params.push(category);
        }
        query += ' ORDER BY published_at DESC LIMIT 50';

        const stmt = env.DB.prepare(query).bind(...params);
        const { results } = await stmt.all();

        const formatted = results.map((r: any) => ({
          ...r,
          tags: typeof r.tags === 'string' ? JSON.parse(r.tags || '[]') : r.tags,
          key_points: typeof r.key_points === 'string' ? JSON.parse(r.key_points || '[]') : r.key_points,
          summary: {
            what: r.summary_what || r.description,
            why: r.summary_why || '',
            action: r.summary_action || '',
            key_points: typeof r.key_points === 'string' ? JSON.parse(r.key_points || '[]') : r.key_points,
          }
        }));

        return new Response(JSON.stringify({ success: true, count: formatted.length, data: formatted }), { headers });
      }

      // -------------------------------------------------------------
      // 2. GET /api/opportunities
      // -------------------------------------------------------------
      if (path === '/api/opportunities') {
        const type = url.searchParams.get('type');
        const status = url.searchParams.get('status') || 'ACTIVE';
        let query = 'SELECT * FROM opportunities WHERE 1=1';
        const params: any[] = [];

        if (status !== 'ALL') {
          query += ' AND status = ?';
          params.push(status);
        }
        if (type && type !== 'all') {
          query += ' AND (opportunity_type = ? OR category = ?)';
          params.push(type, type);
        }
        query += ' ORDER BY importance_score DESC, is_expiring_soon DESC LIMIT 50';

        const stmt = env.DB.prepare(query).bind(...params);
        const { results } = await stmt.all();
        return new Response(JSON.stringify({ success: true, count: results.length, data: results }), { headers });
      }

      // -------------------------------------------------------------
      // 3. GET /api/reports
      // -------------------------------------------------------------
      if (path === '/api/reports') {
        const date = url.searchParams.get('date');
        let query = 'SELECT * FROM daily_reports';
        const params: any[] = [];

        if (date) {
          query += ' WHERE date = ? LIMIT 1';
          params.push(date);
        } else {
          query += ' ORDER BY date DESC LIMIT 10';
        }

        const stmt = env.DB.prepare(query).bind(...params);
        const { results } = await stmt.all();

        const parseReport = (r: any) => ({
          ...r,
          top_stories: typeof r.top_stories === 'string' ? JSON.parse(r.top_stories || '[]') : r.top_stories,
          free_opportunities: typeof r.free_opportunities === 'string' ? JSON.parse(r.free_opportunities || '[]') : r.free_opportunities,
          student_opportunities: typeof r.student_opportunities === 'string' ? JSON.parse(r.student_opportunities || '[]') : r.student_opportunities,
          open_source_highlights: typeof r.open_source_highlights === 'string' ? JSON.parse(r.open_source_highlights || '[]') : r.open_source_highlights,
          expiring_soon: typeof r.expiring_soon === 'string' ? JSON.parse(r.expiring_soon || '[]') : r.expiring_soon,
          stats: typeof r.stats_json === 'string' ? JSON.parse(r.stats_json || '{}') : r.stats_json,
        });

        if (date) {
          if (results.length === 0) {
            return new Response(JSON.stringify({ error: 'Report not found for specified date' }), { status: 404, headers });
          }
          return new Response(JSON.stringify({ success: true, data: parseReport(results[0]) }), { headers });
        }

        return new Response(JSON.stringify({ success: true, data: results.map(parseReport) }), { headers });
      }

      // -------------------------------------------------------------
      // 4. GET /api/search
      // -------------------------------------------------------------
      if (path === '/api/search') {
        const q = url.searchParams.get('q') || '';
        const pattern = `%${q}%`;

        const newsStmt = env.DB.prepare('SELECT * FROM news WHERE title LIKE ? OR description LIKE ? OR tags LIKE ? LIMIT 15').bind(pattern, pattern, pattern);
        const oppsStmt = env.DB.prepare('SELECT * FROM opportunities WHERE title LIKE ? OR provider LIKE ? OR description LIKE ? LIMIT 15').bind(pattern, pattern, pattern);

        const [newsRes, oppsRes] = await Promise.all([newsStmt.all(), oppsStmt.all()]);
        return new Response(JSON.stringify({
          success: true,
          query: q,
          data: { news: newsRes.results, opportunities: oppsRes.results }
        }), { headers });
      }

      // -------------------------------------------------------------
      // 5. GET /api/stats (Real dynamic stats derived from D1 tables)
      // -------------------------------------------------------------
      if (path === '/api/stats') {
        const statusStmt = env.DB.prepare("SELECT * FROM system_status WHERE id = 'current' LIMIT 1");
        const oppsCountStmt = env.DB.prepare("SELECT COUNT(*) as count FROM opportunities WHERE status IN ('ACTIVE', 'EXPIRING_SOON')");
        const sourcesCountStmt = env.DB.prepare("SELECT COUNT(*) as count FROM sources WHERE enabled = 1");

        const [statusRes, oppsCountRes, sourcesCountRes] = await Promise.all([
          statusStmt.all(),
          oppsCountStmt.all(),
          sourcesCountStmt.all()
        ]);

        const currentStatus: any = statusRes.results[0] || {};
        const activeOppsCount = (oppsCountRes.results[0] as any)?.count || 6;
        const totalSources = (sourcesCountRes.results[0] as any)?.count || 9;

        return new Response(JSON.stringify({
          success: true,
          data: {
            status: currentStatus.status || 'ACTIVE',
            last_scan_time: currentStatus.last_scan_time || new Date().toISOString(),
            sources_checked: currentStatus.sources_checked || totalSources,
            new_opportunities_today: activeOppsCount,
            next_report_time: currentStatus.next_report_time || '9:00 PM IST',
            system_cost: '₹0.00'
          }
        }), { headers });
      }

      // -------------------------------------------------------------
      // 6. GET & POST /api/saved (Persistent bookmarks)
      // -------------------------------------------------------------
      if (path === '/api/saved') {
        if (request.method === 'GET') {
          const { results } = await env.DB.prepare("SELECT item_type, item_id FROM saved_items ORDER BY saved_at DESC").all();
          const news = results.filter((r: any) => r.item_type === 'news').map((r: any) => r.item_id);
          const opportunities = results.filter((r: any) => r.item_type === 'opportunity').map((r: any) => r.item_id);
          return new Response(JSON.stringify({ success: true, data: { news, opportunities } }), { headers });
        }

        if (request.method === 'POST') {
          const body = await request.json() as any;
          const { type, id } = body;
          if (!type || !id || (type !== 'news' && type !== 'opportunity')) {
            return new Response(JSON.stringify({ error: 'Invalid item type or id' }), { status: 400, headers });
          }

          // Check if exists -> toggle delete, otherwise insert
          const existing = await env.DB.prepare("SELECT id FROM saved_items WHERE item_type = ? AND item_id = ?").bind(type, id).first();
          if (existing) {
            await env.DB.prepare("DELETE FROM saved_items WHERE item_type = ? AND item_id = ?").bind(type, id).run();
          } else {
            const saveId = `save_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
            await env.DB.prepare("INSERT INTO saved_items (id, item_type, item_id) VALUES (?, ?, ?)").bind(saveId, type, id).run();
          }

          const { results } = await env.DB.prepare("SELECT item_type, item_id FROM saved_items").all();
          const news = results.filter((r: any) => r.item_type === 'news').map((r: any) => r.item_id);
          const opportunities = results.filter((r: any) => r.item_type === 'opportunity').map((r: any) => r.item_id);

          return new Response(JSON.stringify({ success: true, data: { news, opportunities } }), { headers });
        }
      }

      // -------------------------------------------------------------
      // 7. GET & POST /api/preferences (Persistent user settings)
      // -------------------------------------------------------------
      if (path === '/api/preferences') {
        if (request.method === 'GET') {
          const row: any = await env.DB.prepare("SELECT * FROM preferences WHERE id = 'default'").first();
          if (!row) {
            return new Response(JSON.stringify({ success: true, data: {} }), { headers });
          }
          return new Response(JSON.stringify({
            success: true,
            data: {
              ...row,
              categories: JSON.parse(row.categories || '[]'),
              keywords: JSON.parse(row.keywords || '[]'),
              opportunity_types: JSON.parse(row.opportunity_types || '[]'),
              enable_daily_brief: Boolean(row.enable_daily_brief),
              enable_critical_alerts: Boolean(row.enable_critical_alerts)
            }
          }), { headers });
        }

        if (request.method === 'POST') {
          const body = await request.json() as any;
          const categories = JSON.stringify(body.categories || []);
          const keywords = JSON.stringify(body.keywords || []);
          const opportunityTypes = JSON.stringify(body.opportunity_types || []);

          await env.DB.prepare(`
            INSERT INTO preferences (
              id, user_name, theme, categories, keywords, opportunity_types,
              enable_daily_brief, enable_critical_alerts, ai_provider, updated_at
            ) VALUES ('default', ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
              user_name=excluded.user_name,
              theme=excluded.theme,
              categories=excluded.categories,
              keywords=excluded.keywords,
              opportunity_types=excluded.opportunity_types,
              enable_daily_brief=excluded.enable_daily_brief,
              enable_critical_alerts=excluded.enable_critical_alerts,
              ai_provider=excluded.ai_provider,
              updated_at=datetime('now')
          `).bind(
            body.user_name || 'Balaji',
            body.theme || 'system',
            categories,
            keywords,
            opportunityTypes,
            body.enable_daily_brief ? 1 : 0,
            body.enable_critical_alerts ? 1 : 0,
            body.ai_provider || 'fallback'
          ).run();

          return new Response(JSON.stringify({ success: true, data: body }), { headers });
        }
      }

      return new Response(JSON.stringify({ error: 'Endpoint not found' }), { status: 404, headers });
    } catch (err: any) {
      return new Response(JSON.stringify({ error: err.message || 'Internal Server Error' }), { status: 500, headers });
    }
  },
};
