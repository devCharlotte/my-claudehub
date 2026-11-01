# curation — 비공개 메모 보관함

허브 페이지(`index.html`)와 첫 화면 README에는 **나오지 않는** 자료를 한곳에 모아 둔 폴더예요.
나중에 허브를 업데이트하거나 추가 조사를 할 때 여기서 시작하면 됩니다.

> ⚠️ 레포가 공개(Public)면 이 폴더 파일도 누구나 열어볼 수 있어요. 페이지·README 화면에만 안 나올 뿐이에요.
> 완전히 숨기려면 이 폴더를 별도 비공개 레포로 옮기세요.

## 들어 있는 것

| 파일 | 내용 | 언제 보나 |
|---|---|---|
| `sources.py` | 큐레이션(모음집) 소스 목록. `kind`가 `links`면 README 속 깃허브 링크를 섹션별로, `skills`면 k-skill처럼 한 레포 안의 스킬 표를 읽어요 | 새 레포 후보를 찾을 때 |
| `collections.json` | 공개 화면에서 숨긴 모음집 레포들의 설명, 그리고 각 모음집에서 **이미 가져온 항목** 기록 | 어디서 뭘 가져왔는지 확인할 때 |
| `sites.json` | 더 찾아볼 사이트 — 커뮤니티(GeekNews, GPTers, Reddit 등), MCP·스킬 디렉터리(Smithery, MCP.so, skills.sh 등) | 가끔 직접 둘러볼 때 |
| `instagram_accounts.json` | 레포·스킬을 자주 소개하는 인스타 계정 (예: @aiscene.kr) | 인스타에서 새 소식을 찾을 때 |
| `candidates.md` | 아래 '후보 수집'을 실행하면 생기는 결과 | 실행 후 |

## 후보 수집 (아직 허브에 없는 레포 찾기)

1. 깃허브 레포 → **Actions** 탭 → **Collect candidates (manual)** → **Run workflow**
2. 몇 분 뒤 `curation/candidates.md`가 커밋돼요. 모음집의 원래 분류별로 스타순 상위 8개씩 정리돼 있어요.
3. 마음에 드는 레포를 `data.json`의 `repos`에 추가하면 다음 날 오전 8:17 갱신 때 스타·포크가 채워져요.

로컬에서 직접 돌리려면: `GITHUB_TOKEN=내토큰 python scripts/collect_candidates.py`

## data.json 항목 형식 (추가할 때 참고)

```jsonc
{
  "repo": "소유자/레포",
  "url": "https://github.com/소유자/레포",
  "stars": 0, "forks": 0,
  "type": "MCP | Skill | Plugin | Tool | List | Guide | SDK",
  "tags": ["카테고리 id", "..."],
  "desc": "한 줄 역할",
  "detail": "조금 자세한 설명",
  "use": "이럴 때 (없으면 null)",
  "official": true,   // 알려진 회사·기관의 GitHub 조직이나 그 회사 CEO 개인 계정이 직접 만든 경우만 (예: koreainvestment=한국투자증권, kepano=옵시디언 CEO). 이름에 "official"만 붙은 건 X. CEO 계정이면 "officialNote": "○○ CEO" 도 적기
  "insta": true,      // 인스타에서 소개됐으면
  "kdev": true        // 국내 개발자가 만들었으면
}
```

카테고리 id 목록은 `data.json`의 `categories`에 있어요.

## 로컬에서 페이지 미리보기

`index.html`은 `data.json`을 불러와서 그려요. 파일을 바로 열면 안 뜨니까 레포 폴더에서 `python -m http.server` 실행 후 `http://localhost:8000`으로 열어 보세요.
