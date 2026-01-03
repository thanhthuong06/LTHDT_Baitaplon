from datetime import datetime, timedelta
from reports.weekly_report import WeeklyReport
from reports.base_report import BaseReport
import re


class WeeklyReportManager:
    """
    Quản lý báo cáo tuần của dự án
    - Mã báo cáo sinh tự động
    - Ràng buộc thời gian tuần theo tiến độ dự án
    - Tuần không trùng, không nhảy
    """

    def __init__(self, filename="weekly_reports.csv"):
        self.filename = filename

    # ================= 1. TẠO BÁO CÁO TUẦN =================
    def create_report(self, project_manager, staff_manager, task_manager):
        print("\n--- TẠO BÁO CÁO TUẦN ---")

        # ===== CHỌN DỰ ÁN =====
        while True:
            pid = input("Nhập mã dự án: ").strip()
            project = project_manager.find_by_id(pid)
            if not project:
                print("Dự án không tồn tại.")
                continue
            break

        # ===== KIỂM TRA PM =====
        while True:
            sid = input("Nhập mã nhân viên lập báo cáo (PM, 'exit' để thoát): ").strip()
            if sid.lower() == "exit":
                return

            author = staff_manager.find_by_id(sid)
            if not author:
                print("Nhân viên không tồn tại.")
                continue

            if getattr(author, "management_title", "") != "Project Manager":
                print("Chỉ Project Manager mới được lập báo cáo.")
                continue

            if author.staff_id != project.pm_id:
                print("PM này không quản lý dự án.")
                continue
            break

        # ===== LẤY BÁO CÁO CŨ =====
        reports = BaseReport.load_from_csv(self.filename)
        project_reports = [r for r in reports if r["project_id"] == pid]

        # ===== XÁC ĐỊNH TUẦN =====
        if not project_reports:
            is_first_week = True
            expected_start = project.start_date
            print(f"Tuần 1 bắt đầu từ: {expected_start.strftime('%d/%m/%Y')}")
        else:
            is_first_week = False
            last = max(
                project_reports,
                key=lambda r: datetime.strptime(r["period_end"], "%Y-%m-%d")
            )
            expected_start = datetime.strptime(
                last["period_end"], "%Y-%m-%d"
            ) + timedelta(days=1)

        # ===== XỬ LÝ THỜI GIAN =====
        if is_first_week:
            s_date = expected_start
            while True:
                try:
                    e_str = input("Nhập ngày kết thúc tuần 1 (dd/mm/yyyy): ").strip()
                    e_date = datetime.strptime(e_str, "%d/%m/%Y")

                    if e_date < s_date:
                        print("Ngày kết thúc không hợp lệ.")
                        continue
                    if (e_date - s_date).days >= 7:
                        print("Tuần 1 không quá 7 ngày.")
                        continue
                    if e_date > project.expected_end_date:
                        print("Vượt quá ngày kết thúc dự án.")
                        continue
                    break
                except ValueError:
                    print("Sai định dạng ngày.")
        else:
            s_date = expected_start
            e_date = s_date + timedelta(days=6)
            if e_date > project.expected_end_date:
                e_date = project.expected_end_date

        print(
            f"Kỳ báo cáo: {s_date.strftime('%d/%m/%Y')} - {e_date.strftime('%d/%m/%Y')}"
        )

        # ===== SINH MÃ BÁO CÁO TỰ ĐỘNG =====
        week_no = len(project_reports) + 1
        rid = f"WR{pid}_W{week_no:02d}"
        print(f"Mã báo cáo tự động: {rid}")

        # ===== TẠO & LƯU =====
        report = WeeklyReport(
            wreport_id=rid,
            project=project,
            author=author,
            task_manager=task_manager,
            report_date=datetime.now(),
            period_start_date=s_date,
            period_end_date=e_date,
            is_loading=False
        )

        report.display()
        if input("Xác nhận lưu báo cáo? (y/n): ").lower() == "y":
            report.save()
            print("Lưu báo cáo thành công.")
        else:
            print("Đã hủy.")

    # ================= 2. XEM CHI TIẾT =================
    def view_report_detail(self, project_manager, staff_manager, task_manager):
        print("\n--- XEM CHI TIẾT BÁO CÁO ---")

        while True:
            rid = input("Nhập mã báo cáo (hoặc 'exit'): ").strip()
            if rid.lower() == "exit":
                return

            rows = BaseReport.search_item(self.filename, rid)
            row = next((r for r in rows if r["report_id"] == rid), None)
            if not row:
                print("Không tìm thấy. Nhập lại.")
                continue

            project = project_manager.find_by_id(row["project_id"])
            author = staff_manager.find_by_id(row["author_id"])

            s_date = datetime.strptime(row["period_start"], "%Y-%m-%d")
            e_date = datetime.strptime(row["period_end"], "%Y-%m-%d")
            c_date = datetime.strptime(row["created_date"], "%Y-%m-%d %H:%M:%S")

            report = WeeklyReport(
                wreport_id=rid,
                project=project,
                author=author,
                task_manager=task_manager,
                report_date=c_date,
                period_start_date=s_date,
                period_end_date=e_date,
                is_loading=True
            )

            report.display()
            break

    # ================= 3. HIỂN THỊ DANH SÁCH =================
    def display_all(self):
        data = BaseReport.load_from_csv(self.filename)
        if not data:
            print("Danh sách báo cáo trống.")
            return
        self._display_table(data)

    # ================= 4. TÌM KIẾM (RÀNG BUỘC CHẶT) =================
    def search_report(self):
        print("\n--- TÌM KIẾM BÁO CÁO ---")
        while True:
            keyword = input("\nNhập mã cần tìm (hoặc 'exit' để thoát): ").strip()
            # 1. Cho phép thoát
            if keyword.lower() == 'exit':
                return

            # 2. Định nghĩa Regex
            project_pattern = r"^P\d{2}_\d{5}$"
            report_pattern = r"^WRP\d{2}_\d{5}_W\d{2}$"
            # 3. Kiểm tra Validation (Hợp lệ 1 trong 2 trường hợp)
            is_valid_project = re.match(project_pattern, keyword)
            is_valid_report = re.match(report_pattern, keyword)
            if not (is_valid_project or is_valid_report):
                print(">>> LỖI ĐỊNH DẠNG! Vui lòng chỉ nhập theo 2 mẫu sau:")
                print(f"   - Mã dự án : Pyy_nnnnn       (VD: P25_00004)")
                print(f"   - Mã báo cáo: WRPyy_nnnnn_Wnn (VD: WRP25_00004_W01)")
                continue
            # --- THỰC HIỆN TÌM KIẾM ---
            # Nếu nhập đúng định dạng thì mới bắt đầu tìm trong file
            results = BaseReport.search_item(self.filename, keyword)
            if not results:
                print(f" Không tìm thấy dữ liệu nào khớp với mã '{keyword}'.")
            else:
                print(f" Tìm thấy {len(results)} kết quả:")
                self._display_table(results)
                more = input("\nBạn có muốn tìm mã khác không? (y/n): ").lower()
                if more != 'y':
                    break

    # ================= 5. XÓA =================
    def delete_report(self):
        print("\n--- XÓA BÁO CÁO ---")

        while True:
            rid = input("Nhập mã báo cáo (VD: WRP25_00004_W01) hoặc 'exit' để thoát: ").strip()

            if rid.lower() == 'exit':
                print("Đã hủy thao tác xóa.")
                return

            if not re.match(r"^WRP\d{2}_\d{5}_W\d{2}$", rid):
                print("Sai định dạng mã báo cáo.")
                continue

            # kiểm tra tồn tại trong file
            results = BaseReport.search_item(self.filename, rid)
            if not results:
                print(f"Không tìm thấy báo cáo '{rid}'.")
                continue

            confirm = input(f"CẢNH BÁO: Xóa báo cáo '{rid}'? (y/n): ").lower()
            if confirm != 'y':
                print("Đã hủy xóa.")
                return

            if BaseReport.delete_item(self.filename, rid):
                print("Đã xóa báo cáo thành công.")
            else:
                print("Không thể xóa báo cáo.")
            return


    # ================= HÀM PHỤ IN BẢNG =================
    def _display_table(self, data):
        print(
            f"| {'Mã BC':<10} | {'Dự án':<10} | {'Từ ngày':<10} | {'Đến ngày':<10} | "
            f"{'Tổng CV':<8} | {'Hoàn thành':<10} | {'Trễ':<6} | {'Tiến độ':<8} | {'Trạng thái':<10} |"
        )
        for r in data:
            print(
                f"| {r.get('report_id',''):<10} | {r.get('project_id',''):<10} | "
                f"{r.get('period_start',''):<10} | {r.get('period_end',''):<10} | "
                f"{r.get('total_tasks','0'):<8} | {r.get('completed_tasks','0'):<10} | "
                f"{r.get('overdue_tasks','0'):<6} | {r.get('progress','0')}%   | "
                f"{r.get('status',''):<10} |"
            )