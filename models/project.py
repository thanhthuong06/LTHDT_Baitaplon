import re
from datetime import datetime
from models.ProjectItem import ProjectItem

class Project(ProjectItem):
    STATUS_LIST = [
        "Chưa khởi động",
        "Đang thực hiện",
        "Hoàn thành",
        "Hủy"
    ]

    def __init__(self):
        super().__init__()
        self.project_id = ""
        self.project_name = ""
        self.customer = ""
        self.description = ""
        self.start_date = None
        self.expected_end_date = None
        self.actual_end_date = None
        self.budget = 0.0
        self.status_project = "Chưa khởi động"
        self.pm_id = ""

    # ================= CSV =================
    @staticmethod
    def csv_fields():
        return [
            "project_id", "project_name", "customer", "description",
            "start_date", "expected_end_date", "actual_end_date",
            "budget", "status_project", "pm_id",
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
    def from_dict(cls, data):
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
        p.status_project = data.get("status_project", "Chưa khởi động")
        p.pm_id = data.get("pm_id", "")
        return p

    # ================= INPUT INFO =================
    def input_info(self, existing_project_ids):
        # 1. Mã dự án
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

        # 2. Tên dự án
        while True:
            name = input("Nhập tên dự án: ").strip()
            if len(name) < 2:
                print("Tên tối thiểu 2 ký tự")
                continue
            self.project_name = name.title()
            self.name = self.project_name
            break

        # 3. Khách hàng
        while True:
            customer = input("Nhập khách hàng: ").strip()
            if not customer:
                print("Không được để trống")
                continue
            self.customer = customer.title()
            break

        # 4. Mô tả
        self.description = input("Nhập mô tả dự án: ").strip()

        # 5. Ngày bắt đầu
        while True:
            try:
                s_str = input("Ngày bắt đầu (dd/mm/yyyy): ").strip()
                self.start_date = datetime.strptime(s_str, "%d/%m/%Y")
                break
            except ValueError:
                print("Ngày không hợp lệ. Nhập lại.")

        # 6. Ngày kết thúc dự kiến
        while True:
            try:
                d = datetime.strptime(input("Ngày hoàn thành dự kiến (dd/mm/yyyy): "), "%d/%m/%Y")
                if d < self.start_date:
                    print(f"Ngày dự kiến phải >= ngày bắt đầu ({self.start_date.strftime('%d/%m/%Y')})")
                    continue
                self.expected_end_date = d
                break
            except ValueError:
                print("Sai định dạng ngày")

        # 7. Ngân sách
        while True:
            try:
                self.budget = float(input("Ngân sách dự kiến: "))
                if self.budget <= 0:
                    print("Ngân sách phải > 0")
                    continue
                break
            except ValueError:
                print("Phải là số")

        self.actual_end_date = None
        self.status_project = "Chưa khởi động"

    # ================= UPDATE INFO (ĐÃ BỔ SUNG RÀNG BUỘC) =================
    def update_info(self):
        print("\n--- CẬP NHẬT THÔNG TIN DỰ ÁN (Enter để giữ nguyên) ---")

        # 1. Tên dự án
        while True:
            new_name = input(f"Tên dự án ({self.project_name}): ").strip()
            if not new_name:
                break # Giữ nguyên cũ
            if len(new_name) < 2:
                print("Tên tối thiểu 2 ký tự.")
            else:
                self.project_name = new_name.title()
                self.name = self.project_name
                break

        # 2. Khách hàng
        new_customer = input(f"Khách hàng ({self.customer}): ").strip()
        if new_customer:
            self.customer = new_customer.title()

        # 3. Mô tả
        new_desc = input(f"Mô tả ({self.description}): ").strip()
        if new_desc:
            self.description = new_desc

        # 4. Ngày bắt đầu
        # Logic: Nếu sửa ngày bắt đầu, phải kiểm tra xem nó có lớn hơn ngày kết thúc hiện tại không
        while True:
            s_old = self.start_date.strftime('%d/%m/%Y') if self.start_date else ''
            new_s = input(f"Ngày bắt đầu ({s_old}): ").strip()
            if not new_s:
                break
            try:
                temp_start = datetime.strptime(new_s, "%d/%m/%Y")
                # Kiểm tra ràng buộc với Expected End Date hiện tại
                if self.expected_end_date and temp_start > self.expected_end_date:
                    print(f"Lỗi: Ngày bắt đầu mới không được lớn hơn ngày kết thúc dự kiến hiện tại ({self.expected_end_date.strftime('%d/%m/%Y')})")
                    continue
                
                self.start_date = temp_start
                break
            except ValueError:
                print("Ngày không hợp lệ (dd/mm/yyyy).")

        # 5. Ngày kết thúc dự kiến
        # Logic: Nếu sửa ngày kết thúc, phải kiểm tra xem nó có nhỏ hơn ngày bắt đầu hiện tại không
        while True:
            e_old = self.expected_end_date.strftime('%d/%m/%Y') if self.expected_end_date else ''
            new_e = input(f"Ngày hoàn thành dự kiến ({e_old}): ").strip()
            if not new_e:
                break
            try:
                temp_end = datetime.strptime(new_e, "%d/%m/%Y")
                # Kiểm tra ràng buộc với Start Date hiện tại
                if self.start_date and temp_end < self.start_date:
                    print(f"Lỗi: Ngày kết thúc phải >= ngày bắt đầu hiện tại ({self.start_date.strftime('%d/%m/%Y')})")
                    continue
                
                self.expected_end_date = temp_end
                break
            except ValueError:
                print("Ngày không hợp lệ (dd/mm/yyyy).")

        # 6. Ngân sách
        while True:
            b_old = f"{self.budget:.0f}"
            new_b = input(f"Ngân sách ({b_old}): ").strip()
            if not new_b:
                break
            try:
                val = float(new_b)
                if val <= 0:
                    print("Ngân sách phải > 0")
                else:
                    self.budget = val
                    break
            except ValueError:
                print("Phải là số.")
        
        print("Đã cập nhật thông tin cơ bản.")

    # ================= AUTO STATUS =================
    def auto_update_status(self, task_manager):
        tasks = [t for t in task_manager.items if t.project_id == self.project_id]

        if not tasks:
            self.status_project = "Chưa khởi động"
            self.actual_end_date = None
            return

        all_completed = all(t.status_task == "Completed" for t in tasks)

        if all_completed:
            self.status_project = "Hoàn thành"
            if not self.actual_end_date:
                self.actual_end_date = datetime.now()
        else:
            self.status_project = "Đang thực hiện"
            self.actual_end_date = None

    # ================= DISPLAY =================
    def display_info(self):
        s = self.start_date.strftime("%d/%m/%Y") if self.start_date else "N/A"
        e = self.expected_end_date.strftime("%d/%m/%Y") if self.expected_end_date else "N/A"
        a = self.actual_end_date.strftime("%d/%m/%Y") if self.actual_end_date else "--/--/----"
        budget = f"{self.budget:,.0f} VNĐ"

        print(
            f"{self.project_id:<10} | "
            f"{self.project_name:<20} | "
            f"{self.customer:<15} | "
            f"{budget:>15} | "
            f"{s:<10} | "
            f"{e:<10} | "
            f"{a:<10} | "
            f"{self.status_project:<12} | "
            f"{self.pm_id}"
        )