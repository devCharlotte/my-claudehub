import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "curation"), str(ROOT / "scripts")]

from sources import SOURCES
from update_stars import fetch_counts, fmt

TOP_PER_SECTION = 8
GITHUB_LINK = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
SKIP_OWNERS = {"sponsors", "orgs", "topics", "features", "marketplace", "settings", "apps", "user-attachments"}


def fetch_readme(repo):
    for branch in ("HEAD", "main", "master"):
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/README.md"
        try:
            with urllib.request.urlopen(url, timeout=30) as res:
                return res.read().decode("utf-8", "replace")
        except Exception:
            pass
    return ""


def parse_links(text, self_repo):
    section, found, seen = None, [], set()

    for line in text.splitlines():
        heading = re.match(r"^(#{2,3})\s+(.*)", line)
        if heading:
            section = MD_LINK.sub(r"\1", re.sub(r"<[^>]+>", "", heading.group(2))).strip()
            continue
        if not section or not re.match(r"^\s*([-*|]|\d+\.)", line):
            continue

        m = GITHUB_LINK.search(line)
        if not m or m.group(1).lower() in SKIP_OWNERS:
            continue

        name = m.group(1) + "/" + re.sub(r"\.git$", "", m.group(2)).rstrip(".")
        key = name.lower()
        if key == self_repo.lower() or key in seen:
            continue
        seen.add(key)

        desc = MD_LINK.sub(r"\1", line[m.end():])
        desc = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)", "", desc).strip(" )|-–")
        found.append({"repo": name, "section": section, "desc": desc[:160], "official": "🎖" in line})

    return found


def parse_skills(text):
    section, found = None, []

    for line in text.splitlines():
        heading = re.match(r"^### (.*)", line)
        if heading:
            section = heading.group(1).strip()
            continue
        if not section or not line.startswith("| ["):
            continue

        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        found.append({
            "skill": cells[1].strip("` "),
            "section": section,
            "title": re.sub(r"\[(.*?)\].*", r"\1", cells[0]),
            "desc": cells[2],
        })

    return found


def skill_lines(text, have_skills):
    new = [s for s in parse_skills(text) if s["skill"] not in have_skills]
    lines = [f"새 스킬 {len(new)}개\n"]
    lines += [f"- `{s['skill']}` ({s['section']}) — {s['title']}: {s['desc']}" for s in new]
    return lines


def link_lines(text, repo, have):
    cands = [c for c in parse_links(text, repo) if c["repo"].lower() not in have]
    counts = fetch_counts([c["repo"] for c in cands], fallback=False)

    by_section = {}
    for c in cands:
        found = counts.get(c["repo"].lower())
        if found:
            by_section.setdefault(c["section"], []).append((found[0], found[1], c))

    lines = []
    for section, rows in by_section.items():
        rows.sort(key=lambda x: -x[0])
        lines.append(f"\n### {section}\n")
        for stars, forks, c in rows[:TOP_PER_SECTION]:
            official = " ✅공식" if c["official"] else ""
            lines.append(f"- [{c['repo']}](https://github.com/{c['repo']}) ⭐{fmt(stars)} 🍴{fmt(forks)}{official} — {c['desc']}")
    return lines


def main():
    data = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
    have = {r["repo"].lower() for r in data["repos"]}
    have_skills = {r.get("name", "").split(" › ")[-1] for r in data["repos"] if r.get("parent")}

    lines = [
        "# 후보 목록 (자동 생성 · 비공개 메모용)\n",
        "허브에 아직 없는 레포를 모음집의 원래 분류별로, 스타순 상위만 정리했어요.\n",
    ]

    for src in SOURCES:
        text = fetch_readme(src["repo"])
        if not text:
            lines.append(f"\n## {src['repo']}\n\n(README를 못 읽었어요)\n")
            continue

        lines.append(f"\n## {src['repo']} — {src['note']}\n")
        if src["kind"] == "skills":
            lines += skill_lines(text, have_skills)
        else:
            lines += link_lines(text, src["repo"], have)

    (ROOT / "curation" / "candidates.md").write_text("\n".join(lines), encoding="utf-8")
    print("wrote curation/candidates.md")


if __name__ == "__main__":
    main()
