from reports.base_report import BaseReport
from datetime import timedelta


class WeeklyReport(BaseReport):
    WEEKLY_CSV = "weekly_reports.csv"

    def __init__(
        self,
        wreport_id,
        project,
        author,
        task_manager,
        report_date,
        period_start_date,
        period_end_date,
        is_loading=False
    ):
        self.p_id = project.project_id
        if not is_loading:
            self._validate_author(author)

        super().__init__(
            report_id=wreport_id,
            project_id=self.p_id,
            author_id=author.staff_id,
            created_date=report_date
        )

        self.project = project
        self.task_manager = task_manager
        self.period_start_date = period_start_date
        self.period_end_date = period_end_date

        self.project_tasks = [
            t for t in task_manager.task_list if t.project_id == self.p_id
        ]

        self.task_list = [
            t for t in self.project_tasks
            if (
                (t.start_date and self.period_start_date <= t.start_date <= self.period_end_date)
                or
                (t.deadline and self.period_start_date <= t.deadline <= self.period_end_date)
                or
                (
                    t.start_date and t.deadline
                    and t.start_date < self.period_start_date
                    and t.deadline > self.period_end_date
                )
            )
        ]

        self.total_tasks_count = len(
            [t for t in self.task_list if t.status_task != "Cancelled"]
        )

        self.completed_tasks_count = len(
            [
                t for t in self.task_list
                if t.status_task == "Completed"
                and t.completed_date
                and self.period_start_date <= t.completed_date <= self.period_end_date
            ]
        )

        self.overdue_tasks = [
            t for t in self.task_list
            if t.deadline
            and t.deadline < self.period_end_date
            and t.status_task not in ("Completed", "Cancelled")
        ]

        self.overdue_tasks_count = len(self.overdue_tasks)

        self.actual_progress = (
            round(self.completed_tasks_count / self.total_tasks_count * 100, 2)
            if self.total_tasks_count else 0
        )

        self.progress_status = self._get_progress_status()

    def _validate_author(self, author):
        if getattr(author, "management_title", "") != "Project Manager":
            raise PermissionError("Chỉ Project Manager được tạo báo cáo tuần")

    def _get_progress_status(self):
        if self.overdue_tasks_count > 0:
            return "Delay"
        if self.total_tasks_count == 0:
            return "On Track"
        if self.completed_tasks_count < self.total_tasks_count:
            return "At Risk"
        return "On Track"

    def as_dict(self):
        data = super().as_dict()
        data.update({
            "period_start": self.period_start_date.strftime("%Y-%m-%d"),
            "period_end": self.period_end_date.strftime("%Y-%m-%d"),
            "total_tasks": self.total_tasks_count,
            "completed_tasks": self.completed_tasks_count,
            "overdue_tasks": self.overdue_tasks_count,
            "progress": self.actual_progress,
            "status": self.progress_status
        })
        return data

    def save(self):
        return self.add_item(self.WEEKLY_CSV)

    def display(self):
        print("\n" + "=" * 70)
        print("BÁO CÁO TIẾN ĐỘ TUẦN".center(70))
        print("=" * 70)
        print(f"Mã báo cáo : {self.report_id}")
        print(f"Dự án      : {self.project_id}")
        print(
            f"Thời gian  : "
            f"{self.period_start_date.strftime('%d/%m/%Y')} - "
            f"{self.period_end_date.strftime('%d/%m/%Y')}"
        )
        print(f"Người lập  : {self.author_id}")
        print("-" * 70)
        print(f"Tổng CV    : {self.total_tasks_count}")
        print(f"Hoàn thành : {self.completed_tasks_count}")
        print(f"Quá hạn    : {self.overdue_tasks_count}")
        print(f"Tiến độ    : {self.actual_progress}%")
        print(f"Trạng thái : {self.progress_status}")
        print("=" * 70)
