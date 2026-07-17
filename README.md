<<<<<<< HEAD
# SRRM `ai-service` — phần AI (Khối 1/2/3)

Bản hiện thực chạy được của **phần AI** cho hệ thống Smart Rail Revenue Management (đường sắt Bắc–Nam, 20 ga). Bao gồm bộ sinh dữ liệu mô phỏng, ba khối AI, và FastAPI theo hợp đồng `/internal/*`.

## Cấu trúc

```
ai-service/
  ai_service/
    config.py         # 20 ga, cự ly, sức chứa, giá, hệ số (neo theo số liệu thật)
    datagen.py        # bộ sinh dữ liệu (+ thời tiết, khuyến mãi, chiều đi/về Tết)
    unconstraining.py # KHỐI 1 — EM giải kiểm duyệt cầu (censored Poisson)
    booking_curve.py  # KHỐI 1 — đường cong đặt vé + pickup theo lead time
    forecasting.py    # KHỐI 1 — LightGBM Poisson + quantile + tuning + SHAP + pinball
    optimization.py   # KHỐI 2 — DLP bid price (HiGHS) + gán ghế + ghép đoạn
    pricing.py        # KHỐI 3 — markup trên bid price + co giãn + diễn giải
    adapter.py        # ETL 21 bảng CSV -> history (+ đặc trưng mới)
    schemas.py        # hợp đồng JSON (pydantic)
    app.py            # FastAPI /internal/forecast|optimize|price
  scripts/
    eda.py            # khám phá dữ liệu + kiểm định feature set
    gen_data.py       # xuất 21 bảng seeds (CSV+JSON)
    train.py          # train 1 lần -> models/model.pkl (EM + tuning + booking curve)
    eval.py           # KHỐI 1: WAPE/OD, phủ phân vị, pinball, pickup MAPE
    eval_optimization.py  # KHỐI 2: uplift nền vs bid price
    eval_pricing.py   # KHỐI 3: quét trần surge + uplift định giá (mô phỏng WTP)
    run_pipeline.py   # demo end-to-end
  tests/
    test_unconstraining.py  # EM khôi phục λ trên tập giả lập
    test_booking_curve.py   # pickup MAPE + đơn điệu đường cong
  requirements.txt
```

## Chạy

```bash
pip install -r requirements.txt   # gồm lightgbm, shap (tự fallback nếu thiếu)

# 0) Khám phá dữ liệu + kiểm định feature set
python scripts/eda.py --from-seeds out/seeds

# 1) Demo end-to-end nhanh (sinh data -> dự báo -> bid price -> gán ghế -> định giá)
python scripts/run_pipeline.py

# 2) (Xem thử) sinh 21 bảng seeds (+ thời tiết, khuyến mãi)
python scripts/gen_data.py --days 300 --start 2024-01-01

# 3) HUẤN LUYỆN MỘT LẦN -> lưu model ra models/model.pkl  (MVP: chạy tay, chưa cần định kỳ)
python scripts/train.py                                 # tự sinh data bằng datagen
python scripts/train.py --from-seeds out/seeds --tune   # train trên 21 bảng + tuning LightGBM

# 4) Đánh giá
python scripts/eval.py --from-seeds out/seeds               # KHỐI 1: WAPE theo OD/ngày, phủ phân vị
python scripts/eval_optimization.py --from-seeds out/seeds  # KHỐI 2: uplift nền vs AI (doanh thu, ghế-km)
python scripts/eval_pricing.py                              # KHỐI 3: quét trần surge + uplift định giá (mô phỏng)

# 5) Unit test (EM unconstraining + booking curve)
python tests/test_unconstraining.py && python tests/test_booking_curve.py

# 6) Chạy API — app NẠP model đã train, KHÔNG train lúc khởi động
uvicorn ai_service.app:app --port 8100
#   POST /internal/forecast  {"service_date":"2024-02-11"}
#   POST /internal/optimize  {"service_date":"2024-02-11"}
#   POST /internal/price     {"od_id": 12, "service_date":"2024-02-11"}
```

> **Quy trình MVP:** train **một lần** bằng `scripts/train.py` (lưu `models/model.pkl`) → app chỉ nạp model để phục vụ. Khi dữ liệu thay đổi thì **chạy lại `train.py`** (thủ công). Chưa đưa train định kỳ/drift vào MVP — bước train đã tách riêng nên sau này chỉ cần bọc bằng scheduler là xong.

## Ba khối AI

**KHỐI 1 — Dự báo (`forecasting.py` + `unconstraining.py` + `booking_curve.py`)**
LightGBM hồi quy **Poisson** cho λ̂ (tự fallback HistGradientBoosting) + 3 mô hình **quantile** cho p10/p50/p90 (ép đơn điệu). Có **random-search tuning** theo time-split, **feature importance bằng SHAP**, và **pinball loss** khi đánh giá.
- *Giải kiểm duyệt (`unconstraining.py`):* **EM cho censored Poisson** — ngày hết chỗ là quan sát bị cắt (cầu thật ≥ số bán); E-step thay bằng `E[D|D≥k,λ]`, M-step cập nhật λ theo nhóm (OD × mùa). Nhãn train = cầu **đã de-censor**, không phải số bán thô.
- *Booking curve (`booking_curve.py`):* fit đường cong đặt vé tích lũy theo **lead time**, mô hình **pickup** dự phóng cầu cuối (`final = b / c(τ)`). Pickup MAPE @14 ngày ~**5%**.
- *Đặc trưng:* lịch (thứ/tháng/mùa), lễ/Tết, **chiều đi/về Tết** (`days_to_tet`, `is_pre_tet`, `is_post_tet`), **thời tiết** (`is_rainy`), **khuyến mãi** (`promo`), cự ly, giá, độ hút ga, hub, nút cổ chai.
- Kết quả backtest tiêu biểu: **WAPE tổng hợp theo OD ~5–7%**, **phủ p10–p90 ~80%**, **corr(λ̂, λ_thật) ~0.98**.

**KHỐI 2 — Tối ưu (`optimization.py`)**
- *Lớp A:* DLP `max Σ f_j x_j` với ràng buộc sức chứa từng (chặng, loại chỗ); giải bằng **scipy HiGHS**; **bid price = biến đối ngẫu**; quy tắc chấp nhận `fare ≥ Σ bid price`. Giải **~5 ms/chuyến**.
- *Lớp B:* gán ghế bằng **interval partitioning** (greedy, tối ưu — số ghế dùng = tải chồng lấn cực đại) và **ghép đoạn trống best-fit**.

**KHỐI 3 — Định giá (`pricing.py`)**
Giá = markup trên chi phí cơ hội `c_j = Σ bid price`; độ co giãn ước lượng từ dữ liệu (khử nhiễu theo OD), có **guardrail** chặn markup nổ và **trần surge** (đại diện Policy Guard). AI chỉ trả **giá thô + diễn giải**; ép trần/sàn cuối là việc của backend.

> **Đánh giá Khối 3 phải trên MÔ PHỎNG (không dùng seed):** định giá làm *thay đổi cầu* nên cần mô hình mức-sẵn-lòng-trả (WTP) để biết đổi giá thì ai còn mua — seed chỉ ghi vé đã bán, không mang WTP. `eval_pricing.py` sinh khách có WTP (nhích theo cao điểm — Tết khách trả cao & phân tán rộng), rồi cho CÙNG tập khách đối mặt 3 chính sách (nền / +Khối 2 / +Khối 3) và **quét trần surge** để lộ đường cong doanh thu hình chuông. Kết quả tiêu biểu: **ngày thường 0%** (không khan hiếm → không surge), **cao điểm doanh thu +~27%** tại trần tối ưu ~1.6× (giá TB/vé +54%, đổi bớt sản lượng lấy doanh thu); vượt ~2× thì doanh thu *tụt* → cho thấy vì sao cần **trần surge hiệu chỉnh** + Policy Guard 2.5× làm rào cứng. **Cầu nạp vào bộ tối ưu = cầu-trả-tiền tại giá gốc (bookings+soldout — đúng đầu ra Khối 1), KHÔNG phải λ đến thô**, nên ngày vắng bid price = 0 và hệ thống không tăng giá bừa.

## Kết quả demo (chuyến cao điểm Tết 2024-02-11)

```
KHỐI 1: WAPE theo OD ~5.5% | corr(λ̂, λ_thật) 0.98
KHỐI 2: DLP giải ~5 ms | bid price nút cổ chai Huế–ĐN: ngồi mềm ~89k, giường ~98k
        24–30/198 OD bị từ chối (giá < chi phí cơ hội)
        gán ghế 192/192 & 252/252 — tối ưu; tìm ~400 khoảng trống ghép được
KHỐI 3: HN→ĐN (giường, qua nút cổ chai) surge 1.55M; HN→Phủ Lý (chặng thường) giữ giá gốc 62k
```

## Ghi chú thiết kế / triển khai thật

- **ai-service stateless về nghiệp vụ.** Bản demo tự sinh data + train khi khởi động để chạy được ngay. Triển khai thật: **backend đẩy snapshot dữ liệu vào payload**, ai-service không đọc DB.
- **Ground-truth** (λ thật) do `datagen` sinh ra — để ngoài DB vận hành, dùng chấm điểm Phase 1.
- **Có thể thay** `HistGradientBoostingRegressor` bằng **LightGBM** (production); thay `scipy HiGHS` bằng **OR-Tools/Gurobi** nếu cần. Interface không đổi.
- Ánh xạ đầu ra với 21 bảng schema: `demand_forecasts` (Khối 1), `bid_prices`/`quotas` (Khối 2A), `seat`/`gap_combinations` (Khối 2B), `price_quotes` (Khối 3).
- Tham số sinh dữ liệu & mạng 20 ga: xem `Luat_Sinh_Du_Lieu_SRRM.md`.
=======
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
| `make test` | Test cả `ai` và `backend` (12 test) |
| `make lint` | ruff + ESLint |
| `make boundaries` | Kiểm tra ranh giới module |
| `make check` | Cả ba việc trên |
| `docker compose up --build` | Chạy full stack, không cần cài gì |

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
>>>>>>> origin/develop
