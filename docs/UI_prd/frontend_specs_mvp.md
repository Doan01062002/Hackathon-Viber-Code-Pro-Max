# Frontend Specs - SRRM MVP

## 1. Muc tieu

Tai lieu nay tong hop va chuan hoa toan bo cong viec Frontend (FE) tu task board `Task_Board_Duong_sat_MVP.xlsx` thanh 1 file specs de team FE co the trien khai theo sprint.

Pham vi:

- Gom backlog FE cua MVP thanh cac nhom cong viec co uu tien, phu thuoc, dau ra.
- Mapping man hinh, component, luong du lieu, va API can dung.
- Chot cac quy uoc kien truc FE theo repo hien tai.
- Xac dinh checklist ban giao va tieu chi hoan thanh.

Khong bao gom:

- Chi tiet thuat toan AI.
- Mo ta nghiep vu backend o muc implementation.
- Thiet ke UI pixel-perfect.

## 2. Hien trang repo

Frontend hien tai da co:

- Nen tang `Next.js 14 App Router + TypeScript`.
- Cau truc `app/`, `features/`, `components/ui/`, `lib/api/`.
- 1 feature mau la `chat`.
- 1 HTTP client dung chung tai `frontend/src/lib/api/client.ts`.

Frontend hien tai chua co:

- React Query.
- Auth flow va route guard.
- Cac man hinh nghiep vu SRRM.
- State/loading/empty/error chung.
- Test tu dong cho frontend.
- i18n, responsive polish, dashboard/data visualization.

Nhan xet:

- Repo da dung huong cho FE mo rong theo feature.
- Can giu nguyen quy tac: route chi lap rap, logic nam trong `features/*`, va moi HTTP call di qua `lib/api/`.

## 3. Nguyen tac kien truc FE

Team FE can giu cac quy tac sau:

1. Khong goi `fetch()` truc tiep trong page hay component.
2. Moi request di qua `frontend/src/lib/api/`.
3. Moi nghiep vu la 1 feature rieng trong `frontend/src/features/<feature-name>/`.
4. `app/*` chi dung de lap rap route va layout.
5. Component dung chung dua vao `components/ui/`.
6. Types va mapping response phai dat gan feature su dung no.
7. Man hinh phai co du 4 trang thai: loading, empty, error, success.

De xuat cau truc feature:

```text
frontend/src/features/<feature-name>/
  api/
  components/
  hooks/
  types.ts
  index.ts
```

## 4. Tong quan backlog FE

Tong cong theo task board:

- 58 task FE.
- Tong uoc tinh 57 gio.
- Trai tren 5 sprint: `S0` den `S4`.

Nhom cong viec chinh:

1. Nen tang va ha tang FE.
2. Dashboard du bao tai chang.
3. Bao gia va giai thich gia.
4. Ghep doan trong va mo phong phe duyet.
5. Canh bao, polish UX, test, va responsive.

## 5. Muc tieu san pham FE cua MVP

FE MVP can cung cap cac man hinh/chuc nang sau:

1. Trang dang nhap va xu ly phien dang nhap.
2. Dashboard tai chang voi heatmap, bang tai, va bo loc.
3. Ma tran OD de xem nhu cau theo cap ga.
4. Man hinh bao gia co alternatives.
5. Card giai thich gia de hien logic AI theo cach de hieu.
6. Bang doan trong va de xuat ghep OD.
7. Man hinh mo phong va phe duyet kich ban gia.
8. Man hinh canh bao.
9. Bo component trang thai chung, i18n, responsive, va test.

## 6. Workstreams chi tiet

### 6.1. Nen tang FE va shell ung dung

Muc tieu:

- Dung bo khung app de co the mo rong nhanh theo feature.
- Chot navigation, routing, API layer, va state management co the tai su dung.

Cong viec:

- `FE-01.1` Khoi tao du an React.
- `FE-01.2` Layout va navigation.
- `FE-01.3` Routing cac trang.
- `FE-02.1` Cau hinh client HTTP va React Query.
- `FE-02.2` Tao hook cho tung endpoint.
- `FE-02.3` Xu ly loi va timeout chung.

Dau ra bat buoc:

- App shell co sidebar/top nav hoac navigation toi thieu cho MVP.
- Danh sach route co san cho cac man hinh nghiep vu.
- 1 lop API chung ho tro base URL, auth header, timeout, parse loi.
- 1 convention cho query/mutation hook.

Ghi chu implementation:

- Repo hien chua co React Query, can bo sung neu team muon dung dung theo task board.
- Neu can toi gian MVP, co the implement API layer truoc, sau do them React Query o cung cau truc hook.

### 6.2. Auth flow

Muc tieu:

- Cho phep nguoi dung dang nhap va truy cap man hinh theo vai tro.

Cong viec:

- `FE-03.1` Trang dang nhap.
- `FE-03.2` Luu JWT va gan header.
- `FE-03.3` Guard route theo vai tro.

Phu thuoc:

- Backend `BE-04`.

Dau ra bat buoc:

- Form dang nhap.
- Co che luu token an toan o phia client theo chien luoc team chon.
- Guard route cho cac vai tro toi thieu neu backend da cung cap role.

Rui ro can chot som:

- Cach backend tra token.
- Co refresh token hay khong.
- Danh sach role va route nao can chan.

### 6.3. Khoi 1 - Du bao

#### A. Component SegmentHeatmap

Cong viec:

- `FE-04.1` Chon thu vien va dung khung heatmap.
- `FE-04.2` Bind du lieu chang x thoi gian.
- `FE-04.3` Thang mau va chu giai.
- `FE-04.4` Tooltip/hover.
- `FE-04.5` Danh dau nut co chai.

Dau ra:

- 1 component heatmap dung lai duoc.
- Nhan props ro rang cho data, labels, highlight, tooltip.

#### B. Man hinh Dashboard tai chang

Cong viec:

- `FE-05.1` Bo cuc man hinh.
- `FE-05.2` Tich hop `SegmentHeatmap`.
- `FE-05.3` Bang tai/ti le lap day.
- `FE-05.4` Bo loc tau/ngay.
- `FE-05.5` Loading/empty.

Phu thuoc:

- `FE-04.*`
- Backend `BE-06`

Dau ra:

- 1 dashboard tong quan tai chang co bo loc.
- Heatmap + bang summary + trang thai tai du lieu.

#### C. Component ODMatrix

Cong viec:

- `FE-06.1` Dung luoi ma tran OD.
- `FE-06.2` Bind du lieu va mau.
- `FE-06.3` Tooltip va test.

Dau ra:

- 1 component matrix cho nhu cau theo cap OD.

### 6.4. Khoi 2 - Toi uu

#### A. Man hinh Bao gia

Cong viec:

- `FE-07.1` Form nhap OD.
- `FE-07.2` Goi `/v1/quote`.
- `FE-07.3` Hien thi gia va kha dung.
- `FE-07.4` Hien thi alternatives.

Phu thuoc:

- Backend `BE-07`

Dau ra:

- Form input nguoi dung nhap OD, ngay, va cac tham so lien quan.
- Vung ket qua hien gia khuyen nghi, suc chua, va lua chon thay the.

#### B. Bang ghep doan trong

Cong viec:

- `FE-09.1` Bang danh sach doan trong.
- `FE-09.2` Goi `/v1/availability`.
- `FE-09.3` Hien thi de xuat OD ghep.
- `FE-09.4` Viet test.

Phu thuoc:

- Backend `BE-09`

Dau ra:

- Bang co filter/sort toi thieu.
- Co the nhin thay cung luc doan trong va de xuat ghep.

### 6.5. Khoi 3 - Dinh gia

#### A. Component PriceExplainCard

Cong viec:

- `FE-08.1` Thiet ke card dien giai.
- `FE-08.2` Bind explanation.
- `FE-08.3` Tinh chinh.

Dau ra:

- 1 card tom tat ly do AI dua ra gia.
- Phai doc duoc voi nguoi dung nghiep vu, tranh ngon ngu qua ky thuat.

#### B. Man hinh Mo phong va phe duyet

Cong viec:

- `FE-10.1` Chon kich ban.
- `FE-10.2` Goi `/v1/simulate`.
- `FE-10.3` Bang so sanh AI vs hien tai.
- `FE-10.4` Nut phe duyet/ghi de.
- `FE-10.5` Cap nhat policy/limits.

Phu thuoc:

- Backend `BE-14`

Dau ra:

- Man hinh cho phep so sanh truoc va sau.
- Hanh dong phe duyet ro rang, co canh bao khi ghi de.

#### C. Component ScenarioCompareChart

Cong viec:

- `FE-11.1` Dung bieu do so sanh.
- `FE-11.2` Bind doanh thu/san luong.
- `FE-11.3` Chu giai va dinh dang.
- `FE-11.4` Viet test.

Dau ra:

- Bieu do phuc vu quyet dinh, khong chi de minh hoa.

### 6.6. Alerting, i18n, UX polish, test

Cong viec:

- `FE-12.1` `FE-12.3`: Man hinh canh bao.
- `FE-13.1` `FE-13.3`: i18n tieng Viet, format VND, ngay gio, ra soat chuoi.
- `FE-14.1` `FE-14.3`: Loading/empty/error states dung chung va test.
- `FE-15.1` `FE-15.4`: Responsive va polish UX.
- `FE-16.1` `FE-16.3`: Test component heatmap, form bao gia, va luong chinh.

Dau ra:

- Tat ca man hinh co format VND va ngay gio thong nhat.
- Responsive cho desktop va tablet/mobile co ban.
- Co bo test bao ve luong quan trong.

## 7. Ke hoach theo sprint

### Sprint S0 - Nen tang

Pham vi:

- `FE-01.*`
- `FE-02.*`

Definition of done:

- Chay duoc shell app.
- Da co routing co ban.
- Da co API layer va convention hook.

### Sprint S1 - Forecast foundation

Pham vi:

- `FE-03.*`
- `FE-04.*`
- `FE-05.*`
- `FE-06.*`
- `FE-13.*`

Definition of done:

- Dang nhap co ban hoat dong neu backend san sang.
- Dashboard tai chang va OD matrix hien du lieu that.
- Chuoi text va format tieng Viet thong nhat.

### Sprint S2 - Quote va explain

Pham vi:

- `FE-07.*`
- `FE-08.*`

Definition of done:

- Luong bao gia hoan chinh tu form den ket qua.
- Gia duoc giai thich bang card de hieu.

### Sprint S3 - Optimize va approve

Pham vi:

- `FE-09.*`
- `FE-10.*`
- `FE-11.*`

Definition of done:

- Nhin thay doan trong, de xuat ghep, mo phong, va so sanh kich ban.
- Hanh dong phe duyet/ghi de ro luong va co feedback.

### Sprint S4 - Hardening

Pham vi:

- `FE-12.*`
- `FE-14.*`
- `FE-15.*`
- `FE-16.*`

Definition of done:

- Alert screen hoat dong.
- Tat ca man hinh quan trong co loading/empty/error.
- Responsive dat muc MVP.
- Test bao ve luong chinh.

## 8. Mapping man hinh - component - API

| Man hinh / Feature | Component chinh | API/Phu thuoc |
|---|---|---|
| Dang nhap | `LoginForm`, `AuthGuard` | `BE-04` |
| Dashboard tai chang | `SegmentHeatmap`, `LoadTable`, `TrainDayFilter` | `BE-06` |
| OD Matrix | `ODMatrix` | data tu khoi du bao |
| Bao gia | `QuoteForm`, `QuoteResult`, `AlternativeList` | `/v1/quote`, `BE-07` |
| Giai thich gia | `PriceExplainCard` | response quote/explain |
| Ghep doan trong | `AvailabilityTable`, `SuggestedODList` | `/v1/availability`, `BE-09` |
| Mo phong va phe duyet | `ScenarioPicker`, `ScenarioCompareChart`, `ApprovalActions` | `/v1/simulate`, `BE-14` |
| Canh bao | `AlertList` | `BE-06` hoac API canh bao tuong ung |

## 9. De xuat thu vien FE

Can chot som:

- Data fetching: React Query.
- Form: co the dung native React truoc, hoac them `react-hook-form` neu nhieu form.
- Visualization:
  - Heatmap / matrix: uu tien thu vien de control duoc tooltip va color scale.
  - Chart compare: uu tien thu vien nhe, de format du lieu kinh doanh.

Tieu chi chon:

- De custom theo nghiep vu.
- Hien thi tot voi du lieu bang/ma tran.
- Khong qua nang cho MVP.

## 10. Tieu chi hoan thanh FE MVP

FE duoc xem la dat MVP khi:

1. Nguoi dung dang nhap duoc va vao dung man hinh theo vai tro.
2. Dashboard du bao hien thi du lieu va bo loc dung.
3. Luong bao gia tra ket qua va alternatives.
4. Co card giai thich gia de business hieu duoc.
5. Co bang doan trong va de xuat ghep.
6. Co man hinh mo phong, so sanh, va phe duyet.
7. Tat ca man hinh chinh co loading, empty, error.
8. Giao dien doc duoc tren desktop va mobile co ban.
9. Co test cho cac luong FE quan trong.

## 11. Gap analysis voi repo hien tai

So voi specs nay, repo hien tai moi dat:

- Khung `Next.js` va bo cuc feature-based.
- API client co ban.
- Mau cho 1 feature (`chat`).

Nhung phan can lam tiep ngay:

1. Doi shell app tu chat demo sang SRRM shell.
2. Them routing cho cac man hinh MVP.
3. Them API layer theo endpoint nghiep vu.
4. Dung bo component/data viz cho dashboard va quote.
5. Them auth, loading states, test, va responsive.

## 12. Thu tu uu tien de vao viec nhanh

Neu team muon co demo som, nen lam theo thu tu nay:

1. Shell app + routing + API layer.
2. Dashboard tai chang.
3. Bao gia + PriceExplainCard.
4. Mo phong/phe duyet.
5. Alert + responsive + test hardening.

## 13. Ghi chu nguon goc

Tai lieu nay duoc tong hop tu:

- `Task_Board_Duong_sat_MVP.xlsx`
- `Task_Board_Duong_sat_MVP__1_Task Board.csv`
- `README.md`
- `ARCHITECTURE.md`
- Cau truc hien tai trong `frontend/src`
