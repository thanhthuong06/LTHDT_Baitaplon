# file weekly_report_manager.py
from datetime import datetime, timedelta
from reports.weekly_report import WeeklyReport
from reports.base_report import BaseReport
import re


class WeeklyReportManager:
    """
    Quản lý báo cáo tuần của dự án
    - Đảm bảo ràng buộc tuần theo tiến độ dự án
    - Chỉ Project Manager được lập báo cáo
    - Tuần không được trùng, không được nhảy
    """

    def __init__(self, filename="weekly_reports.csv"):
        self.filename = filename

    # ================= 1. TẠO BÁO CÁO TUẦN =================
    def create_report(self, project_manager, staff_manager, task_manager):
        print("\n--- TẠO BÁO CÁO TUẦN ---")

        # 1. Chọn dự án
        while True:
            pid = input("Nhập mã dự án: ").strip()
            project = project_manager.find_by_id(pid)
            if not project:
                print("Dự án không tồn tại.")
                continue
            break

        # 2. Nhập người lập (bắt buộc PM)
        while True:
            sid = input("Nhập mã nhân viên lập báo cáo (PM, Enter để thoát): ").strip()

            # Nếu không nhập, thoát luôn
            if not sid:
                print("Đã hủy tạo báo cáo.")
                return  # thoát khỏi create_report

            # Nếu nhập "exit", cũng thoát
            if sid.lower() == "exit":
                print("Đã hủy tạo báo cáo.")
                return

            # Kiểm tra tồn tại nhân viên
            author = staff_manager.find_by_id(sid)
            if not author:
                print("Nhân viên không tồn tại.")
                continue

            # Kiểm tra phải là Project Manager
            if getattr(author, "management_title", "") != "Project Manager":
                print("Chỉ Project Manager mới được lập báo cáo.")
                continue

            # Kiểm tra là PM của dự án
            if author.staff_id != project.pm_id:
                print("Người lập báo cáo phải là PM của dự án này!")
                continue

            # Nếu hợp lệ, thoát vòng lặp
            break


        # 3. RÀNG BUỘC TUẦN
        reports = BaseReport.load_from_csv(self.filename)
        project_reports = [r for r in reports if r["project_id"] == pid]
        if not project_reports:
            expected_start = project.start_date
            print(f"Tuần đầu tiên bắt buộc bắt đầu từ: {expected_start.strftime('%d/%m/%Y')}")
            is_first_week = True
        else:
            last_report = max(
                project_reports,
                key=lambda r: datetime.strptime(r["period_end"], "%Y-%m-%d")
            )
            last_end = datetime.strptime(last_report["period_end"], "%Y-%m-%d")
            expected_start = last_end + timedelta(days=1)
            print(f"Tuần tiếp theo bắt buộc bắt đầu từ: {expected_start.strftime('%d/%m/%Y')}")
            is_first_week = False


        while True:
            try:
                # ===== NHẬP NGÀY BẮT ĐẦU =====
                s_date_str = input("Nhập ngày bắt đầu tuần (dd/mm/yyyy): ").strip()
                s_date = datetime.strptime(s_date_str, "%d/%m/%Y")

                if s_date.date() != expected_start.date():
                    print("Ngày bắt đầu không hợp lệ theo tiến độ dự án.")
                    continue

                # ===== TUẦN ĐẦU: NHẬP TAY NGÀY KẾT THÚC =====
                if is_first_week:
                    e_date_str = input("Nhập ngày kết thúc tuần 1 (dd/mm/yyyy): ").strip()
                    e_date = datetime.strptime(e_date_str, "%d/%m/%Y")

                    if e_date < s_date:
                        print("Ngày kết thúc không được trước ngày bắt đầu.")
                        continue

                    if e_date > project.expected_end_date:
                        print("Ngày kết thúc vượt quá ngày kết thúc dự án.")
                        continue

                    if (e_date - s_date).days >= 7:
                        print("Tuần báo cáo không được dài quá 7 ngày.")
                        continue

                # ===== TUẦN SAU: TỰ ĐỘNG =====
                else:
                    standard_end = s_date + timedelta(days=6)
                    e_date = min(standard_end, project.expected_end_date)

                print(
                    f"Kỳ báo cáo: "
                    f"{s_date.strftime('%d/%m/%Y')} - {e_date.strftime('%d/%m/%Y')}"
                )
                break

            except ValueError:
                print("Sai định dạng ngày (dd/mm/yyyy).")

        print(f"Mã báo cáo phải theo dạng: WR{pid}_Wxx (VD: WR{pid}_W01)")

        # Lấy danh sách báo cáo đã có
        existing_reports = BaseReport.load_from_csv(self.filename)
        existing_ids = {r["report_id"] for r in existing_reports}

        pattern = rf"^WR{pid}_W\d{{2}}$"

        while True:
            rid = input("Nhập mã báo cáo: ").strip()

            # 1. Không được để trống
            if not rid:
                print("Mã báo cáo không được để trống.")
                continue

            # 2. Kiểm tra đúng format
            if not re.fullmatch(pattern, rid):
                print(
                    f"Sai định dạng mã báo cáo.\n"
                    f"Định dạng đúng: WR{pid}_Wxx (VD: WR{pid}_W01)"
                )
                continue

            # 3. Kiểm tra trùng
            if rid in existing_ids:
                print("Mã báo cáo đã tồn tại. Vui lòng nhập mã khác.")
                continue

            break
        # 5. Tạo và lưu báo cáo
        try:
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

            confirm = input("Xác nhận lưu báo cáo? (y/n): ").lower()
            if confirm == "y":
                report.save()
                print("Lưu báo cáo thành công.")
            else:
                print("Đã hủy tạo báo cáo.")

        except Exception as e:
            print(f"Lỗi khi tạo báo cáo: {e}")

    # ================= 2. XEM CHI TIẾT BÁO CÁO =================
    def view_report_detail(self, project_manager, staff_manager, task_manager):
        print("\n--- XEM CHI TIẾT BÁO CÁO ---")
        report_id = input("Nhập mã báo cáo: ").strip()

        raw = BaseReport.search_item(self.filename, report_id)
        row = next((r for r in raw if r["report_id"] == report_id), None)

        if not row:
            print("Không tìm thấy báo cáo.")
            return

        try:
            project = project_manager.find_by_id(row["project_id"])
            author = staff_manager.find_by_id(row["author_id"])

            s_date = datetime.strptime(row["period_start"], "%Y-%m-%d")
            e_date = datetime.strptime(row["period_end"], "%Y-%m-%d")
            c_date = datetime.strptime(row["created_date"], "%Y-%m-%d %H:%M:%S")

            report = WeeklyReport(
                wreport_id=report_id,
                project=project,
                author=author,
                task_manager=task_manager,
                report_date=c_date,
                period_start_date=s_date,
                period_end_date=e_date,
                is_loading=True
            )

            report.display()

        except Exception as e:
            print(f"Lỗi hiển thị báo cáo: {e}")

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

            # 1. Cho phép thoát
            if rid.lower() == 'exit':
                print("Đã hủy thao tác xóa.")
                return

            # 2. Kiểm tra định dạng Regex: WR{project_id}_WXX
            # Giải thích: ^WR (bắt đầu bằng WR) + P\d{2}_\d{5} (mã dự án) + _W (nối tuần) + \d{2} (2 số tuần)
            if not re.match(r"^WRP\d{2}_\d{5}_W\d{2}$", rid):
                print("Lỗi: Sai định dạng mã báo cáo.") 
                print("Mẫu đúng: WRP25_00004_W01 (WR + Mã Dự Án + _W + Tuần)")
                continue

            # 3. Kiểm tra mã có tồn tại trong danh sách không?
            found_report = None
            for report in self.reports:
                # Lấy ID an toàn (dù thuộc tính tên là id hay report_id)
                curr_id = getattr(report, "report_id", getattr(report, "id", None))
                if curr_id == rid:
                    found_report = report
                    break
            
            if not found_report:
                print(f"Lỗi: Không tìm thấy báo cáo có mã '{rid}' trong hệ thống.")
                continue

            # 4. Xác nhận xóa
            confirm = input(f"CẢNH BÁO: Bạn chắc chắn muốn xóa '{rid}'? (y/n): ").strip().lower()
            if confirm != 'y':
                print("Đã hủy xóa.")
                return # Thoát hàm, quay về menu chính

            # 5. Thực hiện xóa
            # Gọi hàm xóa từ class cha (xử lý file CSV)
            if BaseReport.delete_item(self.filename, rid):
                # Xóa trong list bộ nhớ để đồng bộ
                self.reports.remove(found_report)
                print("- Đã xóa báo cáo thành công.")
                return
            else:
                print("Lỗi hệ thống: Không thể xóa dữ liệu trong file.")
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