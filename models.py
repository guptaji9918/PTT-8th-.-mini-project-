from abc import ABC, abstractmethod
from datetime import date, timedelta


class LibraryItem(ABC):
    """Abstract base class for every item in the library catalogue."""

    def _init_(self, item_id, title, available=True):
        self.item_id = str(item_id)
        self.title = str(title)
        self._available = bool(available)

    @property
    def available(self):
        """Read-only availability state."""
        return self._available

    def mark_borrowed(self):
        if not self._available:
            raise ValueError("This item is already borrowed.")
        self._available = False

    def mark_returned(self):
        self._available = True

    @abstractmethod
    def loan_period_days(self):
        """Return the permitted loan duration for this item."""
        raise NotImplementedError

    def to_dict(self):
        return {
            "type": self._class.name_,
            "item_id": self.item_id,
            "title": self.title,
            "available": self.available,
        }


class Book(LibraryItem):
    def loan_period_days(self):
        return 14


class Magazine(LibraryItem):
    def loan_period_days(self):
        return 7


class ReferenceBook(LibraryItem):
    def loan_period_days(self):
        return 0


class Member:
    """Base member account. Borrowed-item state is controlled by methods."""

    max_active_loans_default = 3

    def _init_(self, member_id, name, borrowing_limit=None):
        self.member_id = str(member_id)
        self.name = str(name)
        self.borrowing_limit = (
            self.max_active_loans_default
            if borrowing_limit is None
            else int(borrowing_limit)
        )
        if self.borrowing_limit < 0:
            raise ValueError("Borrowing limit cannot be negative.")
        self._borrowed_item_ids = set()

    @property
    def borrowed_item_ids(self):
        return tuple(sorted(self._borrowed_item_ids))

    @property
    def active_loan_count(self):
        return len(self._borrowed_item_ids)

    def can_borrow(self):
        return self.active_loan_count < self.borrowing_limit

    def add_borrowed_item(self, item_id):
        self._borrowed_item_ids.add(str(item_id))

    def remove_borrowed_item(self, item_id):
        self._borrowed_item_ids.discard(str(item_id))

    @classmethod
    def set_default_borrowing_limit(cls, limit):
        limit = int(limit)
        if limit < 0:
            raise ValueError("Borrowing limit cannot be negative.")
        cls.max_active_loans_default = limit

    def to_dict(self):
        return {
            "type": self._class.name_,
            "member_id": self.member_id,
            "name": self.name,
            "borrowing_limit": self.borrowing_limit,
            "borrowed_item_ids": list(self.borrowed_item_ids),
        }


class StudentMember(Member):
    def _init_(self, member_id, name, borrowing_limit=None):
        super()._init_(member_id, name, borrowing_limit)


class ResearchStudent(StudentMember):
    def _init_(self, member_id, name, borrowing_limit=None):
        super()._init_(member_id, name, borrowing_limit)


class FacultyMember(Member):
    def _init_(self, member_id, name, borrowing_limit=None):
        super()._init_(member_id, name, borrowing_limit)


class NotificationMixin:
    def send_notice(self, message):
        print(f"[Notification for {self.name}] {message}")


# MRO: NotifiedMember -> Member -> NotificationMixin -> object.
# Member is listed first so its account methods take precedence; the mixin
# supplies send_notice() without changing the core member business rules.
class NotifiedMember(Member, NotificationMixin):
    pass


class Loan:
    def _init_(self, item_id, member_id, issue_date, due_date):
        self.item_id = str(item_id)
        self.member_id = str(member_id)
        self.issue_date = date.fromisoformat(issue_date) if isinstance(issue_date, str) else issue_date
        self.due_date = date.fromisoformat(due_date) if isinstance(due_date, str) else due_date

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "member_id": self.member_id,
            "issue_date": self.issue_date.isoformat(),
            "due_date": self.due_date.isoformat(),
        }

