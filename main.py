from datetime import date

from models import Book, FacultyMember, Magazine, NotifiedMember, ReferenceBook, ResearchStudent, StudentMember
from library_service import LibraryManager
from storage import JSONStorage


DATA_FILE = "data.json"


def read_text(prompt):
    value = input(prompt).strip()
    if not value:
        raise ValueError("Input cannot be empty.")
    return value


def read_nonnegative_int(prompt):
    value = int(input(prompt))
    if value < 0:
        raise ValueError("Enter zero or a positive number.")
    return value


def register_item(manager):
    print("Item type: 1. Book  2. Magazine  3. ReferenceBook")
    choice = input("Choose item type: ").strip()
    item_classes = {"1": Book, "2": Magazine, "3": ReferenceBook}
    item_class = item_classes.get(choice)
    if item_class is None:
        raise ValueError("Invalid item type.")
    item = item_class(read_text("Item ID: "), read_text("Title: "))
    manager.register_item(item)
    print("Item registered successfully.")


def register_member(manager):
    print("Member type: 1. StudentMember  2. ResearchStudent  3. FacultyMember  4. NotifiedMember")
    choice = input("Choose member type: ").strip()
    member_classes = {"1": StudentMember, "2": ResearchStudent,
                     "3": FacultyMember, "4": NotifiedMember}
    member_class = member_classes.get(choice)
    if member_class is None:
        raise ValueError("Invalid member type.")
    member = member_class(read_text("Member ID: "), read_text("Name: "),
                         read_nonnegative_int("Borrowing limit: "))
    manager.register_member(member)
    print("Member registered successfully.")


def borrow_item(manager):
    loan = manager.borrow_item(read_text("Member ID: "), read_text("Item ID: "))
    print(f"Borrow successful: {loan.item_id} issued to {loan.member_id}; due {loan.due_date}.")


def return_item(manager):
    result = manager.return_item(read_text("Item ID: "))
    print(f"Return successful. Overdue days: {result['overdue_days']}; fine: {result['fine']}.")


def show_reports(manager):
    manager.report_all_items()
    manager.report_available_items()
    manager.report_active_loans()
    manager.report_overdue_loans()
    manager.report_members()


def main():
    storage = JSONStorage(DATA_FILE)
    try:
        manager = storage.load()
    except ValueError as error:
        print(error)
        print("Starting with an empty library. Existing data was not overwritten yet.")
        manager = LibraryManager()

    actions = {
        "1": register_item,
        "2": register_member,
        "3": borrow_item,
        "4": return_item,
        "5": show_reports,
    }

    while True:
        print(f"\n{manager.library_name}")
        print("1. Register item  2. Register member  3. Borrow item")
        print("4. Return item    5. View reports    6. Exit")
        choice = input("Choice: ").strip()

        if choice == "6":
            try:
                storage.save(manager)
                print("Data saved. Goodbye!")
            except OSError as error:
                print(error)
            break
        action = actions.get(choice)
        if action is None:
            print("Invalid choice. Select 1–6.")
            continue
        try:
            action(manager)
            storage.save(manager)
        except (ValueError, TypeError, OSError) as error:
            print(f"Error: {error}")


if __name__ == "_main_":
    main()
