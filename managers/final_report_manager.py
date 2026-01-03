import csv
import re 
from datetime import datetime
from reports.final_report import FinalReport

class FinalReportManager:
    def __init__(self, filename="final_reports.csv"):
        self.filename = filename

    # CREATE FINAL REPORT
    def create_report(self, project_manager, staff_manager, task_manager):
        print("\n--- TẠO BÁO CÁO TỔNG KẾT ---")

        # ===== 1. CHỌN DỰ ÁN =====
        selected_project = None
        while True:
            pid = input("Nhập mã dự án cần tổng kết (hoặc 'exit'): ").strip()
            if pid.lower() == 'exit': return

            project = project_manager.find_by_id(pid)
            if not project:
                print("Lỗi: Dự án không tồn tại.")
                continue

            if project.status_project not in ("Hoàn thành", "Hủy"):
                print(f"Lỗi: Dự án đang '{project.status_project}'. Chỉ được tổng kết khi đã 'Hoàn thành' hoặc 'Hủy'.")
                continue
            
            # Kiểm tra xem đã có báo cáo chưa (Tránh tạo trùng)
            expected_id = f"FR{project.project_id}"
            if any(r['report_id'] == expected_id for r in self._load_all()):
                print(f"Lỗi: Báo cáo tổng kết cho dự án {pid} đã tồn tại.")
                return

            selected_project = project
            break

        # ===== 2. CHỌN PM (XÁC THỰC QUYỀN SỞ HỮU) =====
        selected_author = None
        while True:
            sid = input("Nhập mã PM lập báo cáo: ").strip()
            author = staff_manager.find_by_id(sid)

            if not author:
                print("Lỗi: Nhân viên không tồn tại.")
                continue

            # Kiểm tra chức vụ
            if getattr(author, "management_title", "") != "Project Manager":
                print("Lỗi: Nhân viên này không phải là Project Manager.")
                continue

            # QUAN TRỌNG: Kiểm tra PM này có quản lý dự án này không?
            if hasattr(selected_project, 'pm_id') and selected_project.pm_id != sid:
                print(f"Lỗi: Bạn không phải quản lý của dự án {selected_project.project_id}.")
                print(f"(Dự án này thuộc về PM: {selected_project.pm_id})")
                continue

            selected_author = author
            break

        # ===== 3. TỰ ĐỘNG SINH MÃ BÁO CÁO =====
        rid = f"FR{selected_project.project_id}"
        print(f"Hệ thống tự động tạo mã báo cáo: {rid}")

        # ===== 4. TẠO VÀ LƯU =====
        try:
            report = FinalReport(
                project_id=selected_project.project_id,
                report_id=rid,
                author_id=selected_author.staff_id if hasattr(selected_author, 'staff_id') else getattr(selected_author, 'id', ''),
                report_date=datetime.now(),
                is_loading=False
            )

            report.input_info(
                project_manager=project_manager,
                task_manager=task_manager,
                staff_manager=staff_manager
            )

            report.display_info()

            confirm = input("\nXác nhận lưu báo cáo? (y/n): ").lower()
            if confirm == "y":
                report.save()
                print("Đã lưu báo cáo tổng kết thành công.")
            else:
                print("Đã hủy lưu báo cáo.")

        except Exception as e:
            print(f"Lỗi khi tạo báo cáo: {e}")

    # VIEW DETAIL 
    def view_report_detail(self, project_manager, staff_manager, task_manager):
        print("\n--- XEM BÁO CÁO TỔNG KẾT ---")
        while True:
            rid = input("Nhập mã báo cáo (VD: FRP25_00001) hoặc 'exit': ").strip()
            if rid.lower() == 'exit': return
            if not re.match(r"^FRP\d{2}_\d{5}$", rid):
                print("Lỗi định dạng! Mã báo cáo phải có dạng: FR{Mã_Dự_Án}. Ví dụ đúng: FRP25_00001")
                continue
            data = next((r for r in self._load_all() if r["report_id"] == rid), None)

            if not data:
                print("Không tìm thấy báo cáo.")
                continue

            try:
                report = FinalReport.from_dict(data)
                report.display_info()
                break
            except Exception as e:
                print(f"Dữ liệu báo cáo bị lỗi: {e}")
                break

    # SEARCH 
    def search_report(self):
        print("\n--- TÌM KIẾM BÁO CÁO ---")
        while True:
            keyword = input("Nhập mã BC hoặc Mã DA (hoặc 'exit'): ").strip()
            # 2. KIỂM TRA ĐỊNH DẠNG (1 trong 2)
            # Pattern cho Mã Dự Án (VD: P25_00001)
            is_valid_project = re.match(r"^P\d{2}_\d{5}$", keyword)
            
            # Pattern cho Mã Báo Cáo Tổng Kết (VD: FRP25_00001)
            is_valid_report = re.match(r"^FRP\d{2}_\d{5}$", keyword)

            if not (is_valid_project or is_valid_report):
                print(">>> Lỗi định dạng! Vui lòng nhập đúng 1 trong 2 loại:")
                print("    1. Mã dự án : Pyy_nnnnn   (VD: P25_00001)")
                print("    2. Mã báo cáo: FRPyy_nnnnn (VD: FRP25_00001)")
                continue
            if keyword.lower() == 'exit': return
            
            # Validate cơ bản
            if len(keyword) < 3:
                print("Vui lòng nhập ít nhất 3 ký tự.")
                continue

            results = [
                r for r in self._load_all()
                if keyword.lower() in r["report_id"].lower()
                or keyword.lower() in r["project_id"].lower()
            ]

            if not results:
                print("Không tìm thấy kết quả phù hợp.")
            else:
                print(f"Tìm thấy {len(results)} kết quả:")
                self._display_table(results)
                break

    # DISPLAY ALL
    def display_all(self):
        data = self._load_all()
        if not data:
            print("Chưa có báo cáo tổng kết.")
            return
        print(f"\n--- DANH SÁCH BÁO CÁO ({len(data)}) ---")
        self._display_table(data)

    # DELETE 
    def delete_report(self):
        print("\n--- XÓA BÁO CÁO ---")
        rid = input("Nhập mã báo cáo cần xóa: ").strip()
        
        data = self._load_all()
        target = next((r for r in data if r["report_id"] == rid), None)

        if not target:
            print("Không tìm thấy báo cáo.")
            return

        confirm = input(f"CẢNH BÁO: Xóa báo cáo {rid}? (y/n): ").lower()
        if confirm != "y":
            return
        remaining_data = [r for r in data if r["report_id"] != rid]
        valid_fields = set(FinalReport.csv_fields())
        cleaned_data = []
        
        for row in remaining_data:
            clean_row = {k: v for k, v in row.items() if k in valid_fields}
            cleaned_data.append(clean_row)

        try:
            with open(self.filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FinalReport.csv_fields())
                writer.writeheader()
                writer.writerows(cleaned_data) # Ghi dữ liệu đã làm sạch
            print("Đã xóa báo cáo thành công.")
        except Exception as e:
            print(f"Lỗi khi ghi file: {e}")

    # INTERNAL
    def _load_all(self):
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            return []

    def _display_table(self, data):
        print("-" * 90)
        print(
            f"| {'Mã BC':<15} | {'Dự án':<10} | {'Tên dự án':<25} | "
            f"{'Tiến độ':<8} | {'Trạng thái':<12} |"
        )
        print("-" * 90)
        for r in data:
            p_name = r.get('project_name', '')
            if len(p_name) > 23: p_name = p_name[:22] + ".."
            
            print(
                f"| {r.get('report_id',''):<15} | {r.get('project_id',''):<10} | "
                f"{p_name:<25} | "
                f"{str(r.get('overall_progress',0)):<8} | "
                f"{r.get('project_status',''):<12} |"
            )
        print("-" * 90)