#  Delivery Checklist — Day 12 Lab Submission

> **Student Name:** Dương Chí Thành  
> **Student ID:** 2A202600047  
> **Date:** 17/4/2026

---

##  Submission Requirements

Submit a **GitHub repository** containing: https://github.com/strelock123/day12_Duong_Chi_Thanh_2A202600047.git

### 1. Mission Answers (40 points)

Create a file `MISSION_ANSWERS.md` with your answers to all exercises:

```markdown
# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
# ❌ Vấn đề 1: API key hardcode trong code
# Nếu push lên GitHub → key bị lộ ngay lập tức
OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"
DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"

# ❌ Vấn đề 2: Không có config management
DEBUG = True
MAX_TOKENS = 500


@app.get("/")
def home():
    return {"message": "Hello! Agent is running on my machine :)"}


@app.post("/ask")
def ask_agent(question: str):
    # ❌ Vấn đề 3: Print thay vì proper logging
    print(f"[DEBUG] Got question: {question}")
    print(f"[DEBUG] Using key: {OPENAI_API_KEY}")  # ❌ log ra secret!

    response = ask(question)

    print(f"[DEBUG] Response: {response}")
    return {"answer": response}


# ❌ Vấn đề 4: Không có health check endpoint
# Nếu agent crash, platform không biết để restart

# ❌ Vấn đề 5: Port cố định — không đọc từ environment
# Trên Railway/Render, PORT được inject qua env var
if __name__ == "__main__":
    print("Starting agent on localhost:8000...")
    uvicorn.run(
        "app:app",
        host="localhost",   # ❌ chỉ chạy được trên local
        port=8000,          # ❌ cứng port
        reload=True         # ❌ debug reload trong production
    )


### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config  | ...     | ...        | ...            |
Feature	Basic	Advanced	Tại sao quan trọng?
Config	Hardcode (OPENAI_API_KEY, DATABASE_URL, DEBUG, MAX_TOKENS, cứng host/port)	Env vars qua config.settings (PORT, DEBUG, host, app_name, environment, llm_model, allowed_origins)	Env vars giúp tách cấu hình khỏi code, dễ deploy lên cloud, tránh leak secret và cho phép dùng cùng code trên nhiều môi trường.
Health check	Không có	Có /health và /ready	Health/readiness probe giúp platform biết app còn sống và sẵn sàng, hỗ trợ restart tự động và load balancing.
Logging	print() debug, log ra cả secret	Structured JSON logging với logging và logger.info(...)	Logging cấu trúc dễ parse, dễ giám sát, và an toàn hơn vì không in secret; phù hợp với production và log aggregator.
Shutdown	Đột ngột, không cleanup, chạy uvicorn.run(... reload=True)	Graceful shutdown với lifespan + SIGTERM handler	Graceful shutdown cho phép hoàn thành request hiện tại, đóng kết nối đúng cách và tránh mất mát dữ liệu khi container bị tắt.

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: Đây là image  Python chính thức từ Docker Hub, phiên bản 3.11, chứa đầy đủ Python runtime và các công cụ cần thiết.
2. Working directory: Đây là thư mục làm việc bên trong container, nơi các lệnh tiếp theo sẽ thực thi và file sẽ được copy vào.
3. Tại sao Copy requirements.txt trước: Để tận dụng Docker layer caching. Nếu requirements.txt không thay đổi giữa các lần build, Docker sẽ sử dụng cache cho bước RUN pip install, giúp build nhanh hơn và tiết kiệm băng thông.
4. CMD vs Entrypoint khác nhau thế nào: CMD định nghĩa command mặc định khi container start, có thể override bằng arguments khi docker run. entrypoint định nghĩa executable cố định, arguments từ CMD hoặc docker run sẽ được pass vào nó như parameters. Entrypoint không thể override dễ dàng 
...
### Exercise 2.2:
### Exercise 2.3: Image size comparison
- Develop: [1.66] GB
- Production: [236] MB
- Difference: [720]%
### Exercise 2.4: Docker Compose stack

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://day12duongchithanh2a202600047-production.up.railway.app/
- Screenshot: [Link to screenshot in repo]
![alt text](image.png)
### Exercise 3.2: Comparison (render.yaml vs railway.toml)
Câu hỏi: So sánh render.yaml với railway.toml. Khác nhau gì?

render.yaml cho phép định nghĩa toàn bộ hạ tầng (Blueprint) bao gồm cả các dịch vụ phụ trợ như Redis.
railway.toml tập trung vào cấu hình runtime và build pipeline của một service đơn lẻ.

## Part 4: API Security

### Exercise 4.1-4.3: Test results
[Paste your test output]
Câu hỏi: API key được check ở đâu? Điều gì xảy ra nếu sai key? JWT flow là gì? Algorithm nào được dùng cho Rate Limiting?

Trả lời:

API Key: Trả về 401 Unauthorized nếu thiếu key và 403 Forbidden nếu key không khớp với AGENT_API_KEY.
JWT: Người dùng cần POST tới /token lấy Bearer token trước khi gọi /ask. Token giúp mã hóa thông tin người dùng và có thời gian hết hạn (expiry).
Rate Limiting: Thuật toán Sliding Window Counter được sử dụng. Nếu gọi quá 10 req/phút, server phản hồi lỗi 429 Too Many Requests.

### Exercise 4.4: Cost guard implementation
[Explain your aproach]
Câu hỏi: Giải thích cách implement logic check_budget.

Approach: Sử dụng Redis để lưu trữ mức chi tiêu (spending) theo user_id và tháng hiện tại. Trước khi gọi LLM, hệ thống kiểm tra ngân quỹ còn lại. Dữ liệu được đặt TTL 32 ngày để tự động reset mỗi tháng.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]
```
**Câu hỏi:** Ghi chú các điểm quan trọng về Health checks, Graceful shutdown, Stateles design, Load balancing.

**Trả lời:**
- **Health Checks**: Đã triển khai `/health` để kiểm tra sự sống và `/ready` để kiểm tra kết nối Redis/DB.
- **Graceful Shutdown**: Bắt tín hiệu `SIGTERM`, dừng nhận request mới và đợi tối đa 30s cho các request đang xử lý hoàn thành.
- **Stateless Design**: Thay thế hội thoại trong biến global sang lưu trữ trong Redis. Giúp mở rộng số lượng container chạy song song mà không mất dữ liệu người dùng.


---

### 2. Full Source Code - Lab 06 Complete (60 points)

Your final production-ready agent with all files:

```
your-repo/
├── app/
│   ├── main.py              # Main application
│   ├── config.py            # Configuration
│   ├── auth.py              # Authentication
│   ├── rate_limiter.py      # Rate limiting
│   └── cost_guard.py        # Cost protection
├── utils/
│   └── mock_llm.py          # Mock LLM (provided)
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Full stack
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
├── .dockerignore            # Docker ignore
├── railway.toml             # Railway config (or render.yaml)
└── README.md                # Setup instructions
```

**Requirements:**
-  All code runs without errors
-  Multi-stage Dockerfile (image < 500 MB)
-  API key authentication
-  Rate limiting (10 req/min)
-  Cost guard ($10/month)
-  Health + readiness checks
-  Graceful shutdown
-  Stateless design (Redis)
-  No hardcoded secrets

---

### 3. Service Domain Link

Create a file `DEPLOYMENT.md` with your deployed service information:

```markdown
# Deployment Information

## Public URL
https://your-agent.railway.app

## Platform
Railway / Render / Cloud Run

## Test Commands

### Health Check
```bash
curl https://your-agent.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://your-agent.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
```

##  Pre-Submission Checklist

- [ ] Repository is public (or instructor has access)
- [ ] `MISSION_ANSWERS.md` completed with all exercises
- [ ] `DEPLOYMENT.md` has working public URL
- [ ] All source code in `app/` directory
- [ ] `README.md` has clear setup instructions
- [ ] No `.env` file committed (only `.env.example`)
- [ ] No hardcoded secrets in code
- [ ] Public URL is accessible and working
- [ ] Screenshots included in `screenshots/` folder
- [ ] Repository has clear commit history

---

##  Self-Test

Before submitting, verify your deployment:

```bash
# 1. Health check
curl https://your-app.railway.app/health

# 2. Authentication required
curl https://your-app.railway.app/ask
# Should return 401

# 3. With API key works
curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
  -X POST -d '{"user_id":"test","question":"Hello"}'
# Should return 200

# 4. Rate limiting
for i in {1..15}; do 
  curl -H "X-API-Key: YOUR_KEY" https://your-app.railway.app/ask \
    -X POST -d '{"user_id":"test","question":"test"}'; 
done
# Should eventually return 429
```

---

##  Submission

**Submit your GitHub repository URL:**

```
https://github.com/your-username/day12-agent-deployment
```

**Deadline:** 17/4/2026

---

##  Quick Tips

1.  Test your public URL from a different device
2.  Make sure repository is public or instructor has access
3.  Include screenshots of working deployment
4.  Write clear commit messages
5.  Test all commands in DEPLOYMENT.md work
6.  No secrets in code or commit history

---

##  Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CODE_LAB.md](CODE_LAB.md)
- Ask in office hours
- Post in discussion forum

---

**Good luck! **
