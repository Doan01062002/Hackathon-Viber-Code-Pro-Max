# Frontend Task List

Tai lieu nay tong hop danh sach cong viec Frontend can lam cho SRRM MVP, dua tren task board FE da duoc chot.

## 1. Tong quan

- Tong cong viec FE trai tren `S0` den `S4`
- Pham vi gom:
- Nen tang FE
- Dashboard du bao
- Bao gia va alternatives
- Ghep doan trong
- Mo phong va phe duyet
- Canh bao
- i18n, state chung, responsive, test

## 2. Task List Theo Sprint

### Sprint S0 - Nen tang

#### Nền tảng - Khởi tạo React + layout + routing

- [ ] Khoi tao du an React
- [ ] Layout va navigation
- [ ] Routing cac trang

#### Nền tảng - Lớp api/ + React Query

- [ ] Cau hinh client HTTP + React Query
- [ ] Hook cho tung endpoint
- [ ] Xu ly loi/timeout chung

### Sprint S1 - Forecast Foundation + Auth + i18n

#### Nền tảng - Auth flow

- [ ] Trang dang nhap
- [ ] Luu JWT va gan header
- [ ] Guard route theo vai tro

#### Khối 1 - Dự báo - Component SegmentHeatmap

- [ ] Chon thu vien va dung khung heatmap
- [ ] Bind du lieu chang x thoi gian
- [ ] Thang mau va chu giai
- [ ] Tuong tac tooltip/hover
- [ ] Danh dau nut co chai

#### Khối 1 - Dự báo - Màn hình Dashboard tải chặng

- [ ] Bo cuc man hinh
- [ ] Tich hop SegmentHeatmap
- [ ] Bang tai/ti le lap day
- [ ] Bo loc tau/ngay
- [ ] Trang thai loading/empty

#### Khối 1 - Dự báo - Component ODMatrix

- [ ] Dung luoi ma tran OD
- [ ] Tooltip va test
- [ ] Form nhap OD

#### Nền tảng - i18n tiếng Việt + format

- [ ] Thiet lap i18n tieng Viet
- [ ] Format VND va ngay gio
- [ ] Ra soat chuoi

### Sprint S2 - Quote + Price Explain

#### Khối 2 - Tối ưu - Màn hình Báo giá

- [ ] Goi `/v1/quote`
- [ ] Hien thi gia va kha dung
- [ ] Hien thi alternatives
- [ ] Thiet ke card dien giai

#### Khối 3 - Định giá - Component PriceExplainCard

- [ ] Bind explanation (chi phi co hoi, nut co chai)
- [ ] Tinh chinh

### Sprint S3 - Availability + Simulation

#### Khối 2 - Tối ưu - Bảng ghép đoạn trống

- [ ] Bang danh sach doan trong
- [ ] Goi `/v1/availability`
- [ ] Hien thi de xuat OD ghep
- [ ] Viet test

#### Khối 3 - Định giá - Màn hình Mô phỏng & phê duyệt

- [ ] Man hinh chon kich ban
- [ ] Goi `/v1/simulate`
- [ ] Bang so sanh AI vs hien tai
- [ ] Nut phe duyet/ghi de
- [ ] Cap nhat policy/limits

#### Khối 3 - Định giá - Component ScenarioCompareChart

- [ ] Dung bieu do so sanh
- [ ] Bind doanh thu/san luong
- [ ] Chu giai va dinh dang
- [ ] Viet test

### Sprint S4 - Hardening + QA

#### Khối 1 - Dự báo - Màn hình Cảnh báo

- [ ] Danh sach canh bao
- [ ] Bind chang chay ve/trong cao
- [ ] Viet test

#### Nền tảng - Loading/empty/error states

- [ ] Component trang thai chung
- [ ] Ap dung cho cac man hinh
- [ ] Viet test

#### Nền tảng - Responsive + đánh bóng UX

- [ ] Responsive layout
- [ ] Tinh chinh khoang cach/typography
- [ ] Trang thai tuong tac
- [ ] Ra soat tong the

#### Kiểm chứng - Tests (React Testing Library)

- [ ] Test component heatmap
- [ ] Test form bao gia
- [ ] Test luong chinh

## 3. Gom task theo feature de code

### `frontend/src/features/auth`

- [ ] Trang dang nhap
- [ ] Luu JWT va gan header
- [ ] Guard route theo vai tro

### `frontend/src/features/dashboard`

- [ ] SegmentHeatmap
- [ ] Dashboard tai chang
- [ ] Bo loc tau/ngay
- [ ] Bang tai/ti le lap day
- [ ] ODMatrix
- [ ] Loading/empty state cho dashboard

### `frontend/src/features/quote`

- [ ] Form nhap OD
- [ ] Goi `/v1/quote`
- [ ] Hien thi gia va kha dung
- [ ] Alternatives
- [ ] PriceExplainCard

### `frontend/src/features/availability`

- [ ] Bang danh sach doan trong
- [ ] Goi `/v1/availability`
- [ ] Hien thi de xuat OD ghep

### `frontend/src/features/simulation`

- [ ] Chon kich ban
- [ ] Goi `/v1/simulate`
- [ ] Bang so sanh AI vs hien tai
- [ ] ScenarioCompareChart
- [ ] Nut phe duyet/ghi de
- [ ] Cap nhat policy/limits

### `frontend/src/features/alerts`

- [ ] Danh sach canh bao
- [ ] Bind chang chay ve/trong cao

### Shared / cross-cutting

- [ ] API layer
- [ ] React Query hooks
- [ ] Error/timeout handling
- [ ] i18n
- [ ] Format VND/ngay gio
- [ ] Loading/empty/error state components
- [ ] Responsive layout
- [ ] Interaction states

## 4. Thu tu code de vao viec nhanh

1. [ ] App shell + layout + routing
2. [ ] API layer + React Query
3. [ ] Auth
4. [ ] Dashboard + SegmentHeatmap + ODMatrix
5. [ ] Quote + PriceExplainCard
6. [ ] Availability
7. [ ] Simulation + ScenarioCompareChart
8. [ ] Alerts
9. [ ] Shared states + i18n
10. [ ] Responsive + test

## 5. Definition of Done

- [ ] Moi screen co route ro rang
- [ ] Moi screen co loading/empty/error state
- [ ] Cac form co validation co ban
- [ ] Hien thi dung format VND va ngay gio
- [ ] Responsive o muc MVP
- [ ] Co test cho heatmap, quote form, va luong chinh
- [ ] UI bam theo persona Revenue Manager va cac docs trong `docs/UI_prd/`
