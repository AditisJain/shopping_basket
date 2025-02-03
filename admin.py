import json
import os

ADMIN_FILE = "data/admin.json"
PRODUCTS_FILE = "data/products.json"
DISCOUNTS_FILE = "data/discounts.json"

# ------------------------ File I/O -------------------------
def load_data(file_path):
    """Load data from a JSON file."""
    try:
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, "r") as file:
            content = file.read().strip()
            return json.loads(content) if content else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data, file_path):
    """Save data to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# ------------------------ Classes -------------------------
""" Product class with to_dict and from_dict methods. """
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def to_dict(self):
        return {"name": self.name, "price": self.price}

    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data["price"])

""" Discount class with to_dict and from_dict methods. """
class Discount:
    def __init__(self, discount_type, products, x=None, y=None, percent=None):
        self.discount_type = discount_type
        self.products = products
        self.x = x
        self.y = int(y) if y is not None else None
        self.percent = percent

    def to_dict(self):
        data = {"type": self.discount_type, "products": self.products}
        if self.x is not None:
            data["x"] = self.x
        if self.y is not None:
            data["y"] = self.y
        if self.percent is not None:
            data["percent"] = self.percent
        return data

    @classmethod
    def from_dict(cls, data):
        return cls(data["type"], data["products"], data.get("x"), data.get("y"), data.get("percent"))

# ------------------------ Admins -------------------------

def load_admins():
    """Load admin data."""
    data = load_data(ADMIN_FILE)
    return data.get("admins", [])

def authenticate_admin(email, password):
    """Check admin credentials."""
    admins = load_admins()
    return any(admin["email"] == email and admin["password"] == password for admin in admins)

# ------------------------ Products -------------------------
def load_products():
    return [Product.from_dict(p) for p in load_data(PRODUCTS_FILE)]

def save_products(products):
    save_data([p.to_dict() for p in products], PRODUCTS_FILE)

'''Add product to the products list.'''
def add_product():
    products = load_products()
    while True:
        name = input("Enter product name: ").strip()
        price = float(input("Enter price per unit/kg: ").strip())

        if any(p.name.lower() == name.lower() for p in products):
            print(f"Product '{name}' already exists.")
        else:
            products.append(Product(name, price))

        if input("Add another product? (yes/no): ").strip().lower() != 'yes':
            break
    save_products(products)

# ------------------------- Discounts ------------------------

def load_discounts():
    return [Discount.from_dict(d) for d in load_data(DISCOUNTS_FILE)]

def save_discounts(discounts):
    save_data([d.to_dict() for d in discounts], DISCOUNTS_FILE)

'''Add discount to the discounts list.'''
def add_discount():
    discounts = load_discounts()
    products_list = load_products()
    product_names = [p.name.lower() for p in products_list]

    while True:
        print("\nDiscount Types:")
        print("1. Buy X get Y free")
        print("2. Buy X for Y (eg: 3 beans for 2)")
        print("3. Buy X for a fixed price (eg: 2 shampoo for £3)")
        print("4. Any X from set at Y price")
        print("5. X percent off")
        print("6. Member discount")
        discount_type = input("Enter discount type (1-6): ").strip()
        
        if (discount_type not in {"1", "2", "3", "4", "5", "6"}):
            print("Invalid choice.")
            continue
        
        products = [p.strip().lower() for p in input("Enter product(s) (comma separated): ").strip().split(',')]
        non_existing = [p for p in products if p not in product_names]

        if non_existing:
            print(f"Products not found: {', '.join(non_existing)}")
            continue

        if discount_type == "1":
            x = int(input("Enter X (buy X): ").strip())
            y = int(input("Enter Y (get Y free): ").strip())
            discounts.append(Discount("buy_x_get_y_free", products, x=x, y=y))
        elif discount_type == "2":
            x = int(input("Enter X (buy X): ").strip())
            y = int(input("Enter Y (price of Y quantity): ").strip())
            discounts.append(Discount("buy_x_for_price_of_y", products, x=x, y=y))
        elif discount_type == "3":
            x = int(input("Enter X (buy X items): ").strip())
            y = float(input("Enter fixed price for X items: ").strip())
            discounts.append(Discount("buy_x_for_fixed_price", products, x=x, y=y))
        elif discount_type == "4":
            x = int(input("Enter X (any x items from set): ").strip())
            y = int(input("Enter Y (price): ").strip())
            discounts.append(Discount("any_x_from_set_at_y_price", products, x=x, y=y))
        elif discount_type == "5":
            percent = float(input("Enter discount percent: ").strip())
            discounts.append(Discount("percent_off", products, percent=percent))
        elif discount_type == "6":
            percent = float(input("Enter member discount percent: ").strip())
            discounts.append(Discount("member_discount", products, percent=percent))
        else:
            print("Invalid choice.")
            continue

        if input("Add another discount? (yes/no): ").strip().lower() != 'yes':
            break
    save_discounts(discounts)

# ----------------------- Main Program -----------------------
if __name__ == "__main__":
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password: ").strip()

    if authenticate_admin(email, password):
        print("\nAccess granted.")
        while True:
            print("\n1. Add product")
            print("2. Add discount")
            choice = input("Enter choice (1/2): ").strip()

            if choice == "1":
                add_product()
            elif choice == "2":
                add_discount()
            else:
                print("Invalid choice.")

            if input("Go back to main menu? (yes/no): ").strip().lower() != 'yes':
                break
    else:
        print("Access denied. Wrong credentials!")