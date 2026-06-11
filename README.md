# UBISAM 프로젝트 일일 기록 자산화 (v1)

협력업체 투입 프로젝트의 매일 진행 상황을 표준 양식으로 기록 → 대시보드 → 엑셀로 내보내는 한 묶음.
"주 3회 이상 쓰는 업무를 지식자산화한다"의 실제 예시.

## 빠른 시작 (처음 받는 사람)

### 1. Clone
```bash
git clone https://github.com/NohDoyeon241104/ubisam-project-daily-log.git
cd ubisam-project-daily-log
```

### 2. 사용 안내 먼저 열기
`일일기록_사용안내.html` 을 브라우저로 열어 입력/출력 예시를 확인한다 (4단계 흐름).

### 3. 둘 중 하나로 사용
- **Claude / Claude Code** — 그날 한 작업을 적고 "일일 기록 정리해줘" 요청 → `output/[프로젝트]/[날짜].md` 저장
- **Streamlit 앱** (대시보드·엑셀까지 쓸 때만 필요) — 아래 "Python 사전준비" 먼저 확인
```bash
cd scripts
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

> **앱 없이도 동작한다.** 일일 기록 자체는 Claude / Claude Code 만으로 충분하다.
> Python 설치는 대시보드 조회·엑셀 내보내기를 쓸 사람만 하면 된다.

#### Python 사전준비 (앱 쓰는 경우)

**상황 A — Python 자체가 없음 (완전 처음)**
1. https://www.python.org/downloads/ 에서 설치 (Windows)
2. 설치 첫 화면에서 **"Add python.exe to PATH" 체크** (이걸 빠뜨리면 명령을 못 찾는다)
3. 설치 후 터미널(PowerShell)을 새로 연다 (기존 창은 PATH 인식 안 됨)
4. 확인: `py --version` 또는 `python --version` 으로 버전이 나오면 OK

**상황 B — `py` 는 되는데 패키지가 없음 (`No module named streamlit`)**
- Python 은 깔려 있으니 패키지만 설치하면 된다.
```bash
py -m pip install streamlit pandas openpyxl
```

**명령어 주의 (Windows)**
- `python` 이 "인식되지 않습니다" 로 뜨면 `py` 를 대신 쓴다. 이 레포 예시는 `py` 기준이다.
- 설치·실행 모두 `py -m ...` 형태가 가장 안전하다 (`py -m pip ...`, `py -m streamlit run ...`)
- 실행되면 터미널에 `Local URL: http://localhost:8501` 이 뜨고 브라우저가 열린다. 안 열리면 그 주소를 직접 붙여넣는다.

### 4. 본인 정보로 한 줄 수정
`CLAUDE.md` 의 팀·이름·담당 부분을 본인 것으로 바꾼다. (공유받은 그대로 두면 안 됨)

> clone 하면 공통 기능은 함께 받지만, 내가 생성한 일일 기록(`output/`)과 업로드물(`uploads/`)은
> `.gitignore` 로 제외되어 내 로컬에만 쌓인다. 남의 기록이 섞이지 않는다.

---

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
│   ├── main_ui.py            # tkinter 데스크톱 앱 (exe 가능)
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
> Python 미설치/패키지 없음 상황은 상단 "Python 사전준비" 참고. 명령은 `py` 기준(Windows).
```bash
cd scripts
py -m pip install -r requirements.txt
py -m streamlit run app.py
```
1. 기록 루트 = `./output` (기본값, 레포 내부)
2. 프로젝트 관리 탭에서 프로젝트 추가 (기간·상태·색상)
3. 기록 입력 탭에서 날짜(기본 오늘)·담당자·작업 내용 입력
4. "1. 프롬프트 생성" → 복사 → Claude 에 붙여넣기 → output 에 .md 저장
5. 대시보드 탭에서 기간·프로젝트 필터 후 엑셀 내보내기

## 사용 경로 C — 데스크톱 앱 (tkinter, 브라우저 없이)
> 포트·브라우저 없이 프로그램 창으로 뜬다. tkinter 는 파이썬 표준 라이브러리라 별도 설치 불필요.
> 엑셀 내보내기만 pandas·openpyxl 이 필요하다(없으면 그 기능만 비활성).
```bash
cd scripts
py main_ui.py
```
- 기능은 Streamlit 버전(app.py)과 동일: 프로젝트 CRUD, 기록 입력, 프롬프트 생성, 입력 원본 uploads 저장, 대시보드, 엑셀 내보내기
- Streamlit 버전과 tkinter 버전 중 편한 쪽을 쓰면 된다 (둘 다 같은 projects.json·output 사용)

### exe 로 묶기 (배포용, 선택)
받는 사람이 파이썬 없이 더블클릭으로 쓰게 하려면 PyInstaller 로 단일 exe 를 만든다.
```bash
py -m pip install pyinstaller
cd scripts
py -m PyInstaller --onefile --windowed --name UbisamDailyLog main_ui.py
```
- 결과물: `scripts/dist/UbisamDailyLog.exe`
- exe 는 자기 위치 기준으로 `projects.json`·`output`·`uploads` 를 찾으므로, exe 를 레포 루트(또는 scripts 상위 구조 유지)에 두고 실행하는 것을 권장
- `dist/`, `build/`, `*.spec` 은 빌드 산출물이라 git 에 올리지 않는다(.gitignore 에 추가 권장)

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
