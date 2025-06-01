# 🌌 OrrerySQL

**SQL 분석과 시각적 쿼리 플로우 해석을 제공하는 데이터베이스 개발자 도구**

OrrerySQL은 복잡한 SQL 쿼리를 직관적으로 분석하고 이해할 수 있도록 도와주는 GUI 기반 SQL 개발 환경입니다. 천체 운행을 보여주는 오러리(Orrery)처럼, SQL 쿼리의 실행 흐름을 시각적으로 표현합니다.

![OrrerySQL](https://img.shields.io/badge/Language-Python-blue)
![PyQt6](https://img.shields.io/badge/GUI-PySide6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ 주요 기능

### 🔍 **SQL 쿼리 분석**
- **AST 기반 구문 분석**: sqlglot를 활용한 정확한 SQL 파싱
- **쿼리 플로우 시각화**: SELECT, JOIN, WHERE 조건의 실행 순서 표시
- **CTE 분석**: WITH 절과 서브쿼리의 복잡한 관계 해석

### 🎨 **사용자 친화적 인터페이스**
- **다국어 지원**: 한국어/영어 동적 전환
- **SQL 구문 강조**: 키워드, 테이블명, 컬럼명 하이라이팅
- **자동 완성**: 테이블과 컬럼명 기반 인텔리센스

### 🗄️ **다중 데이터베이스 지원**
- **DuckDB**: 고성능 분석용 인메모리 데이터베이스
- **SQLite**: 경량화된 파일 기반 데이터베이스
- **플러그인 아키텍처**: 확장 가능한 데이터베이스 엔진 지원

### 📊 **결과 관리**
- **탭 기반 멀티 쿼리**: 여러 쿼리를 동시에 작업
- **Excel 내보내기**: 쿼리 결과의 손쉬운 데이터 추출
- **와이드 뷰**: 많은 컬럼을 가진 결과의 확장 보기

## 🚀 빠른 시작

### 설치

#### 1. 실행 파일 다운로드 (권장)
```bash
# Releases에서 최신 버전의 OrrerySQL.exe 다운로드
# 별도 설치 없이 바로 실행 가능
```

#### 2. 소스코드에서 실행
```bash
# 저장소 클론
git clone https://github.com/your-username/OrrerySQL.git
cd OrrerySQL

# 의존성 설치
pip install -r requirements.txt

# 실행
python main.py
```

### 패키징 (개발자용)
```bash
# PyInstaller를 사용한 실행 파일 생성
python build.py

# 또는 배치 파일 실행 (Windows)
build.bat
```

## 🛠️ 기술 스택

| 구분 | 기술 |
|------|------|
| **Language** | Python 3.11+ |
| **GUI Framework** | PySide6 (Qt6) |
| **SQL Parser** | sqlglot |
| **Database** | DuckDB, SQLite |
| **Data Processing** | pandas |
| **Export** | openpyxl |
| **Packaging** | PyInstaller |

## 📁 프로젝트 구조

```
OrrerySQL/
├── 📁 SQLCoreProject/
│   ├── 📁 core/              # SQL 분석 엔진
│   │   ├── SQLInterpreterCore.py
│   │   ├── ASTKeywordsAnalyzer.py
│   │   └── CTEkeywords.py
│   ├── 📁 ui/                # UI 구성요소
│   │   ├── SQLgateUI.py
│   │   ├── SQLtoolbar.py
│   │   └── SQLtabsheet.py
│   ├── 📁 data/              # 데이터 처리
│   ├── 📁 plugin/            # 플러그인 시스템
│   └── 📁 resources/         # 테마, 아이콘
├── 📁 language/              # 다국어 지원
│   ├── lang.py
│   ├── ko.py
│   └── en.py
├── main.py                   # 애플리케이션 진입점
├── requirements.txt          # 의존성 목록
└── README.md
```

## 🎯 사용 예시

### SQL 쿼리 분석
```sql
WITH sales_summary AS (
    SELECT 
        customer_id,
        SUM(amount) as total_sales
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.order_date >= '2024-01-01'
    GROUP BY customer_id
)
SELECT 
    c.customer_name,
    s.total_sales
FROM customers c
JOIN sales_summary s ON c.customer_id = s.customer_id
WHERE s.total_sales > 1000
ORDER BY s.total_sales DESC;
```

**OrrerySQL 분석 결과:**
```
1. CTE 'sales_summary' 정의 ↓
2. JOIN 수행: orders ⟷ order_items  
3. WHERE 조건 적용: order_date >= '2024-01-01'
4. GROUP BY 집계: customer_id
5. SUM 집계 함수 계산: amount
6. JOIN 수행: customers ⟷ sales_summary
7. WHERE 조건 적용: total_sales > 1000
8. ORDER BY 정렬: total_sales DESC
```

## 🔧 개발 철학

**RSU (Responsibility Structural Unit)** 방법론을 채택하여:
- 각 모듈의 명확한 책임 분리
- 독립적이고 테스트 가능한 최소 단위 구성
- 확장 가능한 플러그인 아키텍처

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 👥 개발팀

- **Main Developer**: SungHyung-Lim & LLMs
- **SQL Analysis Engine**: Advanced AST parsing with sqlglot
- **UI/UX Design**: Modern dark theme with PySide6

## 🙏 감사의 말

- [sqlglot](https://github.com/tobymao/sqlglot) - 강력한 SQL 파서
- [DuckDB](https://duckdb.org/) - 고성능 분석 데이터베이스
- [PySide6](https://www.qt.io/qt-for-python) - 현대적인 GUI 프레임워크

---

**⭐ 이 프로젝트가 도움이 되셨다면 스타를 눌러주세요!**
