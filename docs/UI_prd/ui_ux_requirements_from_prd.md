# UI/UX Requirements Extracted from `prd_duong_sat.md`

## 1. Muc tieu UI/UX

Day la phan loc rieng cac yeu cau lien quan den giao dien, trai nghiem nguoi dung, man hinh, dashboard, canh bao, va kha nang thao tac duoc neu trong `prd_duong_sat.md`.

## 2. Nguoi dung trong tam

### Persona chinh

- **Quan ly dieu ve / Revenue Manager**
  - Nhu cau: nhin tai chang, du bao, doanh thu du kien.
  - Hanh dong: phe duyet, dieu chinh de xuat, mo phong chinh sach.
  - Giao dien can: dashboard, mo phong, phe duyet.

### Persona phu

- **Dieu do / Ke hoach chay tau**
  - Nhu cau: cap nhat thay doi doan tau, suc chua, ghe khoa/uu tien.
  - Giao dien can: form nhap cau hinh tau, canh bao.

- **Bo phan CNTT / Tich hop**
  - Nhu cau: API on dinh, log kiem toan, phan quyen, rollback.
  - Giao dien lien quan: quan tri he thong, giam sat, audit.

- **Ban giam khao / Lanh dao**
  - Nhu cau: xem bao cao so sanh AI vs thuc te.
  - Giao dien can: man hinh tong hop KPI, dashboard bao cao.

## 3. Yeu cau UI/UX truc tiep tu PRD

### 3.1. Dashboard va truc quan du lieu

- Can co **heatmap tai theo chang** de nguoi quan ly nhan dien nhanh:
  - chang sap chay ve
  - chang trong nhieu
  - chang "nut co chai"

- Can co **bang so lieu day du theo tung chang**, gom:
  - suc chua
  - so ghe ban/giu/trong
  - ti le lap day
  - du bao
  - thieu/thua ghe
  - gia trung binh
  - doanh thu du kien
  - ghe trong do phan bo chua toi uu

- Can co **dashboard cho quan ly** gom:
  - heatmap tai chang
  - ma tran ga di - ga den
  - bieu do toc do ban va du bao
  - bang doan trong co the ghep

- Dieu kien thanh cong UI:
  - Quan ly xac dinh duoc nut co chai trong **<= 1 thao tac**.
  - Dashboard hien thi dung theo **tau/ngay duoc chon**.

### 3.2. Man hinh mo phong va phe duyet

- Can co **man hinh mo phong & phe duyet** cho phep:
  - dieu chinh han ngach
  - mo phong gia
  - so sanh doanh thu/san luong AI vs chinh sach hien tai
  - phe duyet hoac ghi de thu cong truoc khi ap dung

- Yeu cau UX:
  - nguoi dung phai xem duoc **so sanh truoc/sau**
  - co kha nang **can thiep/ghi de thu cong**
  - co **log thay doi** de truy vet

### 3.3. Canh bao

- Can co **canh bao chang sap chay ve hoac trong cao**.
- Canh bao hien thi theo **nguong cau hinh**.
- Trong cac truong hop goi y ghep hanh trinh co doi cho:
  - chi hien thi khi thoa dieu kien
  - phai **canh bao ro**
  - giam thieu so lan doi cho

### 3.4. Giai thich va minh bach

- Moi de xuat gia can co **dien giai ly do**, it nhat gom:
  - chi phi co hoi chang
  - tai
  - thoi diem

- UX can dam bao:
  - AI **giai thich duoc**
  - Quan ly **xem duoc dien giai** cho tung muc gia
  - He thong minh bach, de giai trinh

### 3.5. Ngon ngu va dia phuong hoa

- **Giao dien nguoi dung bang tieng Viet**.

Dieu nay anh huong den:

- toan bo label, title, table header, filter, thong bao
- format ngay gio
- cach dien dat phu hop ngu canh nghiep vu duong sat

### 3.6. Thao tac va hieu nang trai nghiem

- He thong can van hanh **gan thoi gian thuc**.
- Cac man hinh dashboard, mo phong, canh bao can phan hoi nhanh du de ho tro ra quyet dinh.

Tac dong den UX:

- uu tien loading state ro rang
- tranh block giao dien qua lau
- cac thao tac tinh toan lai can co feedback ro

### 3.7. Phan quyen, audit, va thao tac thu cong

- Can **phan quyen theo vai tro (RBAC)**.
- Can co **nhat ky kiem toan day du**.
- Can ho tro **rollback** ve chinh sach truoc.
- Can cho phep **can thiep/ghi de thu cong** cua quan ly.

Tac dong den UI:

- route/man hinh theo vai tro
- action nhay cam can xac nhan ro
- can co lich su thay doi, nguoi thuc hien, thoi diem

## 4. Luong nghiep vu can phan anh tren UI

### 4.1. Luong quan tri doanh thu

1. Xem du bao OD va heatmap tai chang.
2. Xem han ngach va bid price.
3. Xem de xuat gia.
4. Theo doi ban/huy de cap nhat du bao.

UI can ho tro luong nay thanh cac man hinh/lop thong tin lien mach, khong roi rac.

### 4.2. Luong ra quyet dinh tren 1 yeu cau ve

1. Nhan yeu cau OD.
2. So gia ve voi tong bid price cac chang.
3. Chap nhan/tu choi kem ly do.
4. Neu chap nhan thi gan ghe va cap nhat ton kho.

UI/UX implication:

- can co trang thai quyet dinh ro rang
- ly do chap nhan/tu choi phai de doc
- neu co tac dong len ton kho/han ngach thi nen hien thi duoc

### 4.3. Luong mo phong & phe duyet

1. Quan ly mo dashboard.
2. Chay mo phong chinh sach.
3. So sanh AI vs hien tai.
4. Phe duyet/ghi de.
5. Ghi log.

UI can uu tien:

- so sanh side-by-side hoac bang tong hop ro rang
- action primary/secondary de tranh bam nham
- feedback sau khi phe duyet/ghi de

## 5. Danh sach man hinh / module UI suy ra tu PRD

Tu noi dung PRD, FE can it nhat cac man hinh/module sau:

1. Dashboard tai chang cho quan ly.
2. Heatmap chang x thoi gian.
3. Ma tran ga di - ga den.
4. Bieu do toc do ban va du bao.
5. Bang doan trong co the ghep.
6. Man hinh mo phong va phe duyet.
7. Man hinh canh bao.
8. Man hinh/log bao cao thay doi chinh sach.
9. Cac thanh phan giai thich gia va ly do de xuat.
10. Giao dien quan tri co phan quyen theo vai tro.

## 6. Tieu chi UX quan trong rut ra tu PRD

1. Nhan biet nhanh tinh trang tai chang.
2. It thao tac de thay insight quan trong.
3. Co minh bach va giai thich cho moi de xuat AI.
4. Co kha nang can thiep thu cong, khong bat nguoi dung phu thuoc hoan toan vao AI.
5. Co canh bao ro trong cac truong hop rui ro hoac ngoai le.
6. Ho tro ra quyet dinh nhanh, khong chi de xem bao cao.
7. Tieng Viet hoa day du, phu hop ngu canh nghiep vu.

## 7. Trich doan/nguon tham chieu chinh trong PRD

Nhung phan chinh da duoc loc tu `prd_duong_sat.md`:

- Muc 4.1: Pham vi MVP co `heatmap tai chang`, `dashboard mo phong`.
- Muc 5: Personas va cach dung SRRM.
- Muc 7.1: `US1.3`, `FR1.6`, `FR1.7`.
- Muc 7.2: `FR2.7` ve canh bao ro khi doi cho.
- Muc 7.4: `FR4.1`, `FR4.2`, `FR4.3`, `FR4.4`.
- Muc 8: `NFR1`, `NFR5`, `NFR9`.
- Muc 10: Luong `dashboard -> mo phong -> so sanh -> phe duyet/ghi de -> ghi log`.

## 8. File nguon

- Nguon goc: [prd_duong_sat.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/prd_duong_sat.md)
