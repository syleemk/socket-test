.PHONY: help setup up down logs rebuild rebuild-be rebuild-fe

# ── 기본 ────────────────────────────────────────────────
help:
	@echo "사용 가능한 명령어:"
	@echo "  make setup   - 의존성 설치 (최초 1회)"
	@echo "  make up      - 인프라(Redis, PostgreSQL) 시작"
	@echo "  make down    - 인프라 종료"
	@echo "  make logs       - 인프라 컨테이너 로그 확인"
	@echo "  make rebuild    - frontend·backend 이미지 재빌드 후 전체 기동"
	@echo "  make rebuild-be - 백엔드만 이미지 재빌드 후 기동"
	@echo "  make rebuild-fe - 프론트엔드만 이미지 재빌드 후 기동"

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

# ── 재빌드 ───────────────────────────────────────────────
rebuild:
	docker compose up -d --build backend frontend

rebuild-be:
	docker compose up -d --build backend

rebuild-fe:
	docker compose up -d --build frontend
