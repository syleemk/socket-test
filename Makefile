.PHONY: help setup up down be fe logs

# ── 기본 ────────────────────────────────────────────────
help:
	@echo "사용 가능한 명령어:"
	@echo "  make setup   - 의존성 설치 (최초 1회)"
	@echo "  make up      - 인프라(Redis, PostgreSQL) 시작"
	@echo "  make down    - 인프라 종료"
	@echo "  make be      - 백엔드 서버 실행"
	@echo "  make fe      - 프론트엔드 개발 서버 실행"
	@echo "  make logs    - 인프라 컨테이너 로그 확인"

# ── 환경 세팅 ────────────────────────────────────────────
setup:
	uv --directory backend sync

# ── 인프라 ───────────────────────────────────────────────
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

# ── 서버 실행 ────────────────────────────────────────────
be:
	uv --directory backend run uvicorn main:app --reload --host 0.0.0.0 --port 8000

fe:
	npx serve frontend -l 3000
