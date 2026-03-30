"""
EasyInterview — Chatbot Prompt Test Runner
시스템 프롬프트 + output guide + 프리셋 5개 + 후속 질문 1건 테스트
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from google import genai
from google.genai import types

API_KEY     = os.environ.get("GEMINI_API_KEY", "")
MODEL       = "gemini-flash-latest"
PROMPTS_DIR = Path(__file__).parent / "prompts"
RESULTS_DIR = Path(__file__).parent / "results"
INPUT_FILE  = RESULTS_DIR / "test_input_r2r5.json"

def get_client():
    return genai.Client(api_key=API_KEY)

def build_transcript(respondents):
    lines = []
    for r in respondents:
        lines.append(f"=== {r['respondent_id']} ({r['category']}) ===")
        for c in r["conversation"]:
            role = "모더레이터" if c["role"] == "moderator" else "응답자"
            lines.append(f"[{role}] {c['text']}")
        lines.append("")
    return "\n".join(lines)

def load_system():
    sys_prompt = (PROMPTS_DIR / "result_chat_system.txt").read_text(encoding="utf-8")
    output_guide = (PROMPTS_DIR / "result_chat_output_guide.txt").read_text(encoding="utf-8")
    return sys_prompt + "\n\n" + output_guide

async def run_chat_test(test_id, user_msg, transcript, prev_history=None):
    print(f"  [{test_id}] {user_msg[:50]}...")
    start = time.time()

    try:
        c = get_client()
        system = load_system()

        context = f"""[자동 첨부 컨텍스트]
현재 탭: R3 인사이트 보고서
현재 필터: 전체 (n=4)
응답자: P01(신제품개발), P02(광고/캠페인), P03(구매의사결정), P04(타겟세분화)

--- 전체 인터뷰 데이터 ---
{transcript}"""

        messages = []
        if prev_history:
            messages.extend(prev_history)
        messages.append({"role": "user", "parts": [{"text": context + "\n\n" + user_msg}]}
                        if not prev_history else
                        {"role": "user", "parts": [{"text": user_msg}]})

        response = c.models.generate_content(
            model=MODEL,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0,
            )
        )
        result = response.text
        elapsed = round(time.time() - start, 2)

        # 검증
        char_count = len(result)
        has_finding = "핵심" in result or "발견" in result
        has_quote = "—" in result or "P0" in result
        has_followup = "?" in result.split("\n")[-3:] if result.strip() else False

        status = "PASS" if has_finding and has_quote else "WARN"
        print(f"  [{status}] {test_id}: {char_count}자, 발견={'O' if has_finding else 'X'}, "
              f"인용={'O' if has_quote else 'X'} ({elapsed}s)")

        # 대화 이력 반환 (멀티턴용)
        new_history = messages + [{"role": "model", "parts": [{"text": result}]}]

        return {
            "test_id": test_id,
            "user_msg": user_msg,
            "status": status,
            "response": result,
            "char_count": char_count,
            "elapsed": elapsed,
            "history": new_history
        }

    except Exception as e:
        elapsed = round(time.time() - start, 2)
        print(f"  [!!] {test_id}: ERROR - {e}")
        return {
            "test_id": test_id,
            "user_msg": user_msg,
            "status": "ERROR",
            "response": "",
            "char_count": 0,
            "elapsed": elapsed,
            "error": str(e),
            "history": None
        }

async def main():
    print("=" * 65)
    print("  EasyInterview Chatbot 프롬프트 테스트")
    print(f"  모델: {MODEL}")
    print("=" * 65)

    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)
    transcript = build_transcript(data["respondents"])
    print(f"  트랜스크립트: {len(transcript)}자\n")

    # 프리셋 로드
    with open(PROMPTS_DIR / "result_chat_presets.json", encoding="utf-8") as f:
        presets = json.load(f)["presets"]

    results = []

    # 테스트 1~5: 프리셋
    for i, preset in enumerate(presets):
        prompt = preset["prompt"].replace("{current_question}", "Q1")
        r = await run_chat_test(f"T{i+1}_{preset['id']}", prompt, transcript)
        results.append(r)

    # 테스트 6: 자유 질문
    r = await run_chat_test("T6_free", "30대와 40대 응답 차이가 있어?", transcript)
    results.append(r)

    # 테스트 7: 멀티턴 (T6 후속)
    if r["history"]:
        r2 = await run_chat_test("T7_followup", "P01 답변을 더 자세히 볼 수 있어?",
                                  transcript, prev_history=r["history"])
        results.append(r2)

    # 저장
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_results = [{k: v for k, v in r.items() if k != "history"} for r in results]
    json_path = RESULTS_DIR / f"result_chat_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(save_results, f, ensure_ascii=False, indent=2)

    # 요약
    print("\n" + "=" * 65)
    print("  챗봇 테스트 결과")
    print("=" * 65)
    for r in results:
        mark = {"PASS": "OK", "WARN": "!!", "ERROR": "!!"}[r["status"]]
        print(f"  [{mark}] {r['test_id']:20s} | {r['char_count']:4d}자 | {r['elapsed']:.1f}s | {r['status']}")
    print("=" * 65)
    print(f"  저장: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
