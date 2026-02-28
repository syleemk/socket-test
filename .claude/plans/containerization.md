# 컨테이너화 및 K8s 전환 계획

## 전체 로드맵

```
1단계: Docker Compose로 로컬 개발환경 완성   ✅ (완료)
        ↓
2단계: Dockerfile 최적화 (multi-stage build)  ✅ (완료)
        ↓
3단계: minikube 로컬 k8s 클러스터 구성        ⬜ (미완료)
        ↓
4단계: kompose로 자동 변환 후 yaml 직접 수정  ⬜ (미완료)
        ↓
5단계: Ingress, HPA, liveness/readinessProbe 추가 ⬜ (미완료)
        ↓
6단계: (선택) Helm chart로 패키징              ⬜ (미완료)
```

---

## 1단계: Docker Compose 완성 ✅

### 목표
- BE (FastAPI), FE (nginx), Redis, PostgreSQL 4개 서비스를 compose로 통합

### 작업 목록
- [x] `backend/Dockerfile` 작성
- [x] `frontend/Dockerfile` 작성 (nginx 기반)
- [x] `docker-compose.yml` 에 backend, frontend 서비스 추가
- [x] `.env` 파일로 환경변수 외부화 (루트 `.env.example` 추가, `.env`는 gitignore)
- [x] 각 서비스에 `healthcheck` 추가
- [x] `depends_on` + `condition: service_healthy` 설정
- [x] `/health` 엔드포인트 추가 (healthcheck 의존)

### K8s 전환을 염두에 둔 작성 원칙
- 이미지 태그 명시 (`image: socket-test-backend:latest`)
- 환경변수는 모두 `.env`로 분리 (→ 추후 ConfigMap/Secret 대응)
- Named volume 사용 (→ PVC 개념 이해)
- `healthcheck` 추가 (→ `livenessProbe`와 1:1 대응)

### 예상 구조
```yaml
services:
  backend:
    build: ./backend
    image: socket-test-backend:latest
    ports:
      - "8000:8000"
    env_file: .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    depends_on:
      redis:
        condition: service_healthy
      postgres:
        condition: service_healthy

  frontend:
    build: ./frontend
    image: socket-test-frontend:latest
    ports:
      - "3000:80"
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  postgres:
    image: postgres:16-alpine
    env_file: .env
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

---

## 2단계: Dockerfile 최적화 ✅

### Backend (FastAPI + uv)
```dockerfile
# multi-stage build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend (nginx)
```dockerfile
FROM nginx:alpine
COPY . /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

---

## 3단계: minikube 구성

### 사전 준비
```bash
# minikube 설치 (macOS)
brew install minikube kubectl

# 클러스터 시작
minikube start --driver=docker

# 로컬 이미지 사용 설정
eval $(minikube docker-env)

# 이미지 빌드 (minikube 내부에서)
docker build -t socket-test-backend:latest ./backend
docker build -t socket-test-frontend:latest ./frontend
```

---

## 4단계: kompose로 변환 후 수정

### 자동 변환
```bash
# kompose 설치
brew install kompose

# 변환 (k8s/ 디렉토리에 yaml 생성)
kompose convert -o k8s/

# 생성되는 파일 예시
# k8s/backend-deployment.yaml
# k8s/backend-service.yaml
# k8s/frontend-deployment.yaml
# k8s/frontend-service.yaml
# k8s/redis-deployment.yaml  → StatefulSet으로 수동 변경 필요
# k8s/postgres-deployment.yaml → StatefulSet으로 수동 변경 필요
```

### Docker Compose → K8s 개념 매핑

| Docker Compose | Kubernetes |
|---------------|------------|
| `service` | `Deployment` + `Service` |
| `ports` | `Service` (ClusterIP/NodePort/LoadBalancer) |
| `volumes` | `PersistentVolume` + `PersistentVolumeClaim` |
| `environment` | `ConfigMap` + `Secret` |
| `depends_on` | `readinessProbe` + init containers |
| `healthcheck` | `livenessProbe` + `readinessProbe` |
| `networks` | 기본 내장 (같은 namespace 내 DNS 통신) |

### 수동으로 변경해야 할 사항
- Redis, PostgreSQL: `Deployment` → `StatefulSet`
- 환경변수: `ConfigMap` (일반값) + `Secret` (비밀번호) 분리
- 볼륨: `PersistentVolumeClaim` 명시

---

## 5단계: Ingress, Probe, HPA 추가

### Ingress (FE/BE 라우팅)
```bash
minikube addons enable ingress
```

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: socket-test-ingress
spec:
  rules:
    - host: socket-test.local
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

### liveness/readiness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### HPA (수평 자동 확장)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 1
  maxReplicas: 3
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## 6단계: Helm Chart (선택)

```bash
# chart 스캐폴딩
helm create socket-test

# 구조
socket-test/
  Chart.yaml
  values.yaml          # 환경별 설정값
  templates/
    backend/
    frontend/
    redis/
    postgres/
    ingress.yaml
```

---

## 참고 명령어

```bash
# Docker Compose
docker compose up -d
docker compose logs -f
docker compose down -v

# Kubernetes
kubectl apply -f k8s/
kubectl get pods
kubectl get services
kubectl logs -f deployment/backend
kubectl exec -it deployment/backend -- bash
minikube dashboard
minikube tunnel  # LoadBalancer 타입 서비스 로컬 접근
```
