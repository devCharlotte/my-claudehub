const GROUPS = [
  { id: "g-claude", name: "Claude 활용", cats: ["official", "dev", "agents", "models", "memory", "prompt"] },
  { id: "g-connect", name: "연결·자동화", cats: ["mcp", "search", "browser", "automation", "messaging"] },
  { id: "g-work", name: "업무·콘텐츠", cats: ["office", "sheets", "data", "writing", "design", "video", "marketing", "godsaeng", "career"] },
  { id: "g-public", name: "공공·법률·금융", cats: ["gov", "legal", "finance", "korea"] },
  { id: "g-life", name: "생활·분야", cats: ["life", "science", "game", "learn"] },
  { id: "g-infra", name: "개발 인프라", cats: ["cloud", "security", "devtools"] },
];
const PAGE_SIZE = 40;

const state = { cat: "all", group: -1, q: "", type: "", src: "", sort: "stars" };
let data = null;
let cats = {};
let shown = PAGE_SIZE;

const $ = (id) => document.getElementById(id);

const ESC = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" };
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ESC[c]);

const fmt = (n) => (n >= 1000 ? (n / 1000).toFixed(n >= 100000 ? 0 : 1).replace(/\.0$/, "") + "k" : String(n));
const catName = (id) => (cats[id] ? cats[id].name : id);
const catCount = (id) => data.repos.filter((r) => r.tags.includes(id)).length;
const groupCats = (g) => g.cats.filter((id) => cats[id]);
const inGroup = (r, g) => r.tags.some((t) => g.cats.includes(t));

function groupCount(g) {
  return new Set(data.repos.filter((r) => inGroup(r, g)).map((r) => r.url)).size;
}

function renderTabs() {
  const all = `<button class="tab" role="tab" type="button" data-cat="all">전체<small>${data.repos.length}</small></button>`;
  const groups = GROUPS.map(
    (g) => `<button class="tab" role="tab" type="button" data-cat="${g.id}">${g.name}<small>${groupCount(g)}</small></button>`
  );
  $("tabs").innerHTML = all + groups.join("");
}

function chip(id) {
  return `<button class="chip" type="button" data-cat="${id}" aria-current="${id === state.cat}">${esc(catName(id))}<span class="n">${catCount(id)}</span></button>`;
}

function renderCats() {
  const box = $("cats");

  if (state.group < 0) {
    box.classList.add("home");
    box.innerHTML = GROUPS.map(
      (g) => `<div class="crow"><h3>${g.name}</h3><div class="cl">${groupCats(g).map(chip).join("")}</div></div>`
    ).join("");
  } else {
    const g = GROUPS[state.group];
    box.classList.remove("home");
    box.innerHTML =
      `<div class="crow"><div class="cl">` +
      `<button class="chip" type="button" data-cat="${g.id}" aria-current="${state.cat === "all"}">${g.name} 전체<span class="n">${groupCount(g)}</span></button>` +
      groupCats(g).map(chip).join("") +
      `</div></div>`;
  }

  const tabs = $("tabs");
  for (const tab of tabs.querySelectorAll(".tab")) {
    const idx = GROUPS.findIndex((g) => g.id === tab.dataset.cat);
    const on = idx === state.group || (tab.dataset.cat === "all" && state.group < 0);
    tab.setAttribute("aria-selected", String(on));
    if (on) tabs.scrollLeft = Math.max(0, tab.offsetLeft - tabs.clientWidth / 2 + tab.clientWidth / 2);
  }
}

function renderStats() {
  const official = data.repos.filter((r) => r.official).length;
  const updated = data.updated || "";
  $("meta").textContent = `${data.repos.length}개 · 공식 ${official}개 · 카테고리 ${data.categories.length}개 · 마지막 갱신 ${updated}`;
  $("upd").textContent = `스타·포크는 매일 아침 8:17에 자동으로 갱신돼요. 마지막 갱신: ${updated}`;
}

function matches(r, q, group) {
  if (state.cat !== "all" ? !r.tags.includes(state.cat) : group && !inGroup(r, group)) return false;
  if (state.type && r.type !== state.type) return false;
  if (state.src && !r[state.src]) return false;
  if (!q) return true;
  const text = [r.repo, r.name, r.desc, r.detail, r.use, r.sub, r.tags.map(catName).join(" ")].join(" ");
  return text.toLowerCase().includes(q);
}

function filtered() {
  const q = state.q.trim().toLowerCase();
  const group = state.group >= 0 ? GROUPS[state.group] : null;
  const list = data.repos.filter((r) => matches(r, q, group));

  const name = (r) => (r.name || r.repo).toLowerCase();
  const byName = (a, b) => name(a).localeCompare(name(b));
  list.sort(state.sort === "name" ? byName : (a, b) => b[state.sort] - a[state.sort] || byName(a, b));
  return list;
}

function notes(r) {
  const out = [];
  if (r.official) out.push(`<span class="off">공식${r.officialNote ? " (" + esc(r.officialNote) + ")" : ""}</span>`);
  if (r.hot) out.push(`<span class="hot">요즘 인기</span>`);
  if (r.insta) out.push(`<span>인스타 추천</span>`);
  if (r.kdev) out.push(`<span>국내 제작</span>`);
  if (r.parent) out.push(`<span>k-skill 묶음 · ${esc(r.sub || "")}</span>`);
  out.push(r.tags.map((t) => `<button type="button" data-cat="${t}">#${esc(catName(t))}</button>`).join(" "));
  return out.join("");
}

function card(r) {
  const [owner, name] = r.name ? r.name.split(" › ") : r.repo.split("/");
  const sep = r.name ? " › " : "/";
  const link = `href="${esc(r.url)}" target="_blank" rel="noopener"`;

  return `<li class="item">
  <div class="it-main">
    <div class="it-name"><a ${link}><span class="o">${esc(owner)}${sep}</span>${esc(name)}</a><span class="kind">${esc(r.type)}</span></div>
    <p class="it-desc">${esc(r.desc)}</p>
    ${r.detail ? `<p class="it-detail">${esc(r.detail)}</p>` : ""}
    ${r.use ? `<p class="it-use">${esc(r.use)}</p>` : ""}
    ${r.install ? `<div class="cmd"><code>${esc(r.install)}</code><button type="button" data-copy="${esc(r.install)}">복사</button></div>` : ""}
    <div class="notes">${notes(r)}</div>
  </div>
  <div class="it-side"><span>★ <b>${fmt(r.stars)}</b></span><span>⑂ ${fmt(r.forks)}</span>${r.parent ? "<small>묶음 전체 기준</small>" : ""}<a ${link}>GitHub ↗</a></div>
</li>`;
}

function renderHeading() {
  const cat = cats[state.cat];
  const group = state.group >= 0 ? GROUPS[state.group] : null;

  if (cat) {
    $("ctitle").textContent = cat.name;
    $("cdesc").textContent = cat.desc;
  } else if (group) {
    $("ctitle").textContent = group.name;
    $("cdesc").textContent = groupCats(group).map(catName).join(" · ");
  } else {
    $("ctitle").textContent = "전체";
    $("cdesc").textContent = "스타가 많은 순서예요. 위에서 분야를 골라 좁혀 보세요.";
  }
}

function render() {
  renderCats();
  renderHeading();

  const list = filtered();
  $("count").textContent = `${list.length}개`;
  $("grid").innerHTML = list.length
    ? list.slice(0, shown).map(card).join("")
    : `<li class="empty">찾는 항목이 없어요. 검색어나 필터를 바꿔 보세요.</li>`;

  const left = list.length - shown;
  $("more").hidden = left <= 0;
  if (left > 0) $("moreBtn").textContent = `더 보기 (${left}개 남았어요)`;
}

function go(key) {
  const idx = GROUPS.findIndex((g) => g.id === key);
  if (idx >= 0) {
    state.group = idx;
    state.cat = "all";
  } else if (cats[key]) {
    state.cat = key;
    state.group = GROUPS.findIndex((g) => g.cats.includes(key));
  } else {
    state.cat = "all";
    state.group = -1;
  }
  shown = PAGE_SIZE;
  render();
}

function fromHash() {
  go(decodeURIComponent(location.hash.slice(1)));
}

function copy(btn) {
  const text = btn.dataset.copy;
  const selectFallback = () => {
    const range = document.createRange();
    range.selectNodeContents(btn.previousElementSibling);
    const sel = getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  };
  navigator.clipboard
    ?.writeText(text)
    .then(() => {
      btn.textContent = "복사됨";
      setTimeout(() => (btn.textContent = "복사"), 1500);
    })
    .catch(selectFallback);
}

function bindEvents() {
  document.addEventListener("click", (e) => {
    const catBtn = e.target.closest("[data-cat]");
    if (catBtn) {
      const id = catBtn.dataset.cat;
      if (id === "all") {
        history.replaceState(null, "", location.pathname + location.search);
        go("all");
      } else {
        location.hash = id;
      }
      if (catBtn.closest(".notes")) window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    const copyBtn = e.target.closest("[data-copy]");
    if (copyBtn) copy(copyBtn);
  });

  $("moreBtn").onclick = () => {
    shown += PAGE_SIZE;
    render();
  };
  $("q").oninput = (e) => {
    state.q = e.target.value;
    shown = PAGE_SIZE;
    render();
  };
  for (const id of ["type", "src", "sort"]) {
    $(id).onchange = (e) => {
      state[id] = e.target.value;
      shown = PAGE_SIZE;
      render();
    };
  }
  addEventListener("hashchange", fromHash);
}

async function init() {
  $("count").textContent = "불러오는 중…";
  try {
    const res = await fetch("data.json", { cache: "no-cache" });
    data = await res.json();
  } catch (e) {
    $("count").textContent = "";
    $("grid").innerHTML = `<li class="empty">목록을 불러오지 못했어요. 잠시 후 새로고침해 보세요.</li>`;
    return;
  }
  cats = Object.fromEntries(data.categories.map((c) => [c.id, c]));
  renderTabs();
  renderStats();
  bindEvents();
  fromHash();
}

init();
