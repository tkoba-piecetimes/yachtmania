"""Editorial and searchable surfaces using the existing normalized data."""
import json
import re
from datetime import date, datetime, timedelta, timezone
from html import escape as h


def section_title(number, en, ja, link='', label='すべて見る'):
    return f'<div class="section-heading"><div><p class="eyebrow">{number} / {en}</p><h2>{ja}</h2></div>' + (f'<a class="text-link" href="{link}">{label} ↗</a>' if link else '') + '</div>'


def event_dates(event):
    year = event.get('year')
    if not year:
        return None
    match = re.fullmatch(r'(\d{1,2})月(\d{1,2})日(?:[～〜~－-](?:(\d{1,2})月)?(\d{1,2})日)?', event.get('date_text', '').strip())
    if not match:
        return None
    m, d, em, ed = match.groups()
    try:
        start = date(int(year), int(m), int(d))
        end = date(int(year) + (1 if em and int(em) < int(m) else 0), int(em or m), int(ed or d))
        return (start, end) if end >= start else None
    except ValueError:
        return None


def event_state(event, today=None):
    today = today or datetime.now(timezone(timedelta(hours=9))).date()
    dates = event_dates(event)
    if not dates:
        return '日程を確認'
    return '終了' if dates[1] < today else ('開催期間中' if dates[0] <= today else '開催予定')


def events_html(g, data, limit=None):
    events = [e for e in data['calendar'] if e.get('date_text') and not re.search('総会|講習|会議', e['event'])]
    events.sort(key=lambda e: (event_state(e) == '終了', event_dates(e) is None, (event_dates(e) or (date.max,))[0]))
    if limit:
        events = [e for e in events if event_state(e) != '終了'][:limit]
    out = ''
    for e in events:
        region = '全国大会' if '全日本' in e['event'] else g.REGIONS.get(e.get('region'), {}).get('name', '全国')
        out += f'<article class="event-row" data-event-state="{event_state(e)}"><div><span class="status">{event_state(e)}</span><p class="event-date">{h(str(e.get("year", "")))} {h(e["date_text"] or "公式発表を確認")}</p></div><div><span class="meta">{h(region)}</span><h3><a href="{h(e["source_url"])}" target="_blank" rel="noopener">{h(e["event"])} ↗</a></h3><span class="meta">出典：{h(e["source"])}</span></div></article>'
    return out or '<p>掲載できる大会はありません。</p>'


def home(g, data, articles):
    n, r = len(data['universities']), len(data['results'])
    body = f'''<div class="season-strip"><span>COLLEGE SAILING JOURNAL</span><span>全国9水域の大学ヨット</span></div>
    <section class="sailing-hero"><div class="hero-copy"><p class="eyebrow">YACHTMANIA / SAIL TOGETHER</p><h1>風を読む。<br>仲間と、挑む。</h1><p>自分の海も、ライバルの海も。<br>大学ヨットに夢中な、すべての人へ。</p><div class="hero-actions"><a class="cta" href="results/">大会結果を見る ↗</a><a class="text-link" href="my-team/">マイチームを選ぶ →</a></div></div><img src="assets/hero.jpg" alt="帆を上げ、仲間と海を進むヨットのイメージ" width="1440" height="810"><span class="hero-caption">ONE TEAM. ONE HORIZON.</span></section>
    <div class="metrics"><div><strong>09</strong><span>水域の成績を掲載</span></div><div><strong>{n}</strong><span>掲載大学 / 2水域</span></div><div><strong>{r}</strong><span>公式成績資料</span></div><a href="archive/">記録から、次のレースへ。<br><b>データベースを開く ↗</b></a></div>
    <section class="regatta-section">{section_title('01','REGATTA CENTER','次のレースを、見逃すな。','calendar/','大会カレンダー')}<div class="regatta-grid"><div class="event-list">{events_html(g,data,3)}</div><aside class="results-promo"><p class="eyebrow">RACE RESULTS</p><h3>あの大会の結果を、<br>もう一度。</h3><p>水域・年度・クラスから、<br>公式成績を探そう。</p><div class="class-links"><a href="results/?class=470級">470級 ↗</a><a href="results/?class=スナイプ級">スナイプ級 ↗</a></div><p class="meta">成績の掲載年度は検索画面で確認できます。</p></aside></div><p class="meta">日程は近畿北陸学連・全日本学連の掲載情報。開催期間の表示は日付によるもので、実施状況の速報ではありません。</p></section>
    <section>{section_title('02','SAILING AREAS','あなたの水域は、ここに。','regions/','水域一覧')}<div class="area-grid">'''
    for i, code in enumerate(g.REGION_ORDER, 1):
        count = len(data['by_region'].get(code, []))
        body += f'<a class="area-card" href="regions/{code}/"><span class="area-index">{i:02}</span><h3>{h(g.REGIONS[code]["name"])}</h3><span class="meta">{len(data["results_by_region"].get(code, []))} 成績資料 / {str(count)+"大学" if count else "大学情報は未掲載"}</span><span class="area-arrow">↗</span></a>'
    body += '</div></section>'
    body += f'''<section class="myteam-banner"><div><p class="eyebrow">MY TEAM</p><h2>いつものチームへ、まっすぐ。</h2><p>応援する大学を、この端末に保存。<br>大学情報と水域の大会成績にすぐアクセス。</p></div><a class="cta" href="my-team/">マイチームを選ぶ →</a></section>'''
    if articles:
        body += '<section>' + section_title('03','JOURNAL','ヨットを、もっと深く。','articles/','読みもの一覧') + '<div class="digest">' + ''.join(g.article_card(a,'') for a in articles[:3]) + '</div></section>'
    body += f'''<section class="support-feature" id="support"><p class="eyebrow">BEYOND THE RACE / PR</p><h2>その挑戦を、<br>部活の未来につなげよう。</h2><div class="support-cards"><div><h3>部活の活動を、もっと広げたい。</h3><p>遠征費や用具費。チームの活動を支える企業協賛をツナカレで。</p>{g.tunakare_link(g.tunakare_url(g.TUNAKARE_BASE['listing_lp'],'listing'),'協賛募集を無料で掲載 ↗','cv_listing_click')}</div><div><h3>頑張る部活を、応援したい。</h3><p>活動内容や協賛条件を確認して、応援したい部活との接点を。</p>{g.tunakare_link(g.SPONSOR_CTA_URL,'協賛募集中の部活を探す ↗','cv_sponsor_click')}</div></div></section>'''
    g.write_page('',g.page('','ヨットマニア | 大学ヨットの大会・結果・データベース',body,data['meta'],desc='全国9水域の大学ヨット。大会日程、470級・スナイプ級の成績、大学情報を探せるヨットマニア。'))


def result_info(g, p):
    parsed_path = g.PARSED_DIR / f'{p["id"]}.json'
    parsed = json.loads(parsed_path.read_text(encoding='utf-8')) if parsed_path.exists() else None
    names = []
    if parsed:
        names = [b.get('university', '') for b in parsed.get('boats', [])] + [b.get('name', '') for b in parsed.get('rows', [])]
    return parsed, sorted(set(filter(None, names)))


def result_table(g, parsed):
    if not parsed:
        return '<p class="note">この成績は公式PDFで確認できます。ページ内の表はまだ掲載していません。</p>'
    return g.render_boat_table(parsed) if parsed['tier'] == 'boat' else g.render_summary_table(parsed)


def select(name, label, options):
    return f'<label>{label}<select name="{name}"><option value="">すべて</option>' + ''.join(f'<option value="{h(str(v))}">{h(str(t))}</option>' for v,t in options) + '</select></label>'


def results(g, data, archive=False):
    title = '成績データベース' if archive else '大会結果'
    route = 'archive' if archive else 'results'
    years = sorted(set(p['year_label'] for p in data['results']), reverse=True)
    classes = sorted(set(p['class'] for p in data['results']))
    body = f'<div class="page-intro"><p class="eyebrow">RECORDS / COLLEGE SAILING</p><h1>{title}</h1><p>水域、年度、クラス。気になるレースの記録へ。</p></div>'
    if archive:
        parsed_count = sum(1 for p in data['results'] if (g.PARSED_DIR / f'{p["id"]}.json').exists())
        body += f'<div class="archive-coverage"><strong>{len(data["results"])} 成績資料</strong><span>ページ内の表：{parsed_count}件</span><span>掲載年度：{h("・".join(years))}</span><a href="../my-team/">大学から探す →</a></div>'
    body += '<div data-filter-surface><form class="filters" role="search" aria-label="大会成績を検索">'
    body += select('region','水域',[(c,g.REGIONS[c]['name']) for c in g.REGION_ORDER])
    year_select = select('year','年度',[(y,y) for y in years])
    if not archive and years:
        year_select = year_select.replace('<select name="year">',f'<select name="year" data-default="{h(years[0])}">')
    body += year_select
    body += select('class','クラス',[(c,c) for c in classes])
    body += '<label class="search-field">大会名・大学名<input name="q" type="search" placeholder="例：関東、同志社大学" autocomplete="off"></label><button type="reset" class="reset-button">条件をクリア</button></form>'
    body += f'<div class="result-summary"><p data-count role="status" aria-live="polite">{len(data["results"])}件の成績</p><span class="meta">掲載年度：{h("・".join(years))} / 出典：全日本学生ヨット連盟</span></div><p class="meta">大学名は掲載済みの表を検索します。表が未掲載の資料・表記の異なる大学は見つからない場合があります。年度は大会年度です。</p><p class="empty-state" data-empty hidden>条件に一致する成績がありません。条件を減らすか、「条件をクリア」を押してください。</p>'
    for p in sorted(data['results'],key=lambda p:(p['year_label'],p['first_detected_at']),reverse=True):
        parsed, names = result_info(g,p)
        search = ' '.join([p['filename'],g.REGIONS.get(p['region'],{}).get('name',''),*names])
        body += f'<article class="result-card" data-filter-item data-region="{h(p["region"])}" data-year="{h(p["year_label"])}" data-class="{h(p["class"])}" data-search="{h(search)}"><div class="result-card-top"><span class="eyebrow">{h(p["year_label"])} / {h(g.REGIONS.get(p["region"],{}).get("name","全国"))}</span><span class="class-badge">{h(p["class"])}</span></div><h2>{h(p["filename"].removesuffix(".pdf"))}</h2>'
        body += f'<p class="meta">掲載検知：{h(p["first_detected_at"])}（大会開催日ではありません）</p>'
        body += '<details class="inline-results"><summary>成績表をこのページで見る</summary>' + result_table(g,parsed) + '<p class="meta">順位・得点は公式資料の掲載値です。クラスや予選・決勝が異なる表の得点は合算していません。</p></details>' if parsed else result_table(g,None)
        body += f'<div class="result-links"><a href="{h(p["url"])}" target="_blank" rel="noopener">公式PDFを開く ↗</a>'
        if parsed:
            body += f'<a href="../results/{p["id"]}/">この大会の詳細 →</a>'
        body += '</div></article>'
    body += '</div>'
    if archive:
        body += '<p class="note">掲載のない年度は未収録です。記録が存在しないことを示すものではありません。</p>'
    g.write_page(route,g.page('../',title+' | ヨットマニア',body,data['meta'],path=route+'/',desc='大学ヨットの大会結果を水域・年度・クラス・大学名から検索。成績表をページ内で閲覧できます。'))


def calendar(g, data):
    body = '<div class="page-intro"><p class="eyebrow">REGATTA CALENDAR</p><h1>大会カレンダー</h1><p>次のスタートラインを、ここで確かめる。</p></div>'
    body += '<div data-calendar><div class="calendar-tabs" role="group" aria-label="日程の表示"><button type="button" data-period="upcoming" aria-pressed="true">開催中・これから</button><button type="button" data-period="past" aria-pressed="false">終了した大会</button><button type="button" data-period="all" aria-pressed="false">すべて</button></div><p class="meta">開催期間の表示は日付によるものです。延期・中止・時刻などはリンク先の公式発表をご確認ください。</p><div class="event-list">' + events_html(g,data) + '</div><p data-calendar-empty hidden>該当する大会はありません。</p></div>'
    meetings = [e for e in data['calendar'] if re.search('総会|講習|会議',e['event'])]
    if meetings:
        body += '<section><details><summary>学連行事・講習会を見る</summary>' + g.calendar_table(''.join(g.calendar_row(e,'../') for e in meetings)) + '</details></section>'
    official = [e for e in data['calendar'] if not e.get('date_text')]
    if official:
        body += '<section><h2>全国大会の公式案内</h2><p class="note">大会要項・公式掲示などの最新情報はこちら。</p><ul>' + ''.join(f'<li><a href="{h(e["source_url"])}" target="_blank" rel="noopener">{h(e["event"])} ↗</a></li>' for e in official) + '</ul></section>'
    if data['schedule_pdfs']:
        body += '<section><h2>水域別の公式スケジュール資料</h2><p class="note">過年度の資料を含みます。ファイル名の年度をご確認ください。</p><ul>' + ''.join(f'<li><a href="{h(p["url"])}" target="_blank" rel="noopener">{h(p["filename"])}</a></li>' for p in data['schedule_pdfs']) + '</ul></section>'
    body += '<p class="note">日付付き予定は近畿北陸学連のスケジュールから掲載しています。全国のすべての大会を網羅しているものではありません。</p>'
    g.write_page('calendar',g.page('../','大会カレンダー | ヨットマニア',body,data['meta'],path='calendar/'))


def my_team(g,data):
    body = '<div class="page-intro"><p class="eyebrow">YOUR TEAM. YOUR SAILING.</p><h1>マイチーム</h1><p>応援する大学を選んで、自分だけのヨットマニアに。</p></div><section class="saved-teams"><h2>保存した大学</h2><p class="meta">このブラウザーだけに保存されます。登録・ログインは不要です。</p><div data-saved-teams class="team-grid"></div><p data-save-status role="status" aria-live="polite"></p><noscript>保存機能にはJavaScriptが必要です。下の一覧から大学ページをご覧いただけます。</noscript></section><div data-filter-surface><form class="filters" role="search" aria-label="大学を検索">'
    body += select('region','水域',[(c,g.REGIONS[c]['name']) for c in g.REGION_ORDER if data['by_region'].get(c)])
    body += '<label class="search-field">大学名<input name="q" type="search" placeholder="大学名で検索" autocomplete="off"></label><button type="reset" class="reset-button">条件をクリア</button></form><p data-count role="status" aria-live="polite"></p><p class="meta">大学ディレクトリは関東・近畿北陸の46校を掲載。他水域の成績は「大会結果」で確認できます。</p><p class="empty-state" data-empty hidden>該当する大学がありません。条件をクリアしてお試しください。</p><div class="team-grid">'
    for u in data['universities']:
        body += f'<article class="team-card" data-filter-item data-region="{h(u["region"])}" data-search="{h(u["name"])}" data-team="{h(u["slug"])}"><span class="meta">{h(g.REGIONS[u["region"]]["name"])}水域</span><h2><a href="../universities/{h(u["slug"])}/">{h(u["name"])}</a></h2><p class="meta">{h(u.get("harbor") or "活動拠点は公式サイトをご確認ください")}</p><button type="button" class="save-team" data-save-team="{h(u["slug"])}" data-name="{h(u["name"])}" data-region="{h(u["region"])}" aria-pressed="false">マイチームに保存</button></article>'
    body += '</div></div>'
    g.write_page('my-team',g.page('../','マイチーム | ヨットマニア',body,data['meta'],path='my-team/'))
