"""Query real token consumption from opencode SQLite database.

Usage:
  python tools/token_stats.py          # full summary
  python tools/token_stats.py --live   # watch current session
  python tools/token_stats.py --days 30  # last N days
"""
import sqlite3, os, sys, json, datetime

DB = os.path.expanduser(r'~\.local\share\opencode\opencode.db')


def get_conn():
    if not os.path.exists(DB):
        print(f"DB not found: {DB}")
        sys.exit(1)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def total_summary(cur):
    cur.execute("""
        SELECT COUNT(*) as sessions,
               SUM(tokens_input) as inp,
               SUM(tokens_output) as outp,
               SUM(tokens_reasoning) as rsn,
               SUM(tokens_cache_read) as crd,
               SUM(tokens_cache_write) as cwr,
               SUM(cost) as cost
        FROM session
    """)
    r = cur.fetchone()
    total = (r['inp'] or 0) + (r['outp'] or 0) + (r['rsn'] or 0)
    print("=== TOTAL ===")
    print(f"  Sessions:   {r['sessions']}")
    print(f"  Input:      {r['inp'] or 0:>12,}")
    print(f"  Output:     {r['outp'] or 0:>12,}")
    print(f"  Reasoning:  {r['rsn'] or 0:>12,}")
    print(f"  Cache read: {r['crd'] or 0:>12,}")
    print(f"  Total (i+o+r): {total:>12,}")
    print(f"  Cost:       ${r['cost'] or 0:.2f}")
    return r


def by_model(cur):
    cur.execute("""
        SELECT model, COUNT(*) as cnt,
               SUM(tokens_input) as inp,
               SUM(tokens_output) as outp,
               SUM(cost) as cost
        FROM session WHERE tokens_input > 0
        GROUP BY model ORDER BY cost DESC
    """)
    rows = cur.fetchall()
    print(f"\n=== BY MODEL ({len(rows)} models) ===")
    for r in rows:
        m = json.loads(r['model']) if isinstance(r['model'], str) and r['model'].startswith('{') else r['model']
        name = m.get('id', str(r['model'])) if isinstance(m, dict) else str(m)
        print(f"  {name:<30} {r['cnt']:>3} ses  inp:{r['inp'] or 0:>10,}  out:{r['outp'] or 0:>10,}  ${r['cost'] or 0:.2f}")


def recent_sessions(cur, limit=10):
    cur.execute("""
        SELECT id, title, model, tokens_input, tokens_output,
               tokens_reasoning, cost, time_created,
               tokens_cache_read, tokens_cache_write
        FROM session WHERE tokens_input > 0
        ORDER BY time_created DESC LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    print(f"\n=== RECENT {limit} SESSIONS ===")
    hdr = "{:<10} {:<20} {:>10} {:>10} {:>8} {:>8} {:>8}  title"
    print(hdr.format('ID', 'Model', 'Input', 'Output', 'Reason', 'Cost', 'C.Rd'))
    print('-' * 90)
    for r in rows:
        m = json.loads(r['model']) if isinstance(r['model'], str) and r['model'].startswith('{') else r['model']
        name = m.get('id', str(r['model']))[:18] if isinstance(m, dict) else str(r['model'] or '')[:18]
        c = r['cost'] or 0
        print("{:<10} {:<20} {:>10,} {:>10,} {:>8,} ${:>6.2f} {:>8,}  {}".format(
            r['id'][:8], name,
            r['tokens_input'] or 0, r['tokens_output'] or 0,
            r['tokens_reasoning'] or 0, c,
            r['tokens_cache_read'] or 0,
            str(r['title'] or '')[:30]))


def by_day(cur, days=7):
    sub = days * 86400
    cur.execute("""
        SELECT date(time_created/1000, 'unixepoch') as day,
               SUM(tokens_input + tokens_output + tokens_reasoning) as total,
               SUM(cost) as cost, COUNT(*) as sessions
        FROM session
        WHERE tokens_input > 0 AND time_created > ?
        GROUP BY day ORDER BY day
    """, (int((datetime.datetime.now().timestamp() - sub) * 1000),))
    rows = cur.fetchall()
    print(f"\n=== LAST {days} DAYS ===")
    for r in rows:
        print(f"  {r['day']}  {r['total'] or 0:>12,} tokens  ${r['cost'] or 0:.2f}  ({r['sessions']} ses)")


def current_session(cur):
    cur.execute("""
        SELECT id, model, tokens_input, tokens_output, tokens_reasoning, cost
        FROM session WHERE tokens_input > 0
        ORDER BY time_created DESC LIMIT 1
    """)
    s = cur.fetchone()
    if not s:
        return
    print(f"\n=== CURRENT SESSION ({s['id'][:8]}...) ===")
    cur.execute("""
        SELECT COUNT(*) as msgs,
               SUM(CAST(json_extract(data, '$.tokens.input') AS INTEGER)) as inp,
               SUM(CAST(json_extract(data, '$.tokens.output') AS INTEGER)) as outp,
               SUM(CAST(json_extract(data, '$.tokens.reasoning') AS INTEGER)) as rsn
        FROM message WHERE session_id = ?
    """, (s['id'],))
    m = cur.fetchone()
    print(f"  Session total: inp={s['tokens_input'] or 0:,}  out={s['tokens_output'] or 0:,}  rsn={s['tokens_reasoning'] or 0:,}")
    print(f"  Messages:      {m['msgs']}  inp={m['inp'] or 0:,}  out={m['outp'] or 0:,}  rsn={m['rsn'] or 0:,}")

    cur.execute("""
        SELECT id, time_created, data
        FROM message WHERE session_id = ?
        ORDER BY time_created
    """, (s['id'],))
    msgs = cur.fetchall()
    print(f"\n  --- Turn breakdown ---")
    for i, msg in enumerate(msgs):
        d = json.loads(msg['data']) if isinstance(msg['data'], str) else {}
        t = d.get('tokens', {})
        dt = datetime.datetime.fromtimestamp(msg['time_created']/1000).strftime('%H:%M:%S')
        inp = t.get('input', 0) or 0
        out = t.get('output', 0) or 0
        rsn = t.get('reasoning', 0) or 0
        role = d.get('role', '?')[:5]
        print(f"  {i:>2}. [{dt}] {role:>5}  inp:{inp:>8,}  out:{out:>8,}  rsn:{rsn:>8,}  sum:{inp+out+rsn:>8,}")


def main():
    conn = get_conn()
    cur = conn.cursor()

    total_summary(cur)
    by_model(cur)
    recent_sessions(cur, limit=5)
    by_day(cur, days=14)

    if '--live' in sys.argv:
        current_session(cur)
    if '--days' in sys.argv:
        idx = sys.argv.index('--days')
        if idx + 1 < len(sys.argv):
            by_day(cur, int(sys.argv[idx + 1]))

    conn.close()


if __name__ == '__main__':
    main()
