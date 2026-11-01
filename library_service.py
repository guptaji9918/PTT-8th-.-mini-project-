from datetime import date, timedelta

from models import Book, FacultyMember, LibraryItem, Loan, Magazine, Member, NotifiedMember, ReferenceBook, ResearchStudent, StudentMember


class LibraryManager:
    library_name = "Library Lending & Membership Management Backend"
    fine_per_overdue_day = 2

    def _init_(self):
        self.items = {}
        self.members = {}
        self.loans = {}  # keyed by item ID; only active loans are stored

    @staticmethod
    def validate_nonempty(value, field_name):
        if not str(value).strip():
            raise ValueError(f"{field_name} cannot be empty.")

    @staticmethod
    def calculate_fine(overdue_days):
        return max(0, int(overdue_days)) * LibraryManager.fine_per_overdue_day

    @classmethod
    def set_fine_policy(cls, amount_per_day):
        amount_per_day = int(amount_per_day)
        if amount_per_day < 0:
            raise ValueError("Fine per day cannot be negative.")
        cls.fine_per_overdue_day = amount_per_day

    def register_item(self, item):
        if not isinstance(item, LibraryItem):
            raise TypeError("Item must be a LibraryItem subclass instance.")
        self.validate_nonempty(item.item_id, "Item ID")
        if item.item_id in self.items:
            raise ValueError("Item ID must be unique.")
        self.items[item.item_id] = item

    def register_member(self, member):
        if not isinstance(member, Member):
            raise TypeError("Member must be a Member subclass instance.")
        self.validate_nonempty(member.member_id, "Member ID")
        if member.member_id in self.members:
            raise ValueError("Member ID must be unique.")
        self.members[member.member_id] = member

    def borrow_item(self, member_id, item_id, today=None):
        member_id, item_id = str(member_id), str(item_id)
        if member_id not in self.members:
            raise ValueError("Member not found.")
        if item_id not in self.items:
            raise ValueError("Item not found.")

        member = self.members[member_id]
        item = self.items[item_id]
        if not item.available:
            raise ValueError("Item is not available.")
        if item.loan_period_days() <= 0:
            raise ValueError("This reference item cannot be borrowed.")
        if not member.can_borrow():
            raise ValueError("Member has reached the borrowing limit.")

        issue_date = today or date.today()
        due_date = issue_date + timedelta(days=item.loan_period_days())
        loan = Loan(item_id, member_id, issue_date, due_date)
        item.mark_borrowed()
        member.add_borrowed_item(item_id)
        self.loans[item_id] = loan

        if isinstance(member, NotifiedMember):
            member.send_notice(f"Checkout successful: '{item.title}' is due on {due_date.isoformat()}.")
        return loan

    def return_item(self, item_id, today=None):
        item_id = str(item_id)
        if item_id not in self.loans:
            raise ValueError("No active loan exists for this item.")

        loan = self.loans[item_id]
        item = self.items[item_id]
        member = self.members[loan.member_id]
        return_date = today or date.today()
        overdue_days = max(0, (return_date - loan.due_date).days)
        fine = self.calculate_fine(overdue_days)

        item.mark_returned()
        member.remove_borrowed_item(item_id)
        del self.loans[item_id]
        return {"item_id": item_id, "member_id": loan.member_id,
                "return_date": return_date, "overdue_days": overdue_days, "fine": fine}

    def active_loans(self):
        return list(self.loans.values())

    def overdue_loans(self, today=None):
        today = today or date.today()
        return [loan for loan in self.loans.values() if loan.due_date < today]

    def report_all_items(self):
        print("\nALL LIBRARY ITEMS")
        for item in self.items.values():
            print(f"{item.item_id} | {item.title} | {item._class.name_} | {'Available' if item.available else 'Borrowed'}")

    def report_available_items(self):
        print("\nAVAILABLE ITEMS")
        available = [item for item in self.items.values() if item.available]
        if not available:
            print("No items currently available.")
        for item in available:
            print(f"{item.item_id} | {item.title} | {item._class.name_}")

    def report_active_loans(self):
        print("\nACTIVE LOANS")
        if not self.loans:
            print("No active loans.")
        for loan in self.loans.values():
            print(f"{loan.item_id} | {loan.member_id} | Issued: {loan.issue_date} | Due: {loan.due_date}")

    def report_overdue_loans(self, today=None):
        print("\nOVERDUE LOANS")
        overdue = self.overdue_loans(today)
        if not overdue:
            print("No overdue loans.")
        for loan in overdue:
            days = max(0, ((today or date.today()) - loan.due_date).days)
            print(f"{loan.item_id} | {loan.member_id} | Due: {loan.due_date} | Overdue days: {days} | Fine: {self.calculate_fine(days)}")

    def report_members(self):
        print("\nMEMBERS")
        for member in self.members.values():
            print(f"{member.member_id} | {member.name} | {member._class.name_} | Borrowed: {member.active_loan_count}/{member.borrowing_limit}")

    def to_dict(self):
        return {
            "library_name": self.library_name,
            "fine_per_overdue_day": self.fine_per_overdue_day,
            "items": [item.to_dict() for item in self.items.values()],
            "members": [member.to_dict() for member in self.members.values()],
            "loans": [loan.to_dict() for loan in self.loans.values()],
        }

    @classmethod
    def from_dict(cls, data):
        manager = cls()
        if not isinstance(data, dict):
            raise ValueError("Invalid data: expected a JSON object.")
        manager.set_fine_policy(data.get("fine_per_overdue_day", cls.fine_per_overdue_day))

        item_types = {"Book": Book, "Magazine": Magazine, "ReferenceBook": ReferenceBook}
        member_types = {"StudentMember": StudentMember, "ResearchStudent": ResearchStudent,
                        "FacultyMember": FacultyMember, "NotifiedMember": NotifiedMember}

        for record in data.get("items", []):
            item_class = item_types.get(record.get("type"))
            if item_class is None:
                raise ValueError("Invalid item type in saved data.")
            item = item_class(record["item_id"], record["title"], record.get("available", True))
            manager.register_item(item)

        for record in data.get("members", []):
            member_class = member_types.get(record.get("type"))
            if member_class is None:
                raise ValueError("Invalid member type in saved data.")
            member = member_class(record["member_id"], record["name"], record.get("borrowing_limit"))
            manager.register_member(member)

        for record in data.get("loans", []):
            loan = Loan(record["item_id"], record["member_id"], record["issue_date"], record["due_date"])
            if loan.item_id not in manager.items or loan.member_id not in manager.members:
                raise ValueError("Saved loan references a missing item or member.")
            if loan.item_id in manager.loans:
                raise ValueError("Duplicate active loan in saved data.")
            manager.loans[loan.item_id] = loan
            item = manager.items[loan.item_id]
            if item.available:
                item.mark_borrowed()
            manager.members[loan.member_id].add_borrowed_item(loan.item_id)
        return manager
