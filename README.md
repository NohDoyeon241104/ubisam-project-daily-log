# UBISAM 프로젝트 일일 기록 자산화 (v1)

협력업체 투입 프로젝트의 매일 진행 상황을 표준 양식으로 기록 → 대시보드 → 엑셀로 내보내는 한 묶음.
"주 3회 이상 쓰는 업무를 지식자산화한다"의 실제 예시.

## 빠른 시작 (처음 받는 사람)

1. Clone
```bash
git clone https://github.com/NohDoyeon241104/ubisam-project-daily-log.git
cd ubisam-project-daily-log
```
2. 사용 안내 먼저 열기

일일기록_사용안내.html 을 브라우저로 열어 입력/출력 예시를 확인한다 (4단계 흐름).

3. 둘 중 하나로 사용


Claude / Claude Code — 그날 한 작업을 적고 "일일 기록 정리해줘" 요청 → output/[프로젝트]/[날짜].md 저장
Streamlit 앱 — 아래 실행


```bash
cd scripts
pip install -r requirements.txt
streamlit run app.py
```
4. 본인 정보로 한 줄 수정

CLAUDE.md 의 팀·이름·담당 부분을 본인 것으로 바꾼다. (공유받은 그대로 두면 안 됨)


clone 하면 공통 기능은 함께 받지만, 내가 생성한 일일 기록(output/)과 업로드물(uploads/)은
.gitignore 로 제외되어 내 로컬에만 쌓인다. 남의 기록이 섞이지 않는다.

## 먼저 볼 것
- `일일기록_사용안내.html` — 브라우저로 열면 4단계 입력/출력 예시를 시각적으로 확인 (처음 쓰는 사람용)

## 구성
```
ubisam-project-daily-log_v1/
├── SKILL.md                  # 일일 로그 정리 스킬 (양식 박제본)
├── README.md                 # 이 파일
├── 일일기록_사용안내.html      # 사용 안내 (입력/출력 예시 시각화)
├── CLAUDE.md                 # 1층 회사 지침서 샘플 (라우팅만)
├── projects.json             # 프로젝트 관리 데이터 (log_root 기본 ./output)
├── .gitignore                # output·uploads 내용물 제외
├── templates/
│   └── daily_log_template.md # 출력 양식 (YAML + 본문)
├── workflows/
│   └── workflow_dailylog.md  # CLAUDE.md 라우팅용 2층 파일
├── scripts/
│   ├── app.py                # Streamlit 앱
│   └── requirements.txt
├── examples/
│   └── 2026-06-11_sample.md  # 참고용 예시 로그 (git 포함)
├── output/                   # 일일 로그 생성 위치 (git 제외, .gitkeep만 공유)
│   └── _templates/daily_log_template.md
└── uploads/                  # 업로드 파일 위치 (git 제외)
```

## Git 공유 규칙 (중요)
clone 하면 공통 기능(SKILL·워크플로우·앱·템플릿)은 함께 받지만,
생성된 일일 기록(`output/`)과 업로드 파일(`uploads/`)은 `.gitignore` 로 제외되어 올라가지 않는다.
폴더 구조는 `.gitkeep` 으로 유지되고, 내용물은 각자 로컬에만 쌓인다.

## 사용 경로 A — Claude / Claude Code (앱 없이)
1. `CLAUDE.md` 의 팀·이름·담당 부분을 본인 것으로 수정
2. 그날 한 작업을 문장으로 적고 "일일 기록 정리해줘" 요청
3. 체크리스트 .md 가 `output/[프로젝트]/[날짜].md` 에 저장됨

## 사용 경로 B — Streamlit 앱
```bash
cd scripts
pip install -r requirements.txt
streamlit run app.py
```
1. 기록 루트 = `./output` (기본값, 레포 내부)
2. 프로젝트 관리 탭에서 프로젝트 추가 (기간·상태·색상)
3. 기록 입력 탭에서 날짜(기본 오늘)·담당자·작업 내용 입력
4. "1. 프롬프트 생성" → 복사 → Claude 에 붙여넣기 → output 에 .md 저장
5. 대시보드 탭에서 기간·프로젝트 필터 후 엑셀 내보내기

## 폴더 규칙 (대시보드 파싱 전제)
```
output/
├── _templates/daily_log_template.md
├── LGES_OC5_PtoP/2026-06-11.md
└── SKON_P5_Vision/2026-07-01.md
```
프로젝트명 = 폴더(공백은 _), 날짜(YYYY-MM-DD) = 파일명.

## 상태 값 두 층위 (혼동 주의)
- 프로젝트 전체: 예정 / 진행중 / 완료 → projects.json
- 그날 하루: 정상 / 지연 / 이슈 → 일일 로그 YAML 의 status

## 적용 원리 (회의록 5요소 / 3층 구조)
- 5요소: 반드시 트리거 + 파일경로 읽기 + 번호 단계 + 출력형식 지정 + 금지/분량 → SKILL.md·workflow 에 반영
- 3층: 1층 CLAUDE.md(라우팅) / 2층 workflow(상세) / 3층 MEMORY(개인 취향)
- 휴먼터치: AI 는 초안까지, 최종 검토는 사람
