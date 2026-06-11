#!/usr/bin/env python3
"""UBISAM 프로젝트 일일 기록 — 입력 폼 + 프롬프트 생성 + 대시보드 + 엑셀 (tkinter)

브라우저·포트 없이 프로그램 창으로 동작. PyInstaller 로 .exe 패키징 가능.
역할:
  1) 프로젝트(projects.json) 선택·CRUD
  2) 날짜·담당자·작업내용 입력 → 프롬프트 생성, 입력 원본은 uploads/ 저장
  3) output/ 에 쌓인 일일 로그(.md) 를 대시보드로 조회 + 엑셀 내보내기
  (실제 .md 작성은 claude 가 SKILL.md 규칙대로 수행)

실행: py scripts/main_ui.py
엑셀 내보내기에는 pandas, openpyxl 필요 (없으면 그 기능만 비활성).
"""
import os
import json
import datetime
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_JSON = os.path.join(ROOT, "projects.json")
OUTPUT_DIR = os.path.join(ROOT, "output")
UPLOADS_DIR = os.path.join(ROOT, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

STATUS_PROJECT = ["예정", "진행중", "완료"]
STATUS_DAILY = ["정상", "지연", "이슈"]
DEFAULT_COLORS = {"예정": "#EF9F27", "진행중": "#639922", "완료": "#888780"}

BRAND = "#4F81BD"
BRAND_DEEP = "#1F497D"


# ---------------------------------------------------------------------------
# 데이터
# ---------------------------------------------------------------------------
def load_config():
    if os.path.exists(PROJECTS_JSON):
        with open(PROJECTS_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {"log_root": "./output", "status_colors": DEFAULT_COLORS, "projects": []}


def save_config(cfg):
    with open(PROJECTS_JSON, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def to_folder_id(name):
    return name.strip().replace(" ", "_")


def timestamp():
    return datetime.datetime.now().strftime("%H%M%S")


def resolve_root(log_root):
    if os.path.isabs(log_root):
        return log_root
    return os.path.normpath(os.path.join(ROOT, log_root))


def parse_log_md(text):
    meta, body = {}, text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2]
    sections, current = {}, None
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("## "):
            current = s[3:].strip()
            sections[current] = []
        elif s.startswith("- ") and current:
            sections[current].append(s[2:].strip())
    meta["_sections"] = sections
    return meta


def scan_logs(cfg):
    rows = []
    root = resolve_root(cfg.get("log_root", "./output"))
    if not os.path.isdir(root):
        return rows
    valid = {p["id"] for p in cfg.get("projects", [])}
    for pid in os.listdir(root):
        pdir = os.path.join(root, pid)
        if not os.path.isdir(pdir) or pid not in valid:
            continue
        for fn in os.listdir(pdir):
            if not fn.endswith(".md"):
                continue
            try:
                with open(os.path.join(pdir, fn), encoding="utf-8") as f:
                    meta = parse_log_md(f.read())
            except Exception:
                continue
            sec = meta.get("_sections", {})
            rows.append({
                "프로젝트": meta.get("project", pid),
                "날짜": meta.get("date", fn[:-3]),
                "작성자": meta.get("author", ""),
                "진행률": meta.get("progress", ""),
                "상태": meta.get("status", ""),
                "오늘 한 일": " / ".join(sec.get("오늘 한 일", [])),
                "이슈": " / ".join(sec.get("이슈 / 블로커", [])),
                "내일 할 일": " / ".join(sec.get("내일 할 일", [])),
            })
    rows.sort(key=lambda r: (r["프로젝트"], r["날짜"]))
    return rows


def build_prompt(log_root, proj_id, the_date, author, status, work_text):
    path = f"{log_root}/{proj_id}/{the_date}.md".replace("\\", "/")
    tpl = f"{log_root}/_templates/daily_log_template.md".replace("\\", "/")
    return (
        f"반드시 {tpl} 를 읽고, 아래 작업 내용을 "
        f"체크리스트로 정리해서 {path} 로 저장해줘.\n\n"
        f"project: {proj_id}\n"
        f"date: {the_date}\n"
        f"author: {author}\n"
        f"status: {status}\n\n"
        f"[작업 내용]\n{work_text.strip()}\n\n"
        f"오늘 한 일 / 이슈·블로커 / 내일 할 일 로 분류하고, "
        f"이모지·볼드체 남발 금지, status 는 정상/지연/이슈 중 하나만 사용."
    )


# ---------------------------------------------------------------------------
# 앱
# ---------------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        root.title("UBISAM 프로젝트 일일 기록 — 입력 폼 & 프롬프트 생성기")
        root.geometry("720x820")

        tk.Label(root, text="UBISAM 프로젝트 일일 기록",
                 font=("맑은 고딕", 14, "bold"), fg=BRAND_DEEP).pack(pady=(10, 2))
        tk.Label(root, text="폼을 채우고 '프롬프트 생성' → 복사해서 claude 에 붙여넣으세요.",
                 font=("맑은 고딕", 9), fg="#555").pack()

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=12, pady=8)
        self.tab_input = tk.Frame(nb)
        self.tab_proj = tk.Frame(nb)
        self.tab_dash = tk.Frame(nb)
        nb.add(self.tab_input, text="기록 입력")
        nb.add(self.tab_proj, text="프로젝트 관리")
        nb.add(self.tab_dash, text="대시보드 / 내보내기")
        nb.bind("<<NotebookTabChanged>>", lambda e: self.refresh_all())

        self._build_input()
        self._build_proj()
        self._build_dash()
        self.refresh_all()

    # ---- 공통 ----
    def project_names(self):
        return [p["name"] for p in self.cfg.get("projects", [])]

    def refresh_all(self):
        names = self.project_names()
        self.proj_combo["values"] = names
        if names and not self.proj_combo.get():
            self.proj_combo.current(0)
            self.on_project_change()
        self.render_proj_list()
        self.render_dashboard()

    # ---- 탭1: 기록 입력 ----
    def _build_input(self):
        f = self.tab_input
        meta = tk.LabelFrame(f, text=" 기록 메타정보 ", font=("맑은 고딕", 10, "bold"),
                             padx=10, pady=8)
        meta.pack(fill="x", padx=10, pady=8)

        r1 = tk.Frame(meta); r1.pack(fill="x", pady=2)
        tk.Label(r1, text="프로젝트", width=10, anchor="w",
                 font=("맑은 고딕", 9)).pack(side="left")
        self.proj_combo = ttk.Combobox(r1, state="readonly", font=("맑은 고딕", 10))
        self.proj_combo.pack(side="left", fill="x", expand=True)
        self.proj_combo.bind("<<ComboboxSelected>>", lambda e: self.on_project_change())

        r2 = tk.Frame(meta); r2.pack(fill="x", pady=2)
        tk.Label(r2, text="날짜", width=10, anchor="w",
                 font=("맑은 고딕", 9)).pack(side="left")
        self.date_entry = tk.Entry(r2, font=("맑은 고딕", 10))
        self.date_entry.insert(0, datetime.date.today().isoformat())
        self.date_entry.pack(side="left", fill="x", expand=True)

        r3 = tk.Frame(meta); r3.pack(fill="x", pady=2)
        tk.Label(r3, text="상태(그날)", width=10, anchor="w",
                 font=("맑은 고딕", 9)).pack(side="left")
        self.daily_status = ttk.Combobox(r3, values=STATUS_DAILY, state="readonly",
                                          font=("맑은 고딕", 10))
        self.daily_status.current(0)
        self.daily_status.pack(side="left", fill="x", expand=True)

        r4 = tk.Frame(meta); r4.pack(fill="x", pady=2)
        tk.Label(r4, text="담당자", width=10, anchor="w",
                 font=("맑은 고딕", 9)).pack(side="left")
        self.author_entry = tk.Entry(r4, font=("맑은 고딕", 10))
        self.author_entry.pack(side="left", fill="x", expand=True)

        memo = tk.LabelFrame(f, text=" 작업한 내용 (자유롭게 적으면 AI가 체크리스트로 정리) ",
                             font=("맑은 고딕", 10, "bold"), padx=10, pady=8)
        memo.pack(fill="both", expand=True, padx=10, pady=6)
        self.memo_box = scrolledtext.ScrolledText(memo, height=8,
                                                  font=("맑은 고딕", 10), wrap="word")
        self.memo_box.pack(fill="both", expand=True)
        mf = tk.Frame(memo); mf.pack(fill="x", pady=(4, 0))
        tk.Button(mf, text="또는 파일에서 불러오기", command=self.load_memo_file,
                  font=("맑은 고딕", 9)).pack(side="left")
        self.memo_file_label = tk.Label(mf, text="", font=("맑은 고딕", 8), fg=BRAND_DEEP)
        self.memo_file_label.pack(side="left", padx=8)

        btns = tk.Frame(f); btns.pack(fill="x", padx=10, pady=4)
        tk.Button(btns, text="① 프롬프트 생성", command=self.generate_prompt,
                  bg=BRAND, fg="white", font=("맑은 고딕", 10, "bold"),
                  height=2).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(btns, text="② 복사", command=self.copy_prompt,
                  bg=BRAND_DEEP, fg="white", font=("맑은 고딕", 10, "bold"),
                  height=2).pack(side="left", fill="x", expand=True, padx=(4, 0))

        of = tk.LabelFrame(f, text=" 생성된 프롬프트 (claude 에 붙여넣기) ",
                           font=("맑은 고딕", 10, "bold"), padx=10, pady=6)
        of.pack(fill="x", padx=10, pady=(2, 4))
        self.out_box = scrolledtext.ScrolledText(of, height=8, font=("Consolas", 9),
                                                 state="disabled", bg="#f7f7f7",
                                                 wrap="word")
        self.out_box.pack(fill="x")

        tk.Button(f, text="uploads 폴더 열기", command=self.open_uploads,
                  font=("맑은 고딕", 9)).pack(pady=(0, 8))

    def on_project_change(self):
        name = self.proj_combo.get()
        proj = next((p for p in self.cfg["projects"] if p["name"] == name), None)
        if proj:
            self.author_entry.delete(0, tk.END)
            self.author_entry.insert(0, ", ".join(proj.get("members", [])))

    def load_memo_file(self):
        p = filedialog.askopenfilename(
            title="작업 내용 파일 선택",
            filetypes=[("텍스트/마크다운", "*.txt *.md"), ("모든 파일", "*.*")])
        if not p:
            return
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            messagebox.showerror("읽기 실패", str(e))
            return
        self.memo_box.delete("1.0", tk.END)
        self.memo_box.insert(tk.END, text)
        self.memo_file_label.config(text=f"불러옴: {os.path.basename(p)}")

    def generate_prompt(self):
        name = self.proj_combo.get()
        proj = next((p for p in self.cfg["projects"] if p["name"] == name), None)
        if not proj:
            messagebox.showwarning("프로젝트 없음", "프로젝트 관리 탭에서 먼저 추가하세요.")
            return
        the_date = self.date_entry.get().strip() or datetime.date.today().isoformat()
        author = self.author_entry.get().strip()
        status = self.daily_status.get()
        work_text = self.memo_box.get("1.0", tk.END).strip()
        if not work_text:
            messagebox.showwarning("내용 없음", "작업한 내용을 적거나 파일을 불러오세요.")
            return

        # 입력 원본을 uploads 에 저장 (시각까지 붙여 안 덮어쓰기)
        fn = f"{proj['id']}_{the_date}_{timestamp()}_input.txt"
        with open(os.path.join(UPLOADS_DIR, fn), "w", encoding="utf-8") as f:
            f.write(work_text + "\n")

        prompt = build_prompt(self.cfg.get("log_root", "./output"),
                              proj["id"], the_date, author, status, work_text)
        self.out_box.config(state="normal")
        self.out_box.delete("1.0", tk.END)
        self.out_box.insert(tk.END, prompt)
        self.out_box.config(state="disabled")
        self.memo_file_label.config(text=f"입력 원본 저장됨: uploads/{fn}")

    def copy_prompt(self):
        text = self.out_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("안내", "먼저 '프롬프트 생성'을 누르세요.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("복사됨", "프롬프트가 복사되었습니다.\nclaude 창에 붙여넣으세요.")

    def open_uploads(self):
        if os.name == "nt":
            os.startfile(UPLOADS_DIR)
        elif os.uname().sysname == "Darwin":
            os.system(f'open "{UPLOADS_DIR}"')
        else:
            os.system(f'xdg-open "{UPLOADS_DIR}"')

    # ---- 탭2: 프로젝트 관리 (CRUD) ----
    def _build_proj(self):
        f = self.tab_proj
        top = tk.LabelFrame(f, text=" 프로젝트 목록 ", font=("맑은 고딕", 10, "bold"),
                            padx=10, pady=8)
        top.pack(fill="both", expand=True, padx=10, pady=8)
        cols = ("name", "period", "status", "members")
        self.proj_tree = ttk.Treeview(top, columns=cols, show="headings", height=8)
        for c, t, w in [("name", "프로젝트", 180), ("period", "기간", 180),
                        ("status", "상태", 70), ("members", "담당자", 160)]:
            self.proj_tree.heading(c, text=t)
            self.proj_tree.column(c, width=w)
        self.proj_tree.pack(fill="both", expand=True)
        self.proj_tree.bind("<<TreeviewSelect>>", lambda e: self.load_proj_form())

        form = tk.LabelFrame(f, text=" 추가 / 편집 ", font=("맑은 고딕", 10, "bold"),
                             padx=10, pady=8)
        form.pack(fill="x", padx=10, pady=(0, 8))
        self.pf_name = self._frow(form, "프로젝트명")
        self.pf_start = self._frow(form, "시작일")
        self.pf_end = self._frow(form, "종료일(미정 가능)")
        sr = tk.Frame(form); sr.pack(fill="x", pady=2)
        tk.Label(sr, text="상태", width=14, anchor="w",
                 font=("맑은 고딕", 9)).pack(side="left")
        self.pf_status = ttk.Combobox(sr, values=STATUS_PROJECT, state="readonly",
                                      font=("맑은 고딕", 10))
        self.pf_status.current(1)
        self.pf_status.pack(side="left", fill="x", expand=True)
        self.pf_members = self._frow(form, "담당자( , 구분)")

        b = tk.Frame(form); b.pack(fill="x", pady=(6, 0))
        tk.Button(b, text="저장(추가/수정)", command=self.save_proj,
                  bg=BRAND, fg="white", font=("맑은 고딕", 9, "bold")).pack(side="left",
                  fill="x", expand=True, padx=(0, 4))
        tk.Button(b, text="삭제", command=self.delete_proj,
                  fg="#b00", font=("맑은 고딕", 9, "bold")).pack(side="left",
                  fill="x", expand=True, padx=(4, 4))
        tk.Button(b, text="폼 비우기", command=self.clear_proj_form,
                  font=("맑은 고딕", 9)).pack(side="left", fill="x", expand=True, padx=(4, 0))

    def _frow(self, parent, label):
        fr = tk.Frame(parent); fr.pack(fill="x", pady=2)
        tk.Label(fr, text=label, width=14, anchor="w",
                 font=("맑은 고딕", 9)).pack(side="left")
        e = tk.Entry(fr, font=("맑은 고딕", 10))
        e.pack(side="left", fill="x", expand=True)
        return e

    def render_proj_list(self):
        if not hasattr(self, "proj_tree"):
            return
        for i in self.proj_tree.get_children():
            self.proj_tree.delete(i)
        for p in self.cfg.get("projects", []):
            period = f"{p.get('start','')} ~ {p.get('end','') or '미정'}"
            self.proj_tree.insert("", "end", iid=p["id"],
                                  values=(p["name"], period, p["status"],
                                          ", ".join(p.get("members", []))))

    def load_proj_form(self):
        sel = self.proj_tree.selection()
        if not sel:
            return
        p = next((x for x in self.cfg["projects"] if x["id"] == sel[0]), None)
        if not p:
            return
        self.clear_proj_form()
        self.pf_name.insert(0, p["name"])
        self.pf_start.insert(0, p.get("start", ""))
        self.pf_end.insert(0, p.get("end", ""))
        self.pf_status.set(p.get("status", "진행중"))
        self.pf_members.insert(0, ", ".join(p.get("members", [])))

    def clear_proj_form(self):
        for e in (self.pf_name, self.pf_start, self.pf_end, self.pf_members):
            e.delete(0, tk.END)
        self.pf_status.current(1)

    def save_proj(self):
        name = self.pf_name.get().strip()
        if not name:
            messagebox.showwarning("입력 필요", "프로젝트명을 입력하세요.")
            return
        pid = to_folder_id(name)
        new = {
            "id": pid, "name": name,
            "start": self.pf_start.get().strip(),
            "end": self.pf_end.get().strip(),
            "status": self.pf_status.get(),
            "members": [m.strip() for m in self.pf_members.get().split(",") if m.strip()],
        }
        existing = next((p for p in self.cfg["projects"] if p["id"] == pid), None)
        if existing:
            existing.update(new)
        else:
            self.cfg["projects"].append(new)
        save_config(self.cfg)
        self.render_proj_list()
        self.proj_combo["values"] = self.project_names()
        messagebox.showinfo("저장됨", f"'{name}' 저장됨 (폴더 ID: {pid})")

    def delete_proj(self):
        sel = self.proj_tree.selection()
        if not sel:
            messagebox.showinfo("안내", "목록에서 삭제할 프로젝트를 선택하세요.")
            return
        if not messagebox.askyesno("삭제 확인", "선택한 프로젝트를 삭제할까요?"):
            return
        self.cfg["projects"] = [p for p in self.cfg["projects"] if p["id"] != sel[0]]
        save_config(self.cfg)
        self.render_proj_list()
        self.proj_combo["values"] = self.project_names()
        self.clear_proj_form()

    # ---- 탭3: 대시보드 + 엑셀 ----
    def _build_dash(self):
        f = self.tab_dash
        bar = tk.Frame(f); bar.pack(fill="x", padx=10, pady=8)
        tk.Label(bar, text="기간 필터", font=("맑은 고딕", 9)).pack(side="left")
        self.d_from = tk.Entry(bar, width=12, font=("맑은 고딕", 9))
        self.d_from.pack(side="left", padx=4)
        tk.Label(bar, text="~", font=("맑은 고딕", 9)).pack(side="left")
        self.d_to = tk.Entry(bar, width=12, font=("맑은 고딕", 9))
        self.d_to.pack(side="left", padx=4)
        tk.Button(bar, text="조회", command=self.render_dashboard,
                  font=("맑은 고딕", 9)).pack(side="left", padx=6)
        tk.Button(bar, text="엑셀로 내보내기", command=self.export_excel,
                  bg=BRAND, fg="white", font=("맑은 고딕", 9, "bold")).pack(side="right")

        wrap = tk.LabelFrame(f, text=" 기록 목록 ", font=("맑은 고딕", 10, "bold"),
                             padx=8, pady=6)
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        cols = ("프로젝트", "날짜", "진행률", "상태", "오늘 한 일", "이슈", "내일 할 일")
        self.dash_tree = ttk.Treeview(wrap, columns=cols, show="headings")
        widths = {"프로젝트": 120, "날짜": 90, "진행률": 55, "상태": 55,
                  "오늘 한 일": 180, "이슈": 150, "내일 할 일": 150}
        for c in cols:
            self.dash_tree.heading(c, text=c)
            self.dash_tree.column(c, width=widths[c])
        self.dash_tree.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.dash_tree.yview)
        sb.pack(side="right", fill="y")
        self.dash_tree.configure(yscrollcommand=sb.set)

    def _filtered_rows(self):
        rows = scan_logs(self.cfg)
        dfrom = self.d_from.get().strip()
        dto = self.d_to.get().strip()
        if dfrom:
            rows = [r for r in rows if r["날짜"] >= dfrom]
        if dto:
            rows = [r for r in rows if r["날짜"] <= dto]
        return rows

    def render_dashboard(self):
        if not hasattr(self, "dash_tree"):
            return
        for i in self.dash_tree.get_children():
            self.dash_tree.delete(i)
        for r in self._filtered_rows():
            self.dash_tree.insert("", "end", values=(
                r["프로젝트"], r["날짜"], r["진행률"], r["상태"],
                r["오늘 한 일"], r["이슈"], r["내일 할 일"]))

    def export_excel(self):
        rows = self._filtered_rows()
        if not rows:
            messagebox.showinfo("안내", "내보낼 기록이 없습니다.")
            return
        try:
            import pandas as pd
            import openpyxl  # 엔진 확인용 (미설치 시 여기서 잡힘)
        except Exception as e:
            messagebox.showerror(
                "라이브러리 로드 실패",
                "pandas/openpyxl 로드 중 오류가 발생했습니다.\n\n"
                f"{type(e).__name__}: {e}\n\n"
                "설치: py -m pip install pandas openpyxl")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=f"project_logs_{datetime.date.today().isoformat()}.xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        try:
            pd.DataFrame(rows).to_excel(path, index=False, sheet_name="ProjectLogs",
                                        engine="openpyxl")
        except Exception as e:
            messagebox.showerror("내보내기 실패", f"{type(e).__name__}: {e}")
            return
        messagebox.showinfo("완료", f"엑셀 저장됨:\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()