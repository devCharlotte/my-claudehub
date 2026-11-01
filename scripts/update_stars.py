import json
import os
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN = os.environ.get("GITHUB_TOKEN", "")
KST = timezone(timedelta(hours=9))
BATCH = 40


def gh(url):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "hub-updater",
    })
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def fmt(n):
    if n < 1000:
        return str(n)
    s = f"{n / 1000:.0f}k" if n >= 100000 else f"{n / 1000:.1f}k"
    return s.replace(".0k", "k")


def summary(repo):
    return repo["stargazers_count"], repo["forks_count"], repo["full_name"], repo["html_url"]


def fetch_counts(names, fallback=True):
    names = sorted(set(names))
    counts = {}

    for i in range(0, len(names), BATCH):
        query = "+".join("repo:" + n for n in names[i:i + BATCH])
        try:
            res = gh("https://api.github.com/search/repositories?per_page=100&q=" + query)
            for repo in res.get("items", []):
                counts[repo["full_name"].lower()] = summary(repo)
        except Exception as e:
            print("search failed:", e)
        time.sleep(2.5)

    if fallback:
        for name in names:
            if name.lower() in counts:
                continue
            try:
                counts[name.lower()] = summary(gh(f"https://api.github.com/repos/{name}"))
            except Exception as e:
                print("skip", name, e)

    return counts


def main():
    path = ROOT / "data.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    counts = fetch_counts([r["repo"] for r in data["repos"]])

    for r in data["repos"]:
        found = counts.get(r["repo"].lower())
        if not found:
            continue
        r["stars"], r["forks"], full_name, url = found
        if full_name != r["repo"]:
            print("renamed", r["repo"], "->", full_name)
            if not r.get("parent"):
                r["url"] = url
            r["repo"] = full_name

    data["repos"].sort(key=lambda x: (-x["stars"], x.get("name", x["repo"])))
    data["updated"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M (KST)")

    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "README.md").write_text(readme(data), encoding="utf-8")


def badges(item):
    marks = ""
    if item.get("official"):
        marks += "✅"
    if item.get("insta"):
        marks += "📱"
    if item.get("hot"):
        marks += "🔥"
    if item.get("kdev"):
        marks += "🇰🇷"
    marks = " " + marks if marks else ""
    if item.get("parent"):
        marks += f"<br><sub>📦 {item['parent']}</sub>"
    return marks


def row(item):
    body = f"**{item['desc']}**<br>{item['detail']}"
    if item.get("use"):
        body += f"<br>👉 {item['use']}"
    name = item.get("name", item["repo"])
    return (f"| [{name}]({item['url']}){badges(item)} | `{item['type']}` "
            f"| {fmt(item['stars'])} | {fmt(item['forks'])} | {body.replace('|', '/')} |")


def readme(data):
    cats = data["categories"]
    items = sorted(data["repos"], key=lambda x: -x["stars"])

    lines = [
        "# JH Claude Hub\n",
        "각종 콘텐츠들이 추천하는 스킬, MCP, 플러그인, 툴들을 하나의 사이트에서 볼 수 있도록 모았어요!  ",
        "하는 일 기준으로 나눠 두었고, 검색·필터는 GitHub Pages 페이지(`index.html`)에서 더 편하게 쓸 수 있어요.\n",
        "> 📄 페이지: 이 레포의 GitHub Pages  ",
        f"> 🕒 **자동 갱신:** 매일 오전 8:17 (한국 시간, GitHub Actions) · 마지막 갱신 {data['updated']}  ",
        "> 표시: ✅ 공식(알려진 회사·기관의 GitHub 조직이나 그 회사 CEO가 직접 만든 것 — 그 밖의 개인·미확인 팀은 제외) "
        f"· 📱 인스타에서 소개 · 🔥 요즘 급상승 · 🇰🇷 국내 개발자 제작 · 📦 스킬 묶음 안의 개별 스킬(⭐는 묶음 전체) · 총 {len(items)}개\n",
        "**종류** `MCP` 외부 앱 연결 서버 · `Skill` Claude가 불러 쓰는 작업 지침 · `Plugin` 스킬·명령어·훅 묶음 "
        "· `Tool` 독립 실행 앱/라이브러리 · `List` 큐레이션 · `Guide`/`SDK` 학습·개발용\n",
        "## 카테고리\n",
    ]

    for c in cats:
        n = sum(1 for i in items if c["id"] in i["tags"])
        lines.append(f"- [{c['name']}](#{c['id']}) ({n}) — {c['desc']}")
    lines.append("")

    for c in cats:
        lines.append(f'<a id="{c["id"]}"></a>\n')
        lines.append(f"## {c['name']}\n\n{c['desc']}\n")
        lines.append("| 레포 | 종류 | ⭐ | 🍴 | 무슨 역할? |\n|---|---|---:|---:|---|")
        lines += [row(i) for i in items if c["id"] in i["tags"]]
        lines.append("\n[↑ 카테고리로](#카테고리)\n")

    lines.append("---\n출처: 인스타 게시물, GitHub 트렌딩, GeekNews Show GN, 키워드 검색 등. 꾸준히 추가하고 있어요 — made by JH")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
