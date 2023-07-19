import barcode
import random

def generate_barcode(product_name, price, save_path="."):
    # A function to generate a 12-digit random number for barcode
    def generate_random_number():
        num1 = "0123456789"
        num2 = "0123456789"
        number = num1 + num2
        length = 8
        result = "".join(random.sample(number,length))
        return result
    
    # Set the barcode format
    barcode_format = barcode.get_barcode_class('ean8')
    # Generate a random barcode number
    barcode_number = generate_random_number()
    # Create barcode image using the generated barcode number and save it
    generated = barcode_format(barcode_number)
    # Save the barcode image to the specified save_path
    filename = f"{barcode_number}"
    barcode_path = f"static/img/{filename}"
    
    generated.save(barcode_path)
    # Store the generated barcode number, product name, price, and image path in a dictionary
    data = {
        "barcode_number": barcode_number,
        "product_name": product_name,
        "price": price,
        "image_path": barcode_path
    }
    return data