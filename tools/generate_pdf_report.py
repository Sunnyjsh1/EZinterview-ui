"""
PDF 파싱 테스트 결과 리포트 생성기
fpdf2 사용 — 한글 지원 (Malgun Gothic)
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = Path(__file__).parent / "results"
PROMPT_FILE = Path(__file__).parent / "prompts" / "init_pdf_parser.txt"

# 한글 폰트 경로
FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
FONT_BOLD_PATH = "C:/Windows/Fonts/malgunbd.ttf"


class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("malgun", "", FONT_PATH)
        self.add_font("malgun", "B", FONT_BOLD_PATH)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("malgun", "B", 10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, "PDF 파싱 프롬프트 테스트 리포트", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("malgun", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("malgun", "B", 14)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def sub_title(self, title):
        self.set_font("malgun", "B", 11)
        self.set_text_color(67, 56, 202)  # indigo
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("malgun", "", 9)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def badge(self, text, color):
        r, g, b = color
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("malgun", "B", 8)
        w = self.get_string_width(text) + 6
        self.cell(w, 6, text, fill=True, new_x="END")
        self.set_text_color(50, 50, 50)

    def add_result_badge(self, status):
        if status == "PASS":
            self.badge(" PASS ", (34, 197, 94))
        else:
            self.badge(" FAIL ", (239, 68, 68))


def find_latest_result():
    files = sorted(RESULTS_DIR.glob("result_pdf_parser_*.json"), reverse=True)
    if not files:
        raise FileNotFoundError("결과 파일이 없습니다. 먼저 test_pdf_parser.py를 실행하세요.")
    return files[0]


def generate_report(result_file: Path):
    with open(result_file, encoding="utf-8") as f:
        results = json.load(f)

    prompt_text = PROMPT_FILE.read_text(encoding="utf-8")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    pdf = ReportPDF()
    pdf.alias_nb_pages()

    # ── Page 1: 커버 + 요약 ──
    pdf.add_page()
    pdf.ln(20)
    pdf.set_font("malgun", "B", 24)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 14, "PDF 파싱 프롬프트", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 14, "테스트 리포트", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("malgun", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 7, f"생성일: {now}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "모델: gemini-flash-latest  |  Temperature: 0", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(16)

    # 요약 테이블
    pdf.section_title("1. 테스트 결과 요약")

    sample_labels = {
        "sample1_health_beverage": ("Sample 1", "건강음료 신제품 컨셉", "쉬움 — 정형화된 번호+태그"),
        "sample2_ott_service": ("Sample 2", "OTT 서비스 이용행태", "중간 — 표(Table) 형식"),
        "sample3_car_brand": ("Sample 3", "자동차 브랜드 이미지", "어려움 — 문단형 자유 텍스트"),
    }

    # Table header
    pdf.set_font("malgun", "B", 9)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(25, 7, "샘플", border=1, fill=True, align="C")
    pdf.cell(55, 7, "주제", border=1, fill=True, align="C")
    pdf.cell(55, 7, "난이도", border=1, fill=True, align="C")
    pdf.cell(25, 7, "질문 수", border=1, fill=True, align="C")
    pdf.cell(20, 7, "결과", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("malgun", "", 9)
    pdf.set_text_color(50, 50, 50)
    for r in results:
        label, topic, diff = sample_labels.get(r["sample"], (r["sample"], "", ""))
        count_str = f"{r['parsed_count']}/{r['expected_count']}"
        status_str = r["status"]

        pdf.cell(25, 7, label, border=1, align="C")
        pdf.cell(55, 7, topic, border=1, align="C")
        pdf.cell(55, 7, diff, border=1, align="C")
        pdf.cell(25, 7, count_str, border=1, align="C")

        # Status cell with color
        if status_str == "PASS":
            pdf.set_text_color(34, 197, 94)
        else:
            pdf.set_text_color(239, 68, 68)
        pdf.set_font("malgun", "B", 9)
        pdf.cell(20, 7, status_str, border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("malgun", "", 9)
        pdf.set_text_color(50, 50, 50)

    pass_count = sum(1 for r in results if r["status"] == "PASS")
    total_count = len(results)
    pdf.ln(4)
    pdf.set_font("malgun", "B", 11)
    if pass_count == total_count:
        pdf.set_text_color(34, 197, 94)
        pdf.cell(0, 8, f"ALL PASS ({pass_count}/{total_count})", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_text_color(239, 68, 68)
        pdf.cell(0, 8, f"{pass_count}/{total_count} PASSED", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(50, 50, 50)

    # ── Page 2+: 각 샘플 상세 ──
    for idx, r in enumerate(results):
        pdf.add_page()
        label, topic, diff = sample_labels.get(r["sample"], (r["sample"], "", ""))

        pdf.section_title(f"2.{idx+1}  {label}: {topic}")

        # 메타 정보
        pdf.sub_title("메타 정보")
        meta = r["parsed"].get("meta", {})
        pdf.set_font("malgun", "", 9)
        pdf.cell(30, 6, "소요시간:", new_x="END")
        pdf.cell(0, 6, f"{meta.get('g_time', 'N/A')}분", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(30, 6, "조사 목적:", new_x="END")
        pdf.cell(0, 6, str(meta.get('g_purpose', 'N/A')), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(30, 6, "조사 대상:", new_x="END")
        pdf.cell(0, 6, str(meta.get('g_target', 'N/A')), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # 질문 목록
        pdf.sub_title("추출된 질문")
        questions = r["parsed"].get("questions", [])

        # Table header
        pdf.set_font("malgun", "B", 8)
        pdf.set_fill_color(245, 245, 245)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(10, 6, "No.", border=1, fill=True, align="C")
        pdf.cell(18, 6, "섹션", border=1, fill=True, align="C")
        pdf.cell(22, 6, "태그", border=1, fill=True, align="C")
        pdf.cell(140, 6, "질문 내용", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("malgun", "", 8)
        pdf.set_text_color(50, 50, 50)
        for q in questions:
            section = q.get("section", "?")
            section_display = {"icebreak": "ICE BREAK", "main": "본설문", "closing": "CLOSING"}.get(section, section)

            # Section color
            if section == "icebreak":
                pdf.set_fill_color(224, 231, 255)  # light indigo
            elif section == "closing":
                pdf.set_fill_color(254, 226, 226)  # light red
            else:
                pdf.set_fill_color(255, 255, 255)

            order_str = f"Q{q.get('order', '?')}"
            tag = q.get("tag", "?")
            content = q.get("content", "")

            # Truncate if too long
            if len(content) > 75:
                content = content[:73] + "..."

            fill = section in ("icebreak", "closing")
            pdf.cell(10, 6, order_str, border=1, align="C", fill=fill)
            pdf.cell(18, 6, section_display, border=1, align="C", fill=fill)
            pdf.cell(22, 6, tag, border=1, align="C", fill=fill)
            pdf.cell(140, 6, content, border=1, fill=fill, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(3)
        pdf.set_font("malgun", "", 9)
        pdf.cell(0, 6, f"총 {len(questions)}개 질문 추출  |  난이도: {diff}", new_x="LMARGIN", new_y="NEXT")

        # 이슈
        if r["issues"]:
            pdf.ln(3)
            pdf.sub_title("발견된 이슈")
            for issue in r["issues"]:
                pdf.body_text(f"  - {issue}")

    # ── 마지막 페이지: 사용된 프롬프트 ──
    pdf.add_page()
    pdf.section_title("3. 사용된 파싱 프롬프트")
    pdf.set_font("malgun", "", 8)
    pdf.set_text_color(60, 60, 60)
    # 프롬프트를 줄 단위로 출력 (여백 확보)
    left_margin = 12
    right_margin = 12
    usable_w = pdf.w - left_margin - right_margin
    pdf.set_left_margin(left_margin)
    pdf.set_right_margin(right_margin)
    for line in prompt_text.split("\n"):
        if line.startswith("#"):
            pdf.set_font("malgun", "B", 9)
            pdf.set_text_color(67, 56, 202)
            pdf.multi_cell(usable_w, 5, line)
            pdf.set_font("malgun", "", 8)
            pdf.set_text_color(60, 60, 60)
        elif line.strip():
            pdf.multi_cell(usable_w, 4.5, line)
        else:
            pdf.ln(3)

    # 저장
    out_path = RESULTS_DIR / f"report_pdf_parser_{ts}.pdf"
    pdf.output(str(out_path))
    print(f"PDF 리포트 생성 완료: {out_path}")
    return out_path


if __name__ == "__main__":
    result_file = find_latest_result()
    print(f"결과 파일: {result_file}")
    generate_report(result_file)
