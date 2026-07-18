# 🤖 Viber Coding Pro Max

Khung dự án AI Agent chia thành **3 module độc lập** — `ai/` (LangGraph), `backend/`
(FastAPI theo MVC), `frontend/` (Next.js 14). Ranh giới giữa chúng được kiểm tra tự
động, nên cấu trúc không rã ra khi dự án lớn dần.

> ⚠️ **Đây là khung, chưa phải sản phẩm.** Agent hiện trả về chuỗi mẫu, **chưa gọi LLM**.
> Toàn bộ đường đi đã thông và có test — bạn chỉ cần thay phần lõi.
> Xem [Bạn cần làm gì tiếp](#-bạn-cần-làm-gì-tiếp).

## ⚡ Chạy thử trong 2 phút

```bash
# 1. Cài đặt
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt      # ai + backend
cd frontend && npm install && cd ..  # frontend

# 2. Chạy
make run       # Terminal 1 — backend  http://localhost:8000/docs
make run-fe    # Terminal 2 — frontend http://localhost:3000/chat
```

Hoặc gọn hơn: `bash scripts/setup.sh` làm cả hai bước cài đặt.
Hoặc không cài gì cả: `docker compose up --build`.

Chưa cần `.env` hay API key — agent mẫu chạy được ngay.

## 🧭 Hệ thống hiện làm được gì

| Thành phần | Trạng thái |
|---|---|
| `POST /api/v1/chat` → agent → trả lời hiện trên UI | ✅ chạy suốt, có test |
| Giao diện chat (gửi tin, hiện lỗi, trạng thái loading) | ✅ |
| `GET /health`, `GET /api/v1/status` | ✅ |
| Ranh giới module được CI chặn | ✅ |
| Docker cho cả 2 service | ✅ |
| **Agent gọi LLM thật** | ❌ chưa — trả chuỗi mẫu |
| **Tools (`search_knowledge`, `calculate`) gắn vào agent** | ❌ code có sẵn, chưa nối vào graph |
| **Database / Vector store** | ❌ mới chỉ có config, chưa có code |
| Test tự động cho frontend | ❌ mới có typecheck + lint + build |

## 📁 Cấu trúc

Ranh giới giữa 3 module được kiểm tra bằng `make boundaries` — chi tiết ở
[ARCHITECTURE.md](docs/ARCHITECTURE.md).

```
├── ai/                       # 🧠 LangGraph agent — KHÔNG biết gì về HTTP
│   ├── src/ai/
│   │   ├── __init__.py       #    ⭐ interface công khai: run_agent()
│   │   ├── graph.py          #    State graph (nodes + edges)
│   │   ├── state.py          #    State schema (TypedDict)
│   │   ├── llm.py            #    LLM client — CHƯA được node nào gọi
│   │   ├── config.py         #    Config LLM + vector store
│   │   ├── nodes/            #    Node functions
│   │   └── tools/            #    Agent tools — CHƯA gắn vào graph
│   ├── tests/                #    6 test
│   └── pyproject.toml
│
├── backend/                  # 🌐 FastAPI theo MVC
│   ├── src/backend/
│   │   ├── controllers/      #    C — router: nhận HTTP, gọi service
│   │   ├── models/           #    M — domain model + request schema
│   │   ├── views/            #    V — response schema (response_model)
│   │   ├── services/         #    Nghiệp vụ — nơi DUY NHẤT import ai
│   │   ├── config.py         #    Config app + CORS + database
│   │   └── main.py           #    App factory
│   ├── tests/                #    6 test
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/                 # 💻 Next.js 14 App Router — chia theo feature
│   ├── src/
│   │   ├── app/              #    Routes — chỉ lắp ráp, không chứa logic
│   │   ├── features/chat/    #    Trọn vẹn 1 feature: components + hooks + api + types
│   │   ├── components/ui/    #    Design system dùng chung
│   │   ├── lib/api/          #    HTTP client — chỗ duy nhất gọi fetch()
│   │   └── hooks/  types/    #    Dùng chung nhiều feature
│   ├── Dockerfile
│   └── package.json
│
├── scripts/
│   ├── check_boundaries.sh   #    ⭐ Chặn vi phạm ranh giới module
│   └── setup.sh              #    Dựng venv + npm install + .env
│
├── docs/                     # 📚 Kiến trúc, schema, specs, ADRs, planning, tasks
├── .github/workflows/ci.yml  # ⚡ CI: ai + backend + frontend + boundaries
├── docker-compose.yml        # 🐙 backend:8000 + frontend:3000
└── Makefile                  # make run / run-fe / test / lint / boundaries
```

<details>
<summary><b>Tại sao có <code>backend/src/backend/</code> và <code>ai/src/ai/</code>?</b></summary>

Hai chữ trùng nhau là hai thứ khác nhau: lớp ngoài (`backend/`) là *thư mục module*,
chứa `pyproject.toml`, `Dockerfile`, `tests/`. Lớp trong (`src/backend/`) là *package
Python* — chính là thứ `import backend` trỏ tới, và tên import bắt buộc phải là tên
một thư mục.

Còn `src/` ở giữa là [src-layout chuẩn PyPA](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/):
nhờ nó, thư mục hiện tại không chứa package, nên `pytest` luôn chạy trên package **đã
cài** thay vì thư mục local. Thiếu file trong bản đóng gói sẽ lộ ra ngay lúc test,
thay vì đợi tới khi deploy mới phát hiện.

`frontend/` không có kiểu lặp này vì TypeScript dùng alias `@/*` → `./src/*`.
</details>

## 🚧 Quy tắc phụ thuộc

```
frontend  ──HTTP──▶  backend  ──import──▶  ai
                        ▲                   │
                        └────── CẤM ────────┘
```

- **`ai` không được import `backend`** — agent phải dùng được ngoài HTTP (notebook, CLI, batch job).
- **Chỉ `backend/services/` được import `ai`** — controller không chạm thẳng vào agent.
- **FE chỉ gọi HTTP qua `lib/api/`** — không `fetch()` rải rác trong component.

`make boundaries` kiểm tra cả ba. CI chạy nó và fail build nếu vi phạm — quy ước không
có gì cưỡng chế thì sớm muộn cũng bị phá.

## 🎯 Bạn cần làm gì tiếp

Thứ tự đề xuất, từ việc đổi ít code nhất:

**1. Cho agent gọi LLM thật.** [ai/src/ai/llm.py](ai/src/ai/llm.py) đã có `get_llm()`
sẵn sàng nhưng chưa ai gọi. Sửa [nodes/example_node.py](ai/src/ai/nodes/example_node.py)
để dùng nó thay cho chuỗi ghép cứng. Lúc này mới cần `OPENAI_API_KEY` trong `.env`.

**2. Gắn tools vào graph.** [tools/example_tool.py](ai/src/ai/tools/example_tool.py) có
`calculate` (parse AST, an toàn, không dùng `eval`) và `search_knowledge` (còn là mẫu).
Bind chúng vào LLM trong [graph.py](ai/src/ai/graph.py).

**3. Đổi tên dự án.** "Viber Coding Pro Max" đang nằm ở 4 chỗ:
[backend/config.py](backend/src/backend/config.py), [layout.tsx](frontend/src/app/layout.tsx),
[page.tsx](frontend/src/app/page.tsx), và `LANGCHAIN_PROJECT` trong `.env.example`.

**4. Thêm feature FE mới.** Tạo `frontend/src/features/<tên>/` theo đúng khuôn của
`features/chat/` — không đụng gì tới phần còn lại.

Điều quan trọng: mọi thay đổi trên đều **nằm gọn trong một module**. Đổi lõi agent
không phải sửa backend; đổi giao diện không phải sửa agent.

## 🔧 Lệnh hay dùng

| Lệnh | Việc |
|---|---|
| `make run` / `make run-fe` | Chạy backend / frontend |
| `make test` | Test toàn bộ `ai` và `backend` |
| `make lint` | ruff + ESLint |
| `make boundaries` | Kiểm tra ranh giới module |
| `make check` | Cả ba việc trên |
| `docker compose up --build` | Chạy full stack, không cần cài gì |

Backend integration tests dùng PostgreSQL thật về mặt tính năng SQL, nhưng luôn chạy
trên database test cô lập. GitHub Actions tự dựng PostgreSQL tạm, nạp `schema.sql` và
fixture xác định; không kết nối RDS. Khi chạy local, xem phần kiểm thử trong
[`docs/AWS_RDS_POSTGRES_SETUP.md`](docs/AWS_RDS_POSTGRES_SETUP.md).

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| AI Agent | LangGraph + LangChain |
| Backend | FastAPI + Uvicorn, bố cục MVC |
| LLM | OpenAI GPT-4o-mini *(cấu hình sẵn, chưa nối vào agent)* |
| Frontend | Next.js 14 App Router + TypeScript |
| DevOps | Docker + GitHub Actions |
| Testing | pytest + pytest-asyncio |

## 📊 AI logging and Trace Agent (LangSmith)

Agent application logs are enabled by default and written to stdout as JSON. Configure them
in `.env`:

```bash
AI_LOG_LEVEL=INFO       # DEBUG, INFO, WARNING, ERROR, CRITICAL
AI_LOG_FORMAT=json      # json for production, text for local development
```

Every `run_agent()` call gets a `run_id` and emits start, completion, or failure events with
its processing time. Query and prompt content is never logged; only query length is included
for diagnostics without exposing user data.

Khi agent trả kết quả lạ, trace cho thấy từng node chạy gì và LLM nhận prompt nào.
Bật bằng 3 biến trong `.env`:

```bash
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=viber-coding-pro-max
LANGCHAIN_TRACING_V2=true
```

LangChain tự đọc các biến này, không cần sửa code. Bỏ trống `LANGCHAIN_TRACING_V2`
nếu không muốn gửi trace đi đâu cả.

## 📄 License

MIT
