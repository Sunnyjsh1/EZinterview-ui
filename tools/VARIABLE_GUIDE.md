# EasyInterview 변수 가이드

> 전체 파이프라인에서 사용되는 변수 정의 + JSON 스키마 + DB 매핑을 한 문서에 정리
> Version 1.0 | 2026-03-25

---

## 1. 파이프라인 흐름과 변수 관계

```
[INIT]                    [EDIT]                [INTERVIEW]           [RESULT]
G_time ─┐                G_concept ──┐         확정 가이드라인 ──┐   R1 트랜스크립트
G_purpose ┼→ G_questions   G_media ───┤→ 확정    응답자 입력 ───┤→  R2 응답 요약
G_target ─┘                수정 요청 ──┘  가이드라인              │   R3 인사이트 보고서
                                                                 │   R4 워드 클라우드
G_questions_raw  (방식 B) ─┐                                      └─  R5 센티멘트 분석
G_questions_file (방식 C) ─┤→ G_questions (정규화)
```

---

## 2. INIT 단계 변수

### 2.1 입력 변수 (공통)

| 변수 | 타입 | 필수 | 유효값 | 설명 | 예시 |
|---|---|---|---|---|---|
| `G_time` | integer | O | 5, 10, 15, 20, 25, 30 | 예상 소요시간 (분). 범위 이탈 시 가장 가까운 값으로 반올림 | `15` |
| `G_purpose` | string | O | 비어있지 않은 문자열 | 조사 목적 (1문장) | `건강 음료 신제품 컨셉에 대한 소비자 반응 파악` |
| `G_target` | string | O | 비어있지 않은 문자열 | 조사 대상 (1문장) | `건강에 관심 있는 30~40대 직장인 (남녀 혼합)` |

### 2.2 입력 방식별 변수

| 변수 | 타입 | 방식 | 설명 |
|---|---|---|---|
| `G_questions_raw` | string | B (직접 작성) | 운영자가 텍스트로 직접 작성한 질문 목록 |
| `G_questions_file` | array | C (파일 업로드) | PDF/DOCX/XLSX에서 파싱된 질문 배열 |
| `G_questions` | array | **공통 출력** | 세 방식 모두의 정규화 결과. EDIT 단계 진입 변수 |

### 2.3 G_time → 질문 수 매핑

| G_time | ICE BREAK | 본설문 | CLOSING | 전체 |
|---|---|---|---|---|
| 5분 | 1개 | 2~3개 | 1개 | 4~5개 |
| 10분 | 1개 | 4~5개 | 1개 | 6~7개 |
| 15분 | 1개 | 6~8개 | 1개 | 8~10개 |
| 20분 | 1개 | 9~10개 | 1개 | 11~12개 |
| 25분 | 1개 | 11~13개 | 1개 | 13~15개 |
| 30분 | 1개 | 14~15개 | 1개 | 16~17개 |

---

## 3. G_questions 아이템 스키마 (INIT 출력 / EDIT 입력)

```json
{
  "order": 0,
  "type": "question",
  "stimulus": null,
  "content": "질문 텍스트"
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `order` | integer | 질문 순서 (0부터 시작). Q0 = ICE BREAK |
| `type` | string | 고정값 `"question"` |
| `stimulus` | object \| null | 자극물 정보. INIT에서는 항상 null. EDIT에서 삽입 |
| `content` | string | 본 질문 텍스트 |

### stimulus 객체 (EDIT 단계에서 삽입)

```json
{
  "instruction": "아래 제품 이미지를 보시고 첫인상을 말씀해주세요.",
  "media_type": "image",
  "media_url": "https://example.com/product_concept_a.png"
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `stimulus.instruction` | string \| null | 안내 멘트 |
| `stimulus.media_type` | string \| null | `"image"` \| `"url"` \| `"video"` |
| `stimulus.media_url` | string \| null | 미디어 경로 |

---

## 4. EDIT 단계 변수

| 변수 | 타입 | 설명 |
|---|---|---|
| `G_concept` | array | 복수 컨셉 정의. 개별 평가 → 비교 구조 자동 생성 |
| `G_media` | array | 자극물(이미지, 영상, URL) 목록. 3개 이상 시 본설문 질문 수 차감 |

### G_media 차감 규칙

| G_media 수 | 질문 수 조정 |
|---|---|
| 0~2개 | 유지 |
| 3개 이상 | 초과분만큼 본설문에서 차감 (최소 2개 보장) |

---

## 5. PDF 파싱 스키마 (방식 C: 파일 업로드)

파싱 프롬프트(`init_pdf_parser.txt`)의 출력 스키마.

```json
{
  "meta": {
    "g_time": 15,
    "g_purpose": "조사 목적",
    "g_target": "조사 대상"
  },
  "questions": [
    {
      "order": 0,
      "section": "icebreak",
      "tag": "워밍업",
      "content": "질문 텍스트"
    }
  ]
}
```

### meta 객체

| 필드 | 타입 | 설명 |
|---|---|---|
| `g_time` | integer \| null | 소요시간 (분). 문서에 없으면 null |
| `g_purpose` | string \| null | 조사 목적 (1문장) |
| `g_target` | string \| null | 조사 대상 (1문장) |

### questions 아이템

| 필드 | 타입 | 유효값 | 설명 |
|---|---|---|---|
| `order` | integer | 0부터 연속 | 질문 순서 |
| `section` | string | `"icebreak"` \| `"main"` \| `"closing"` | 섹션 분류 |
| `tag` | string | 2~4글자 | 주제 태그 |
| `content` | string | | 질문 텍스트 (정규화된 질문문) |

### section 분류 규칙

| 값 | 조건 |
|---|---|
| `icebreak` | "ICE BREAK", "워밍업", "도입" 라벨 / 첫 질문 + 가벼운 톤 |
| `main` | icebreak, closing이 아닌 모든 질문 |
| `closing` | "CLOSING", "마무리", "종합" 라벨 / 마지막 질문 + 종합 정리 |

### tag 부여 규칙

| 조건 | 처리 |
|---|---|
| 문서에 태그 명시됨 | 그대로 사용 |
| icebreak | `"워밍업"` 고정 |
| closing | `"마무리"` 고정 |
| main (태그 없음) | 질문 내용 기반 2~4글자 자동 생성 |

---

## 6. INTERVIEW 단계 변수

인터뷰 진행 중 시스템이 관리하는 변수.

| 변수 | 타입 | 설명 |
|---|---|---|
| `current_question` | integer | 현재 진행 중인 질문 order |
| `probing_count` | integer | 현재 질문의 프루빙 횟수 (최대 3) |
| `turn` | integer | 대화 턴 번호 |
| `role` | string | `"moderator"` \| `"respondent"` |
| `message` | string | 해당 턴의 발화 텍스트 |
| `question_ref` | integer \| null | 해당 발화가 속한 질문 order. 프루빙은 동일 question_ref |

### 프루빙 스킵 조건 (3가지 모두 충족 시에만)

1. 이유가 명시되어 있다 ("~때문에", "~해서")
2. 구체적 상황/예시가 포함되어 있다
3. 2문장 이상의 답변이다

---

## 7. RESULT 단계 변수 (R1~R5)

### 7.1 R1. 원문 트랜스크립트

STT 원시 데이터. LLM 처리 없음.

| 필드 | 타입 | 설명 |
|---|---|---|
| `respondent_id` | string | 응답자 ID (P01, P02...) |
| `speaker` | string | `"moderator"` \| `"respondent"` |
| `text` | string | 발화 원문 |
| `timestamp` | string | 발화 시작 시간 (mm:ss) |
| `question_ref` | string | 해당 발화의 질문 번호 (Q0, Q1...) |

### 7.2 R2. 응답 요약

```json
{
  "respondent_id": "P01",
  "questions": [
    {
      "question_id": "Q0",
      "question_text": "질문 텍스트",
      "summary": "3~4문장 요약",
      "highlights": ["핵심 구절 1", "핵심 구절 2"]
    }
  ]
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `respondent_id` | string | 응답자 ID |
| `question_id` | string | 질문 번호 (Q0, Q1...) |
| `question_text` | string | 질문 원문 |
| `summary` | string | 핵심 답변 3~4문장 요약 |
| `highlights` | string[] | 분석적으로 중요한 핵심 구절 2~3개 |

### 7.3 R3. 인사이트 보고서 (기본)

```json
{
  "questions": [
    {
      "question_id": "Q1",
      "question_text": "질문 텍스트",
      "finding": {
        "title": "핵심 발견 제목",
        "bullets": ["불릿 1", "불릿 2", "불릿 3"]
      },
      "distribution": {
        "positive_ratio": 0.625,
        "neutral_ratio": 0.25,
        "negative_ratio": 0.125,
        "description": "분포 설명"
      },
      "keywords": {
        "positive": ["키워드1", "키워드2"],
        "negative": ["키워드1"]
      },
      "voc": {
        "positive": { "text": "발화 원문", "respondent_id": "P01" },
        "negative": { "text": "발화 원문", "respondent_id": "P02" }
      }
    }
  ]
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `finding.title` | string | 핵심 발견 1문장 제목 |
| `finding.bullets` | string[] | 구체적 근거 최대 3개 |
| `distribution.positive_ratio` | float | 긍정 비율 (0.0~1.0) |
| `distribution.neutral_ratio` | float | 중립 비율 (0.0~1.0) |
| `distribution.negative_ratio` | float | 부정 비율 (0.0~1.0) |
| `distribution.description` | string | 분포 의미 설명 1문장 |
| `keywords.positive` | string[] | 긍정 키워드 3~5개 |
| `keywords.negative` | string[] | 부정 키워드 2~3개 |
| `voc.positive.text` | string | 긍정 대표 발화 원문 |
| `voc.positive.respondent_id` | string | 긍정 대표 발화 응답자 ID |
| `voc.negative.text` | string \| null | 부정 대표 발화 원문 |
| `voc.negative.respondent_id` | string \| null | 부정 대표 발화 응답자 ID |

### 7.4 R3. 인사이트 보고서 (요청형)

자유 프롬프트 기반. 출력은 Markdown 형식.

| 필드 | 타입 | 설명 |
|---|---|---|
| `prompt` | string | 사용자 분석 요청 텍스트 |
| `output` | string (md) | Markdown 형식 분석 보고서 |

### 7.5 R4. 워드 클라우드

질문별 탭. 형태소 분석 기반.

| 필드 | 타입 | 설명 |
|---|---|---|
| `question_id` | string | 질문 번호 |
| `keyword` | string | 추출된 키워드 |
| `frequency` | integer | 등장 횟수 |
| `speakers` | integer | 사용한 응답자 수 |
| `sentiment` | string | `"positive"` \| `"neutral"` \| `"negative"` |
| `representative_voc` | string | 대표 발화 원문 |
| `respondent_id` | string | 대표 발화 응답자 ID |

### 7.6 R5. 센티멘트 분석

```json
{
  "respondent_id": "P01",
  "questions": [
    {
      "question_id": "Q0",
      "question_text": "질문 텍스트",
      "utterances": [
        { "text": "발화 원문", "sentiment": "positive" }
      ],
      "summary": {
        "positive_count": 2,
        "neutral_count": 1,
        "negative_count": 0,
        "dominant": "positive",
        "representative_positive": "긍정 대표 발화",
        "representative_negative": null
      }
    }
  ],
  "overall": {
    "positive_ratio": 0.6,
    "neutral_ratio": 0.3,
    "negative_ratio": 0.1,
    "dominant": "positive"
  }
}
```

| 필드 | 타입 | 유효값 | 설명 |
|---|---|---|---|
| `utterances[].text` | string | | 응답자 발화 원문 |
| `utterances[].sentiment` | string | `"positive"` \| `"neutral"` \| `"negative"` | 문장별 감정 분류 |
| `summary.positive_count` | integer | 0 이상 | 긍정 발화 수 |
| `summary.neutral_count` | integer | 0 이상 | 중립 발화 수 |
| `summary.negative_count` | integer | 0 이상 | 부정 발화 수 |
| `summary.dominant` | string | `"positive"` \| `"neutral"` \| `"negative"` | 지배적 감정 |
| `summary.representative_positive` | string \| null | | 긍정 대표 발화 |
| `summary.representative_negative` | string \| null | | 부정 대표 발화 |
| `overall.positive_ratio` | float | 0.0~1.0 | 전체 긍정 비율 |
| `overall.neutral_ratio` | float | 0.0~1.0 | 전체 중립 비율 |
| `overall.negative_ratio` | float | 0.0~1.0 | 전체 부정 비율 |
| `overall.dominant` | string | | 전체 지배적 감정 |

> ratio 값은 반드시 0.0~1.0 소수점. 절대 퍼센트 정수(62.5)로 쓰지 않는다.

---

## 8. 필터 변수

R2, R3에만 적용. 스크리너 변수 기반 동적 생성.

| 필드 | 타입 | 설명 |
|---|---|---|
| `filter_variables` | object | 스크리너에서 동적 생성된 필터 조건 |

```
예시:
단일: { "성별": "여성" }
복합: { "성별": "여성", "연령": "30대" }  // AND 조건
```

| 결과물 | 필터 적용 | 비고 |
|---|---|---|
| R1 트랜스크립트 | X | 전체 고정 |
| R2 응답 요약 | O | 필터 응답자만 카드 표시 |
| R3 인사이트 보고서 | O | 필터 응답자만 재분석 |
| R4 워드 클라우드 | X | 모수 부족 방지 |
| R5 센티멘트 분석 | X | 모수 부족 방지 |

---

## 9. DB 테이블 ↔ JSON 매핑

### projects 테이블

| DB 컬럼 | 타입 | JSON 변수 매핑 |
|---|---|---|
| `id` | UUID PK | |
| `name` | VARCHAR(200) | |
| `g_time` | INT | `G_time` |
| `g_purpose` | TEXT | `G_purpose` |
| `g_target` | TEXT | `G_target` |
| `status` | VARCHAR(20) | `"init"` \| `"edit"` \| `"interview"` \| `"completed"` |
| `created_at` | TIMESTAMP | |

### questions 테이블

| DB 컬럼 | 타입 | JSON 매핑 |
|---|---|---|
| `id` | UUID PK | |
| `project_id` | UUID FK | → projects.id |
| `order` | INT | `.order` |
| `type` | VARCHAR(20) | `.type` (고정: "question") |
| `instruction` | TEXT NULL | `.stimulus.instruction` |
| `media_type` | VARCHAR(10) NULL | `.stimulus.media_type` |
| `media_url` | TEXT NULL | `.stimulus.media_url` |
| `content` | TEXT | `.content` |

> `stimulus: null` → `instruction`, `media_type`, `media_url` 모두 NULL

### transcripts 테이블

| DB 컬럼 | 타입 | 설명 |
|---|---|---|
| `id` | UUID PK | |
| `project_id` | UUID FK | → projects.id |
| `respondent_id` | UUID | 응답자 식별자 |
| `turn` | INT | 대화 턴 번호 |
| `role` | VARCHAR(20) | `"moderator"` \| `"respondent"` |
| `message` | TEXT | 발화 텍스트 |
| `question_ref` | INT NULL | questions.order 참조 |
| `created_at` | TIMESTAMP | |

---

## 10. 모델 설정

| 항목 | INIT | INTERVIEW | RESULT |
|---|---|---|---|
| Model | gemini-flash-latest | gemini-flash-latest | gemini-flash-latest |
| Temperature | 0 (결정론적) | 0.7 (자연스러운 대화) | 0 (구조적 출력) |
| Max Tokens | 8192 | 8192 | 8192 |
| 응답 형식 | 텍스트 | 텍스트 | JSON (`response_mime_type`) |

---

## 11. 센티멘트 3단계 정의

R3, R4, R5에서 공통 사용.

| 값 | 의미 | 포함 감정 |
|---|---|---|
| `positive` | 긍정 | 호감, 만족, 기대, 관심, 구매 의향 |
| `neutral` | 중립 | 사실 전달, 단순 설명, 판단 유보, 조건부 답변 |
| `negative` | 부정 | 불만, 거부, 무관심, 가격 저항, 비교 열위 |

---

## 12. 프롬프트 파일 인덱스

| 파일 | 단계 | 용도 |
|---|---|---|
| `prompts/init_system.txt` | INIT | 가이드라인 초안 생성 시스템 프롬프트 |
| `prompts/init_pdf_parser.txt` | INIT (방식 C) | PDF 파싱 시스템 프롬프트 |
| `prompts/interview_system.txt` | INTERVIEW | 인터뷰 진행 시스템 프롬프트 |
| `prompts/result_r2_summary.txt` | RESULT R2 | 응답 요약 시스템 프롬프트 |
| `prompts/result_r3_basic.txt` | RESULT R3 (기본) | 인사이트 보고서 시스템 프롬프트 |
| `prompts/result_r3_custom.txt` | RESULT R3 (요청형) | 맞춤 분석 시스템 프롬프트 |
| `prompts/result_r5_sentiment.txt` | RESULT R5 | 센티멘트 분석 시스템 프롬프트 |
