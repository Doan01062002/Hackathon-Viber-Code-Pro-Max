# UI Execute Plan

Tai lieu nay la task list thuc thi cho team Frontend de xay dung UI SRRM MVP theo luong ro rang, bam theo `schema.sql` va bo docs hien tai.

## 1. Muc tieu

- Dua team FE vao coding theo thu tu uu tien ro rang.
- Dam bao moi screen deu bam dung persona, luong nghiep vu, va data contract.
- Tach task theo feature folder de co the implement ngay trong `frontend/src/features/*`.

## 2. Thu tu thuc hien

1. Foundation va data contract
2. App shell va shared UI
3. Dashboard
4. Quote
5. Simulation
6. Alerts
7. Audit
8. Auth
9. API integration
10. Responsive, polish, QA

## 3. Foundation

- [ ] Doc [README.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/README.md)
- [ ] Doc [frontend_specs_mvp.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/frontend_specs_mvp.md)
- [ ] Doc [ui_ux_requirements_from_prd.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/ui_ux_requirements_from_prd.md)
- [ ] Doc [docs/prd_duong_sat.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/prd_duong_sat.md)
- [ ] Doc [docs/tasks/SRRM-004-simulation-and-ui.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/tasks/SRRM-004-simulation-and-ui.md)
- [ ] Doc [docs/specs/features.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/specs/features.md)
- [ ] Doc [docs/specs/user-roles.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/specs/user-roles.md)
- [ ] Doc [schema.sql](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/schema.sql)
- [ ] Chot persona trong tam: `Revenue Manager`
- [ ] Chot luong chinh: `Login -> Dashboard -> Quote -> Simulation -> Alerts -> Audit`

## 4. Data Contract

- [ ] Lap bang mapping `screen -> bang SQL -> field can dung`
- [ ] Chot format chung:
- [ ] `currency`: VND
- [ ] `datetime`: gio/ngay theo VN
- [ ] `status`: badge mau thong nhat
- [ ] Tao FE domain types:
- [ ] `Trip`
- [ ] `Segment`
- [ ] `SegmentInventory`
- [ ] `DemandForecast`
- [ ] `GapCombination`
- [ ] `PriceQuote`
- [ ] `AuditLog`
- [ ] Tao view model rieng cho UI, khong bind truc tiep SQL row vao component
- [ ] Tao file data contract tom tat trong feature docs neu can

## 5. Cau truc folder FE can co

```text
frontend/src/
  app/
    login/
    dashboard/
    quote/
    simulation/
    alerts/
    audit/
  components/ui/
  features/
    auth/
    dashboard/
    quote/
    simulation/
    alerts/
    audit/
  lib/api/
  lib/format/
  types/
```

## 6. App Shell

### 6.1. Routes

- [ ] Tao route `/login`
- [ ] Tao route `/dashboard`
- [ ] Tao route `/quote`
- [ ] Tao route `/simulation`
- [ ] Tao route `/alerts`
- [ ] Tao route `/audit`

### 6.2. Layout

- [ ] Tao admin layout chung
- [ ] Tao sidebar/navigation
- [ ] Tao top bar hien context tau/ngay neu can
- [ ] Tao page container dung chung
- [ ] Tao state route-level: loading, error, empty, not found

### 6.3. Guard

- [ ] Tao auth guard co ban
- [ ] Tao role gate mock cho `Revenue Manager`, `Dispatcher`, `IT Integrator`

## 7. Shared UI System

### 7.1. Shared components

- [ ] `PageHeader`
- [ ] `MetricCard`
- [ ] `FilterBar`
- [ ] `StatusBadge`
- [ ] `DataTable`
- [ ] `EmptyState`
- [ ] `ErrorState`
- [ ] `LoadingSkeleton`
- [ ] `ChartCard`
- [ ] `ConfirmActionDialog`

### 7.2. Shared utilities

- [ ] Format VND
- [ ] Format percent
- [ ] Format date/time
- [ ] Map muc do canh bao sang mau
- [ ] Map role sang label hien thi

## 8. Mock Data Bam Theo SQL

### 8.1. Dashboard mock

- [ ] Tao mock tu `trips`
- [ ] Tao mock tu `segments`
- [ ] Tao mock tu `segment_inventory`
- [ ] Tao mock tu `segment_capacities`
- [ ] Tao mock tu `demand_forecasts`
- [ ] Tao mock tu `gap_combinations`

### 8.2. Quote mock

- [ ] Tao mock tu `od_products`
- [ ] Tao mock tu `od_product_segments`
- [ ] Tao mock tu `bid_prices`
- [ ] Tao mock tu `price_policies`
- [ ] Tao mock tu `price_quotes`

### 8.3. Simulation mock

- [ ] Tao mock tu `price_policies`
- [ ] Tao mock tu `bookings`
- [ ] Tao mock tu `price_quotes`
- [ ] Tao mock so sanh AI vs hien tai

### 8.4. Alerts mock

- [ ] Tao mock tu `segment_inventory`
- [ ] Tao mock tu `demand_forecasts`

### 8.5. Audit mock

- [ ] Tao mock tu `audit_logs`

## 9. Feature `auth`

Folder de tao:

```text
frontend/src/features/auth/
  api/
  components/
  hooks/
  mocks/
  types.ts
  index.ts
```

Task:

- [ ] Tao `LoginForm`
- [ ] Tao state login loading/error
- [ ] Tao mock role va user session
- [ ] Tao redirect sau login
- [ ] Tao route protection co ban

## 10. Feature `dashboard`

Folder de tao:

```text
frontend/src/features/dashboard/
  api/
  components/
  hooks/
  mocks/
  types.ts
  index.ts
```

Components can co:

- [ ] `DashboardPageView`
- [ ] `DashboardFilters`
- [ ] `SegmentHeatmap`
- [ ] `BookingCurveChart`
- [ ] `LoadSummaryCards`
- [ ] `GapSuggestionTable`
- [ ] `ODMatrixPanel` hoac placeholder neu lam sau

Task:

- [ ] Dung layout tong dashboard
- [ ] Ve heatmap tai chang
- [ ] Ve booking curve
- [ ] Hien KPI cards
- [ ] Hien danh sach gap suggestions
- [ ] Them bo loc tau/ngay/seat type
- [ ] Hoan thien loading/empty/error state

Data SQL lien quan:

- [ ] `trips`
- [ ] `segments`
- [ ] `segment_inventory`
- [ ] `segment_capacities`
- [ ] `demand_forecasts`
- [ ] `gap_combinations`

## 11. Feature `quote`

Folder de tao:

```text
frontend/src/features/quote/
  api/
  components/
  hooks/
  mocks/
  types.ts
  index.ts
```

Components can co:

- [ ] `QuoteForm`
- [ ] `QuoteResultCard`
- [ ] `AlternativeList`
- [ ] `PriceExplainCard`

Task:

- [ ] Dung form nhap OD
- [ ] Hien ket qua gia
- [ ] Hien alternatives
- [ ] Hien explanation cho gia
- [ ] Hoan thien validate co ban
- [ ] Hoan thien loading/empty/error state

Data SQL lien quan:

- [ ] `od_products`
- [ ] `od_product_segments`
- [ ] `bid_prices`
- [ ] `price_policies`
- [ ] `price_quotes`

## 12. Feature `simulation`

Folder de tao:

```text
frontend/src/features/simulation/
  api/
  components/
  hooks/
  mocks/
  types.ts
  index.ts
```

Components can co:

- [ ] `SimulationWorkspace`
- [ ] `ScenarioPicker`
- [ ] `ScenarioCompareChart`
- [ ] `SimulationSummaryTable`
- [ ] `ApprovalActions`

Task:

- [ ] Dung layout workspace mo phong
- [ ] Tao so sanh AI vs hien tai
- [ ] Tao chart doanh thu/san luong
- [ ] Tao hanh dong phe duyet/ghi de
- [ ] Them canh bao cho action nhay cam
- [ ] Hoan thien loading/empty/error state

Data SQL lien quan:

- [ ] `price_policies`
- [ ] `price_quotes`
- [ ] `bookings`
- [ ] `demand_forecasts`
- [ ] `audit_logs` cho hanh dong phe duyet neu can

## 13. Feature `alerts`

Folder de tao:

```text
frontend/src/features/alerts/
  api/
  components/
  hooks/
  mocks/
  types.ts
  index.ts
```

Components can co:

- [ ] `AlertList`
- [ ] `AlertFilters`
- [ ] `AlertSeverityBadge`

Task:

- [ ] Hien danh sach canh bao chang sap chay ve
- [ ] Hien danh sach canh bao chang trong cao
- [ ] Them bo loc theo loai/muc do
- [ ] Hoan thien loading/empty/error state

Data SQL lien quan:

- [ ] `segment_inventory`
- [ ] `demand_forecasts`

## 14. Feature `audit`

Folder de tao:

```text
frontend/src/features/audit/
  api/
  components/
  hooks/
  mocks/
  types.ts
  index.ts
```

Components can co:

- [ ] `AuditLogTable`
- [ ] `AuditFilters`
- [ ] `AuditDetailDrawer`

Task:

- [ ] Hien actor, action, entity, time
- [ ] Xem `before_data` va `after_data`
- [ ] Loc theo actor/action/date
- [ ] Hoan thien loading/empty/error state

Data SQL lien quan:

- [ ] `audit_logs`

## 15. API Integration

### 15.1. API modules

- [ ] Tao `dashboard/api`
- [ ] Tao `quote/api`
- [ ] Tao `simulation/api`
- [ ] Tao `alerts/api`
- [ ] Tao `audit/api`
- [ ] Tao `auth/api`

### 15.2. Hooks

- [ ] Hook fetch danh sach/dashboard summary
- [ ] Hook fetch quote
- [ ] Hook run simulation
- [ ] Hook fetch alerts
- [ ] Hook fetch audit logs
- [ ] Hook login/session

### 15.3. Chuyen mock sang API that

- [ ] Giu mock de demo truoc
- [ ] Thay tung screen bang API that khi backend san sang
- [ ] Khong goi HTTP truc tiep trong page/component

## 16. Responsive va Polish

- [ ] Chot desktop-first
- [ ] Toi uu tablet
- [ ] Toi uu mobile co ban cho dashboard, quote, alerts
- [ ] Chinh spacing va typography
- [ ] Chinh tooltip, hover, focus, disabled
- [ ] Ra soat text tieng Viet toan bo

## 17. QA

- [ ] Test luong `login -> dashboard`
- [ ] Test luong `dashboard -> quote`
- [ ] Test luong `simulation -> phe duyet/ghi de`
- [ ] Test luong `alerts`
- [ ] Test luong `audit`
- [ ] Test loading/empty/error tung screen
- [ ] Test voi mock data thieu field
- [ ] Test responsive

## 18. Definition of Done cho UI MVP

- [ ] Co app shell va route day du
- [ ] Dashboard chay duoc voi mock data giong schema SQL
- [ ] Quote chay duoc voi ket qua va explanation
- [ ] Simulation co so sanh AI vs hien tai va action phe duyet
- [ ] Alerts hien thi duoc theo nguong
- [ ] Audit xem duoc lich su thay doi
- [ ] Tat ca screen co loading/empty/error
- [ ] Giao dien tieng Viet va doc duoc tren desktop/mobile co ban

## 19. Thu tu bat tay code ngay

1. [ ] Tao app shell va routes
2. [ ] Tao shared components
3. [ ] Tao feature `dashboard` voi mock data
4. [ ] Tao feature `quote`
5. [ ] Tao feature `simulation`
6. [ ] Tao feature `alerts`
7. [ ] Tao feature `audit`
8. [ ] Ghep API layer
9. [ ] Polish va QA
