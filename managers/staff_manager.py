#file staff_manager.py
import csv
import re
from models.staff import Staff

CAP_DO_HOP_LE = ["Intern", "Junior", "Senior"]

VAI_TRO_HOP_LE = [
    "Business Analyst", "Developer", "Tester",
    "UI/UX Designer", "Technical Lead",
    "Implementation Consultant", "DevOps Engineer",
    "Quality Assurance"
]

CHUC_DANH_QUAN_LY = ["Team Leader", "Project Manager"]


class StaffManager:
    """
    Quản lý nghiệp vụ Nhân viên
    - Lưu staff.csv
    - Không lưu project_list (suy ra từ task)
    """

    def __init__(self, filename="staffs.csv"):
        self.filename = filename
        self.staff_list = []
        self.load_from_file()
        self.task_manager = None
    def set_task_manager(self, task_manager):
        self.task_manager = task_manager
    # ==================================================
    # FILE
    # ==================================================
    def load_from_file(self):
        self.staff_list = []

        try:
            with open(self.filename, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    staff = Staff(
                        staff_id=row["staff_id"],
                        full_name=row["full_name"],
                        age=int(row["age"]),
                        level=row["level"],
                        role=row["role"],
                        management_title=row["management_title"] or None,
                        task_list=row["task_list"].split(";") if row["task_list"] else []
                    )
                    self.staff_list.append(staff)
        except FileNotFoundError:
            pass

    def save_to_file(self):
        with open(self.filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "staff_id",
                    "full_name",
                    "age",
                    "level",
                    "role",
                    "management_title",
                    "task_list",
                ]
            )
            writer.writeheader()

            for s in self.staff_list:
                writer.writerow({
                    "staff_id": s.staff_id,
                    "full_name": s.full_name,
                    "age": s.age,
                    "level": s.level,
                    "role": s.role,
                    "management_title": s.management_title or "",
                    "task_list": ";".join(s.task_list),
                })

    # ==================================================
    # CRUD
    # ==================================================
    def add_staff(self):
        staff = Staff()
        staff.input_info(self.staff_list)
        self.staff_list.append(staff)
        self.save_to_file()
        print("Thêm nhân viên thành công")

    def update_staff(self):
             while True:
                keyword = input("Nhập mã nhân viên cần cập nhật: ").strip().upper()

                # 1. Kiểm tra định dạng
                if not re.fullmatch(r"NV_\d{5}", keyword):
                    print("Mã nhân viên sai định dạng (VD: NV_00001)")
                    continue

                # 2. Kiểm tra tồn tại
                staff = self.find_by_id(keyword)
                if not staff:
                    print("Mã nhân viên không tồn tại, vui lòng nhập lại")
                    continue

                # 3. Hợp lệ → cập nhật
                staff.update_info()
                self.save_to_file()
                print("Cập nhật nhân viên thành công")
                return True
    def delete_staff(self):
        while True:
            staff_id = input("Nhập mã nhân viên muốn xóa: ").strip().upper()

            # 1. Kiểm tra định dạng
            if not re.fullmatch(r"NV_\d{5}", staff_id):
                print("Mã nhân viên sai định dạng (VD: NV_00001)")
                continue

            # 2. Kiểm tra tồn tại
            staff = next((s for s in self.staff_list if s.staff_id == staff_id), None)
            if not staff:
                print("Nhân viên không tồn tại, vui lòng nhập lại")
                continue

            break  
        # 3. Xác nhận xóa
        confirm = input(
            f"Bạn chắc chắn muốn xóa nhân viên {staff_id} vĩnh viễn? (y/n): "
        ).strip().lower()

        if confirm != "y":
            print("Đã hủy thao tác xóa.")
            return

        # 4. Gỡ nhân viên khỏi các task (chuyển sang Unassigned)
        if self.task_manager:
            self.task_manager.unassign_staff(staff_id)
        else:
            print("Cảnh báo: Chưa kết nối TaskManager.")

        # 5. Xóa nhân viên khỏi danh sách
        self.staff_list.remove(staff)

        # 6. Lưu file
        self.save_to_file()
        print(f"Đã xóa nhân viên {staff_id} thành công.")

    # ==================================================
    # DISPLAY
    # ==================================================
    def display_all(self):
        if not self.staff_list:
            print("Danh sách nhân viên trống")
            return

        print("\n=== DANH SÁCH NHÂN VIÊN ===")
        
        print(f"| {'Mã NV':<10} | {'Họ và tên':<15} | {'Tuổi':<3} | {'Cấp độ':<10} | {'Vai trò':<15} | {'Chức danh QL':<10} | {'Công việc':<25} |")

        for s in self.staff_list:
            s.display_info()
            
    # ==================================================
    # SEARCH 
    # ==================================================
    def search_staff(self):
        while True:
            print("\n--- TÌM KIẾM NHÂN VIÊN ---")
            print("1. Tìm theo mã nhân viên")
            print("2. Tìm theo họ tên")
            print("3. Tìm theo vai trò")
            print("0. Quay lại")

            choice = input("Chọn cách tìm: ").strip()

            # ================= QUAY LẠI =================
            if choice == "0":
                return

            # ================= THEO MÃ NV =================
            if choice == "1":
                while True:
                    keyword = input("Nhập mã nhân viên (NV_00001): ").strip().upper()

                    if not re.fullmatch(r"NV_\d{5}", keyword):
                        print("Mã nhân viên sai định dạng (VD: NV_00001)")
                        continue

                    result = [
                        s for s in self.staff_list
                        if s.staff_id.upper() == keyword
                    ]
                    break

            # ================= THEO HỌ TÊN =================
            elif choice == "2":
                while True:
                    keyword = input("Nhập họ tên nhân viên: ").strip()

                    if not re.fullmatch(r"[A-Za-zÀ-ỹ\s]+", keyword):
                        print("Họ tên không hợp lệ (không chứa số hoặc ký tự đặc biệt)")
                        continue

                    keyword_lower = keyword.lower()
                    result = [
                        s for s in self.staff_list
                        if keyword_lower in s.full_name.lower()
                    ]
                    break

            # ================= THEO VAI TRÒ =================
            elif choice == "3":
                print("Các vai trò hợp lệ:")
                for vt in VAI_TRO_HOP_LE:
                    print(f"- {vt}")

                while True:
                    keyword = input("Nhập vai trò: ").strip()

                    if keyword not in VAI_TRO_HOP_LE:
                        print("Vai trò không hợp lệ")
                        continue

                    result = [
                        s for s in self.staff_list
                        if s.role == keyword
                    ]
                    break

            else:
                print("Lựa chọn không hợp lệ")
                continue

            # ================= KẾT QUẢ =================
            if not result:
                print("Không tìm thấy nhân viên phù hợp")
                return

            print(f"\nKẾT QUẢ TÌM KIẾM ({len(result)} nhân viên):")
            print(
                f"| {'Mã NV':<10} | {'Họ và tên':<20} | {'Tuổi':<3} | "
                f"{'Cấp độ':<10} | {'Vai trò':<15} | {'Chức danh QL':<15} | {'Công việc được giao'}"
            )
            print("-" * 95)

            for s in result:
                s.display_info()

            return

    # ==================================================
    # NGHIỆP VỤ LIÊN KẾT
    # ==================================================
    def find_by_id(self, staff_id):
        return next(
            (s for s in self.staff_list if s.staff_id == staff_id),
            None
        )

    def remove_task_from_all_staff(self, task_id):
        """
        Khi task bị xóa hoặc hủy
        → gỡ task khỏi toàn bộ nhân viên
        """
        changed = False

        for s in self.staff_list:
            if task_id in s.task_list:
                s.task_list.remove(task_id)
                changed = True

        if changed:
            self.save_to_file()

    def add_task_to_staff(self, staff_id, task_id):
        """
        Khi giao task cho nhân viên
        """
        staff = self.find_by_id(staff_id)
        if not staff:
            return

        if task_id not in staff.task_list:
            staff.task_list.append(task_id)
            self.save_to_file()