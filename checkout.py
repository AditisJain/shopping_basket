import json

class Basket:
    def __init__(self):
        self.items = {}
        self.member_id = None

    def add_product(self, product, quantity):
        if product in self.items:
            self.items[product] += quantity
        else:
            self.items[product] = quantity

    def calculate_total(self, pricing_rules):
        total = 0
        savings = 0
        detailed_receipt = []
        
        set_discount_applied = False
        for product, quantity in self.items.items():
            price, discount, details = pricing_rules.get_price_and_discount(product, quantity, self.items, self.member_id, set_discount_applied)
            total += price
            savings += discount
            detailed_receipt.append((product, quantity, price + discount, discount, details))  
            
            if any("Set discount" in detail for detail in details):
                set_discount_applied = True
        
        return total, savings, detailed_receipt

    def print_receipt(self, pricing_rules, total, savings, detailed_receipt):
        print("\n------------------------------------------------------")
        print("Item\t\t\t\t| Price")
        print("------------------------------------------------------")
        for product, quantity, subtotal, discount, details in detailed_receipt:
            unit_price = pricing_rules.products[product]
            total_price = unit_price * quantity
            print(f"{product.capitalize()} x {quantity}\t\t\t| £{total_price:.2f} ({unit_price:.2f}/unit)")

        print("------------------------------------------------------")
        print(f"Sub-total\t\t\t| £{total + savings:.2f}")
        print("------------------------------------------------------")
        print("Savings")
        print("------------------------------------------------------")
        
        for product, quantity, subtotal, discount, details in detailed_receipt:
            for detail in details:
                print(f"{detail:<25}\t| -£{discount:.2f}")

        print(f"Total savings\t\t\t| -£{savings:.2f}")
        print("------------------------------------------------------")
        print(f"Total to pay\t\t\t| £{total:.2f}")

class PricingRules:
    def __init__(self, products, discounts, members):
        self.products = {product['name'].lower(): product['price'] for product in products}
        self.discounts = discounts
        self.members = {member['membership_id']: member for member in members}

    def get_price_and_discount(self, product, quantity, basket_items, member_id=None, set_discount_applied=False):
        unit_price = self.products.get(product, 0)
        total_price = unit_price * quantity
        total_discount = 0
        details = []

        # Check for Set Discount First
        if not set_discount_applied:
            set_discounts = [rule for rule in self.discounts if rule['type'] == 'any_x_from_set_at_y_price']
            for discount_rule in set_discounts:
                set_products = discount_rule['products']
                set_quantity = discount_rule['x']
                set_price = discount_rule['y']

                # Find all eligible items from the basket
                matched_items = {p: basket_items[p] for p in basket_items if p in set_products}
                total_matched_quantity = sum(matched_items.values())
                total_matched_price = sum(self.products[p] * matched_items[p] for p in matched_items) 


                # If we have enough for at least one set
                if total_matched_quantity >= set_quantity and total_matched_price > set_price:
                    sorted_items = sorted(matched_items.items(), key=lambda x: self.products[x[0]])  # Sort by price
                    full_sets = total_matched_quantity // set_quantity # Number of full sets
                    leftover_items = total_matched_quantity % set_quantity  # Items that don’t fit into a full set
                    
                    # If we have leftovers, exclude the cheapest item(s) from set discount
                    if leftover_items > 0:
                        for i in range(len(sorted_items)):
                            product_name, product_qty = sorted_items[i]
                            if product_qty >= leftover_items:
                                matched_items[product_name] -= leftover_items
                                break
                            else:
                                leftover_items -= product_qty
                                matched_items[product_name] = 0

                    # Calculate discount based on actual matched items
                    actual_matched_price = sum(self.products[p] * matched_items[p] for p in matched_items)
                    total_set_discount = (actual_matched_price - (full_sets * set_price))
                    total_discount += total_set_discount
                    details.append(f"Set discount: {full_sets} x {set_quantity} for £{set_price:.2f}")
                    set_discount_applied = True
                    break  # Only one set discount rule applies

        # If a set discount was applied, skip member discount for this product
        if set_discount_applied:
            member_discount_applied = False  
        else:
            member_discount_applied = True  

        # Apply other individual product discounts if no set discount was applied
        for discount_rule in self.discounts:
            if product in discount_rule['products']:
                if discount_rule['type'] == 'buy_x_get_y_free' and quantity >= discount_rule['x']:
                    free_items = (quantity // discount_rule['x']) * discount_rule['y']
                    discount_amount = free_items * unit_price
                    temp_discount = discount_amount
                    if temp_discount > total_discount:
                        total_discount = temp_discount
                        details.append(f"{product.capitalize()} {discount_rule['x']} for {discount_rule['x'] - discount_rule['y']}")

                elif discount_rule['type'] == 'buy_x_for_price_of_y' and quantity >= discount_rule['x']:
                    groups = quantity // discount_rule['x']
                    remainder = quantity % discount_rule['x']
                    discount_price = (groups * discount_rule['y'] * unit_price) + (remainder * unit_price)
                    temp_discount = total_price - discount_price
                    if temp_discount > total_discount:
                        total_discount = temp_discount
                        details.append(f"{product.capitalize()} {discount_rule['x']} for {discount_rule['y']}")

                elif discount_rule['type'] == 'buy_x_for_fixed_price' and quantity >= discount_rule['x']:
                    groups = quantity // discount_rule['x']
                    remainder = quantity % discount_rule['x']
                    discount_price = (groups * discount_rule['y']) + (remainder * unit_price)
                    temp_discount = total_price - discount_price
                    if temp_discount > total_discount:
                        total_discount = temp_discount
                        details.append(f"{product.capitalize()} {discount_rule['x']} for £{discount_rule['y']:.2f}")

                elif discount_rule['type'] == 'percent_off':
                    discount_amount = total_price * (discount_rule['percent'] / 100)
                    temp_discount = discount_amount
                    if temp_discount > total_discount:
                        total_discount = temp_discount
                        details.append(f"{discount_rule['percent']}% off on {product.capitalize()}")

                # Member Discount
                elif discount_rule['type'] == 'member_discount' and member_id and member_discount_applied:
                    discount_amount = total_price * (discount_rule['percent'] / 100)
                    temp_discount = discount_amount
                    if temp_discount > total_discount:
                        total_discount = temp_discount
                        details.append(f"{discount_rule['percent']}% member off {product.capitalize()}")

        final_price = total_price - total_discount
        return final_price, total_discount, details

# ----------------------- Helper Functions -----------------------
def load_data(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)
    
# ----------------------- Main Program -----------------------
if __name__ == "__main__":
    products = load_data('data/products.json')
    discounts = load_data('data/discounts.json')
    members = load_data('data/membership.json')
    pricing_rules = PricingRules(products, discounts, members)
    basket = Basket()
    
    member_id = input("Please enter your member ID if you have one (or type 'skip' to continue): ").strip()
    if member_id.lower() != 'skip' and member_id in pricing_rules.members:
        basket.member_id = member_id
        print("Member discount will be applied where applicable.")
    else:
        print("Proceeding without member discount.")

    products_input = input("Enter products and quantities to add to cart (e.g., apple 2, banana 3): ")
    products = [product.strip() for product in products_input.split(",")]

    for item in products:
        product, quantity = item.rsplit(' ', 1)
        if product.lower() in pricing_rules.products:
            basket.add_product(product.lower(), int(quantity))
        else:
            print(f"\n{product.capitalize()} is not available.")

    total, savings, detailed_receipt = basket.calculate_total(pricing_rules)
    basket.print_receipt(pricing_rules, total, savings, detailed_receipt)