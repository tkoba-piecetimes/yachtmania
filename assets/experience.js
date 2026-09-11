'use strict';
(() => {
  const currentPath = location.pathname.replace(/index\.html$/,'').replace(/\/$/,'');
  document.querySelectorAll('.global-nav a').forEach(link => {
    const url = new URL(link.href);
    if (!url.hash && url.pathname.replace(/index\.html$/,'').replace(/\/$/,'') === currentPath) link.setAttribute('aria-current','page');
  });
  document.querySelectorAll('.tbl').forEach(table => {
    table.tabIndex = 0;
    table.setAttribute('role','region');
    table.setAttribute('aria-label','成績・日程の表。幅が収まらない場合は横スクロールできます');
  });
  const normalize = value => String(value || '').normalize('NFKC').toLocaleLowerCase().replace(/\s+/g, '');
  document.querySelectorAll('[data-filter-surface]').forEach(surface => {
    const form = surface.querySelector('form');
    const fields = [...form.querySelectorAll('[name]')];
    const items = [...surface.querySelectorAll('[data-filter-item]')];
    const apply = (updateUrl = true) => {
      let count = 0;
      const values = Object.fromEntries(fields.map(field => [field.name, field.value]));
      for (const item of items) {
        item.hidden = !Object.entries(values).every(([key,value]) => !value || (key === 'q' ? normalize(item.dataset.search).includes(normalize(value)) : item.dataset[key] === value));
        if (!item.hidden) count++;
      }
      surface.querySelector('[data-count]').textContent = `${count}件 / 全${items.length}件`;
      surface.querySelector('[data-empty]').hidden = count > 0;
      if (updateUrl) {
        const url = new URL(location.href);
        for (const [key,value] of Object.entries(values)) {
          const field = fields.find(field => field.name === key);
          if (value || field.dataset.default) url.searchParams.set(key,value);
          else url.searchParams.delete(key);
        }
        history.replaceState(null,'',url);
      }
    };
    const readUrl = () => {
      const params = new URLSearchParams(location.search);
      fields.forEach(field => { field.value = params.has(field.name) ? params.get(field.name) : (field.dataset.default || ''); });
      apply(false);
    };
    form.addEventListener('submit',event => { event.preventDefault(); apply(); });
    form.addEventListener('input',() => apply());
    form.addEventListener('change',() => apply());
    form.addEventListener('reset',() => setTimeout(() => apply(),0));
    window.addEventListener('popstate',readUrl);
    readUrl();
  });
  document.querySelectorAll('[data-calendar]').forEach(surface => {
    const buttons = [...surface.querySelectorAll('[data-period]')];
    const rows = [...surface.querySelectorAll('[data-event-state]')];
    function show(period) {
      let count = 0;
      rows.forEach(row => {
        const past = row.dataset.eventState === '終了';
        row.hidden = period === 'past' ? !past : period === 'upcoming' ? past : false;
        if (!row.hidden) count++;
      });
      buttons.forEach(button => button.setAttribute('aria-pressed',String(button.dataset.period === period)));
      surface.querySelector('[data-calendar-empty]').hidden = count > 0;
    }
    buttons.forEach(button => button.addEventListener('click',() => show(button.dataset.period)));
    show('upcoming');
  });
  const savedContainer = document.querySelector('[data-saved-teams]');
  if (savedContainer) {
    const key = 'yachtmania.myTeams.v1';
    const buttons = [...document.querySelectorAll('[data-save-team]')];
    const valid = new Map(buttons.map(button => [button.dataset.saveTeam,button]));
    const status = document.querySelector('[data-save-status]');
    let saved = [];
    try {
      const value = JSON.parse(localStorage.getItem(key) || '[]');
      if (Array.isArray(value)) saved = [...new Set(value.filter(slug => valid.has(slug)))];
    } catch { status.textContent = 'このブラウザーでは保存を読み込めません。大学の一覧は利用できます。'; }
    const render = () => {
      savedContainer.replaceChildren();
      if (!saved.length) {
        const p = document.createElement('p');
        p.textContent = 'まだ保存していません。下の一覧から応援する大学を選んでください。';
        savedContainer.append(p);
      }
      buttons.forEach(button => {
        const selected = saved.includes(button.dataset.saveTeam);
        button.setAttribute('aria-pressed',String(selected));
        button.textContent = selected ? '保存済み · 解除する' : 'マイチームに保存';
      });
      saved.forEach(slug => {
        const original = valid.get(slug);
        const card = document.createElement('article');
        card.className = 'team-card';
        const heading = document.createElement('h3');
        const link = document.createElement('a');
        link.href = `../universities/${encodeURIComponent(slug)}/`;
        link.textContent = original.dataset.name;
        heading.append(link);
        const results = document.createElement('a');
        results.href = `../results/?region=${encodeURIComponent(original.dataset.region)}`;
        results.textContent = 'この水域の大会成績を見る →';
        const remove = document.createElement('button');
        remove.className = 'reset-button';
        remove.type = 'button';
        remove.textContent = '保存を解除';
        remove.setAttribute('aria-label',`${original.dataset.name}の保存を解除`);
        remove.addEventListener('click',() => toggle(slug));
        card.append(heading,results,remove);
        savedContainer.append(card);
      });
    };
    const toggle = slug => {
      const next = saved.includes(slug) ? saved.filter(s => s !== slug) : [...saved,slug];
      try {
        localStorage.setItem(key,JSON.stringify(next));
        saved = next;
        status.textContent = next.includes(slug) ? `${valid.get(slug).dataset.name}を保存しました。` : `${valid.get(slug).dataset.name}の保存を解除しました。`;
        render();
      } catch { status.textContent = '保存できませんでした。ブラウザーの保存設定をご確認ください。'; }
    };
    buttons.forEach(button => button.addEventListener('click',() => toggle(button.dataset.saveTeam)));
    render();
  }
})();
