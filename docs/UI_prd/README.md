# UI PRD

Thư mục này tập hợp toàn bộ tài liệu liên quan đến UI/UX và phạm vi Frontend của SRRM MVP.

## Mục tiêu

- Gom các tài liệu UI đang bị rải rác trong repo về một chỗ.
- Tách rõ tài liệu UI phục vụ designer, frontend và PM.
- Giữ lại các file nguồn quan trọng, loại bỏ các bản trùng lặp hoặc đặt sai chỗ.

## Tài liệu chính

- [ui_ux_requirements_from_prd.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/ui_ux_requirements_from_prd.md)
  - Lọc riêng các yêu cầu UI/UX từ PRD gốc.
  - Tập trung vào dashboard, heatmap, mô phỏng, phê duyệt, cảnh báo, RBAC và audit.

- [frontend_specs_mvp.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/frontend_specs_mvp.md)
  - Chuyển backlog FE thành implementation specs theo sprint.
  - Có mapping màn hình, component, API/phụ thuộc backend và definition of done.

- [ui_execute_plan.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/ui_execute_plan.md)
  - Kế hoạch triển khai dạng task list để bắt tay code theo folder và feature.

- [frontend_task_list.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/frontend_task_list.md)
  - Danh sách công việc FE được tổng hợp lại theo sprint và theo feature.

## Tài liệu theo màn hình

- [hd_dashboard_screen_guide.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/hd_dashboard_screen_guide.md)
  - Mô tả màn hình tổng quan và dashboard trung tâm.

- [hd_quote_screen_guide.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/hd_quote_screen_guide.md)
  - Mô tả màn hình báo giá và phương án thay thế.

- [hd_simulation_screen_guide.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/hd_simulation_screen_guide.md)
  - Mô tả màn hình mô phỏng và phê duyệt.

- [hd_alerts_screen_guide.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/hd_alerts_screen_guide.md)
  - Mô tả màn hình cảnh báo.

- [hd_audit_screen_guide.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/hd_audit_screen_guide.md)
  - Mô tả màn hình nhật ký kiểm toán.

- [hd_train_layout_screen_guide.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/hd_train_layout_screen_guide.md)
  - Mô tả màn hình toa tàu và sơ đồ ghế.

- [hd_login_screen_guide.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/UI_prd/hd_login_screen_guide.md)
  - Mô tả màn hình đăng nhập.

## Nguồn tham chiếu cần đọc cùng

- [docs/prd_duong_sat.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/prd_duong_sat.md)
  - PRD chính của dự án.

- [docs/tasks/SRRM-004-simulation-and-ui.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/tasks/SRRM-004-simulation-and-ui.md)
  - Task kỹ thuật gần nhất với dashboard và simulation workspace.

- [docs/specs/features.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/specs/features.md)
  - Functional requirements ở mức feature, đặc biệt là FR1.6, FR1.7, FR4.1, FR4.2, FR4.3, FR4.4.

- [docs/specs/user-roles.md](/D:/AI20K/Vietnam%20AI%20Innovation/Hackathon-Viber-Code-Pro-Max/docs/specs/user-roles.md)
  - Persona và hành động trên hệ thống cho Revenue Manager, Dispatcher và IT Integrator.

## Tổng hợp nhanh cho team UI

1. Persona trọng tâm của MVP là Revenue Manager.
2. Màn hình trọng tâm là dashboard tải chặng, workspace mô phỏng/phê duyệt, cảnh báo và audit.
3. Component trọng tâm là heatmap, booking curve, OD matrix, quote result, scenario compare chart và audit log.
4. Toàn bộ giao diện cần dùng tiếng Việt, có loading/empty/error và hỗ trợ can thiệp thủ công.
5. Luồng UX quan trọng nhất là xem insight nhanh, so sánh AI với hiện tại rõ ràng và phê duyệt an toàn.

## Định hướng sử dụng

- PM/designer: bắt đầu từ `ui_ux_requirements_from_prd.md`
- FE lead/dev: đọc tiếp `frontend_specs_mvp.md`
- Khi cần đối chiếu với backend hoặc spec tổng: xem các file trong phần `Nguồn tham chiếu cần đọc cùng`
