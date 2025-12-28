# models/project.py
import re
from datetime import datetime
from models.ProjectItem import ProjectItem


class Project(ProjectItem):
    STATUS_LIST = [
        "Chưa khởi động",
        "Đang thực hiện",
        "Tạm dừng",
        "Hoàn thành",
        "Hủy"
    ]

    def __init__(self):
        super().__init__()
        self.project_id = ""
        self.project_name = ""
        self.customer = ""
        self.expected_end_date = None
        self.actual_end_date = None
        self.budget = 0.0
        self.status_project = ""
        self.pm_id = ""        # Mã Project Manager

    @staticmethod
    def csv_fields():
        return [
            "project_id",
            "project_name",
            "customer",
            "description",
            "start_date",
            "expected_end_date",
            "actual_end_date",
            "budget",
            "status_project",
            "pm_id",  # thêm trường PM
        ]

    def to_dict(self):
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "customer": self.customer,
            "description": self.description,
            "start_date": self.start_date.strftime("%Y-%m-%d") if self.start_date else "",
            "expected_end_date": self.expected_end_date.strftime("%Y-%m-%d") if self.expected_end_date else "",
            "actual_end_date": self.actual_end_date.strftime("%Y-%m-%d") if self.actual_end_date else "",
            "budget": self.budget,
            "status_project": self.status_project,
            "pm_id": self.pm_id,
        }

    @classmethod
    def from_dict(cls, data: dict):
        p = cls()
        p.project_id = data.get("project_id", "")
        p.id = p.project_id
        p.project_name = data.get("project_name", "")
        p.name = p.project_name
        p.customer = data.get("customer", "")
        p.description = data.get("description", "")
        p.start_date = datetime.strptime(data["start_date"], "%Y-%m-%d") if data.get("start_date") else None
        p.expected_end_date = datetime.strptime(data["expected_end_date"], "%Y-%m-%d") if data.get("expected_end_date") else None
        p.actual_end_date = datetime.strptime(data["actual_end_date"], "%Y-%m-%d") if data.get("actual_end_date") else None
        p.budget = float(data.get("budget", 0))
        p.status_project = data.get("status_project", "")
        p.pm_id = data.get("pm_id", "")
        return p

    # ================= INPUT =================
    def input_info(self, existing_project_ids=None, staff_manager=None):
        if existing_project_ids is None:
            existing_project_ids = []

        # PROJECT ID
        while True:
            pid = input("Nhập mã dự án (PYY_NNNNN): ").strip()
            if not re.fullmatch(r"P\d{2}_\d{5}", pid):
                print("Sai định dạng (VD: P25_00001)")
                continue
            if pid in existing_project_ids:
                print("Mã dự án đã tồn tại")
                continue
            self.project_id = pid
            self.id = pid
            break

        # NAME
        while True:
            name = input("Nhập tên dự án: ").strip()
            if len(name) < 2:
                print("Tên tối thiểu 2 ký tự")
                continue
            self.project_name = name.title()
            self.name = self.project_name
            break

        # CUSTOMER
        while True:
            customer = input("Nhập khách hàng: ").strip()
            if not customer:
                print("Không được để trống")
                continue
            self.customer = customer.title()
            break

        # DESCRIPTION
        self.description = input("Nhập mô tả dự án: ").strip()

        # START DATE
        self.input_start_date()

        # EXPECTED END DATE
        while True:
            try:
                d = datetime.strptime(input("Ngày hoàn thành dự kiến (dd/mm/yyyy): "), "%d/%m/%Y")
                if d < self.start_date:
                    print("Ngày dự kiến phải >= ngày bắt đầu")
                    continue
                self.expected_end_date = d
                break
            except ValueError:
                print("Sai định dạng ngày")

        # ACTUAL END DATE
        while True:
            s = input("Ngày hoàn thành thực tế (Enter nếu chưa xong): ").strip()
            if not s:
                self.actual_end_date = None
                break
            try:
                d = datetime.strptime(s, "%d/%m/%Y")
                if d < self.start_date:
                    print("Ngày thực tế phải >= ngày bắt đầu")
                    continue
                self.actual_end_date = d
                break
            except ValueError:
                print("Sai định dạng ngày")

        # BUDGET
        while True:
            try:
                self.budget = float(input("Ngân sách dự kiến: "))
                if self.budget <= 0:
                    print("Ngân sách phải > 0")
                    continue
                break
            except ValueError:
                print("Phải là số")

        # STATUS
        while True:
            print("Chọn trạng thái:")
            for i, st in enumerate(self.STATUS_LIST, 1):
                print(f"{i}. {st}")

            try:
                choice = int(input("Chọn: "))
                if choice < 1 or choice > len(self.STATUS_LIST):
                    raise ValueError

                status = self.STATUS_LIST[choice - 1]
                today = datetime.now()

                if status == "Hoàn thành":
                    # Chưa tới hạn dự kiến
                    if self.expected_end_date and today < self.expected_end_date:
                        print("Dự án chưa tới ngày hoàn thành dự kiến → không thể chọn 'Hoàn thành'")
                        continue

                    # Có ngày thực tế nhưng sai logic
                    if self.actual_end_date and self.actual_end_date > today:
                        print("Ngày hoàn thành thực tế không hợp lệ")
                        continue

                self.status_project = status
                break

            except ValueError:
                print("Lựa chọn không hợp lệ")


        # PM (bắt buộc)
        if staff_manager:
            while True:
                pm_id = input("Nhập mã PM của dự án: ").strip()
                if not pm_id:
                    print("Phải nhập PM hoặc gõ 'exit' để hủy")
                    continue
                if pm_id.lower() == "exit":
                    print("Hủy nhập dự án.")
                    return False
                staff = staff_manager.find_by_id(pm_id)
                if not staff:
                    print("Nhân viên không tồn tại.")
                    continue
                if getattr(staff, "management_title", "") != "Project Manager":
                    print("Người nhập phải là Project Manager")
                    continue
                self.pm_id = pm_id
                break

        return True
    # ================= UPDATE (FULL VALIDATION) =================
    def update_info(self, staff_manager=None):
        print(f"\n--- CẬP NHẬT DỰ ÁN: {self.project_id} ---")
        print("(Nhấn Enter để giữ nguyên giá trị cũ)")

        # 1. Cập nhật Tên (Ràng buộc: >= 2 ký tự)
        while True:
            new_name = input(f"Tên dự án [{self.project_name}]: ").strip()
            if not new_name:
                break  # Bỏ qua, giữ nguyên cũ
            if len(new_name) < 2:
                print("Lỗi: Tên dự án phải tối thiểu 2 ký tự.")
                continue
            self.project_name = new_name.title()
            self.name = self.project_name
            break

        # 2. Cập nhật Khách hàng (Ràng buộc: không để trống nếu đã nhập sửa)
        while True:
            new_customer = input(f"Khách hàng [{self.customer}]: ").strip()
            if not new_customer:
                break
            self.customer = new_customer.title()
            break

        # 3. Cập nhật Mô tả (Không ràng buộc khắt khe)
        new_desc = input(f"Mô tả [{self.description}]: ").strip()
        if new_desc:
            self.description = new_desc

        # 4. Cập nhật Ngày dự kiến hoàn thành (Ràng buộc: >= start_date)
        cur_expected = self.expected_end_date.strftime("%d/%m/%Y") if self.expected_end_date else "N/A"
        while True:
            date_str = input(f"Ngày dự kiến HT [{cur_expected}]: ").strip()
            if not date_str:
                break
            try:
                new_date = datetime.strptime(date_str, "%d/%m/%Y")
                if self.start_date and new_date < self.start_date:
                    print(f"Lỗi: Ngày dự kiến ({date_str}) phải sau ngày bắt đầu ({self.start_date.strftime('%d/%m/%Y')})")
                    continue
                self.expected_end_date = new_date
                break
            except ValueError:
                print("Lỗi: Sai định dạng ngày (dd/mm/yyyy).")

        # 5. Cập nhật Ngân sách (Ràng buộc: > 0)
        while True:
            budget_str = input(f"Ngân sách [{self.budget}]: ").strip()
            if not budget_str:
                break
            try:
                val = float(budget_str)
                if val <= 0:
                    print("Lỗi: Ngân sách phải > 0.")
                    continue
                self.budget = val
                break
            except ValueError:
                print("Lỗi: Vui lòng nhập số.")

        # 6. Cập nhật Trạng thái (Logic phức tạp về ngày tháng)
        # Không cần while loop bao ngoài vì ta chọn theo menu số, sai thì thôi
        print(f"Trạng thái hiện tại: {self.status_project}")
        print("Danh sách trạng thái mới:")
        for i, st in enumerate(self.STATUS_LIST, 1):
            print(f"{i}. {st}")
        
        st_choice = input("Chọn trạng thái mới (Enter để bỏ qua): ").strip()
        if st_choice:
            try:
                idx = int(st_choice) - 1
                if 0 <= idx < len(self.STATUS_LIST):
                    new_status = self.STATUS_LIST[idx]
                    
                    # Logic kiểm tra: Nếu chọn Hoàn thành mà chưa tới ngày dự kiến
                    is_valid = True
                    today = datetime.now()
                    
                    if new_status == "Hoàn thành":
                         if self.expected_end_date and today < self.expected_end_date:
                            confirm = input("CẢNH BÁO: Chưa tới ngày dự kiến. Vẫn muốn set 'Hoàn thành'? (y/n): ")
                            if confirm.lower() != 'y':
                                is_valid = False
                    
                    if is_valid:
                        self.status_project = new_status
                        # Tự động gán ngày thực tế nếu chưa có
                        if new_status == "Hoàn thành" and not self.actual_end_date:
                            self.actual_end_date = today
                            print(f" Đã cập nhật ngày thực tế: {today.strftime('%d/%m/%Y')}")
                    else:
                        print(" Đã hủy thay đổi trạng thái.")
                else:
                    print("Lỗi: Lựa chọn không nằm trong danh sách.")
            except ValueError:
                print("Lỗi: Nhập không hợp lệ.")

        # 7. Cập nhật PM (Vòng lặp bắt buộc nhập đúng hoặc Enter)
        if staff_manager:
            while True:
                new_pm = input(f"Mã PM [{self.pm_id}]: ").strip()
                if not new_pm:
                    break # Enter để bỏ qua
                
                staff = staff_manager.find_by_id(new_pm)
                if not staff:
                    print(f"Lỗi: Không tìm thấy nhân viên có mã '{new_pm}'. Vui lòng nhập lại.")
                    continue # Quay lại đầu vòng lặp
                
                # Kiểm tra chức vụ (dùng getattr cho an toàn)
                if getattr(staff, "management_title", "") != "Project Manager":
                    print(f"Lỗi: Nhân viên '{staff.name}' không phải là Project Manager.")
                    continue # Quay lại đầu vòng lặp
                
                # Nếu mọi thứ OK
                self.pm_id = new_pm
                print(f" Đã cập nhật PM mới: {staff.name}")
                break

    # ================= DISPLAY =================
    def display_info(self):
        # 1. Xử lý hiển thị ngày tháng (tránh lỗi nếu ngày là None)
        s_date = self.start_date.strftime("%d/%m/%Y") if self.start_date else "N/A"
        e_date = self.expected_end_date.strftime("%d/%m/%Y") if self.expected_end_date else "N/A"
        
        # Ngày thực tế: Nếu chưa có thì hiện dấu gạch ngang
        if self.actual_end_date:
            a_date = self.actual_end_date.strftime("%d/%m/%Y")
        else:
            a_date = "--/--/----"

        # 2. Xử lý hiển thị tiền tệ (thêm dấu phẩy)
        budget_str = f"{self.budget:,.0f} VNĐ"

        print(
            f"{self.project_id:<10} | "        # Mã dự án
            f"{self.project_name:<20} | "      # Tên dự án
            f"{self.customer:<15} | "          # Khách hàng
            f"{budget_str:>15} | "             # Ngân sách (căn phải cho số)
            f"{s_date:<10} | "                 # Ngày bắt đầu
            f"{e_date:<10} | "                 # Ngày dự kiến
            f"{a_date:<10} | "                 # Ngày thực tế
            f"{self.status_project:<12} | "    # Trạng thái
            f"{self.pm_id}"                # Mã PM
        )
    