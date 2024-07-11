
from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
import shutil

@task
def order_robots_from_RobotSpareBin():
    """Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(slowmo=200)
    open_robot_order_website()
    download_orders_file()
    orders = get_orders()
    for order in orders:
        fill_and_submit_robot_data(order)
    archive_receipts()
    clean_up()

def open_robot_order_website():
    """Navigates to the URL and clicks on popup"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")
    close_popup()

def download_orders_file():
    """Downloads CSV file from the given URL"""
    http = HTTP()
    http.download("https://robotsparebinindustries.com/orders.csv", overwrite=True)

def get_orders():
    """Reads the CSV file into a table"""
    library = Tables()
    orders = library.read_table_from_csv("orders.csv", columns=["Order number", "Head", "Body", "Legs", "Address"])
    return orders

def close_popup():
    page = browser.page()
    page.click("text=OK")

def fill_form(order):
    """Fills in the robot order form with given details"""
    page = browser.page()
    # Fill in the Address
    page.fill("#address", order["Address"])
    # Select the Head type
    page.select_option("#head", str(order["Head"]))
    # Fill the Legs type using an attribute selector for name
    leg_input_selector = "input[placeholder='Enter the part number for the legs']"
    page.fill(leg_input_selector, str(order["Legs"]))
    # Select the Body type
    body_value = str(order["Body"])
    # Construct the selector for the body radio button
    body_selector = f"label[for='id-body-{body_value}']"
    # Click on the label corresponding to the body value
    page.click(body_selector)
    # Click Order button
    page.click("text=Order")

def fill_and_submit_robot_data(order):
    """Fills in the robot order details and clicks the 'Order' button"""
    fill_form(order)
    page = browser.page()
    
    while True:
        page.click("#order")
        order_another = page.query_selector("#order-another")
        if order_another:
            pdf_path = store_receipt_as_pdf(int(order["Order number"]))
            screenshot_path = screenshot_robot(int(order["Order number"]))
            embed_screenshot_to_receipt(screenshot_path, pdf_path)
            order_another_bot()
            close_popup()
            break

def store_receipt_as_pdf(order_number):
    """Stores the robot order receipt as a PDF"""
    page = browser.page()
    order_receipt_html = page.locator("#receipt").inner_html()
    pdf = PDF()
    pdf_path = f"output/receipts/{order_number}.pdf"
    pdf.html_to_pdf(order_receipt_html, pdf_path)
    return pdf_path

def screenshot_robot(order_number):
    """Takes a screenshot of the ordered robot"""
    page = browser.page()
    screenshot_path = f"output/screenshots/{order_number}.png"
    page.locator("#robot-preview-image").screenshot(path=screenshot_path)
    return screenshot_path

def embed_screenshot_to_receipt(screenshot_path, pdf_path):
    """Embeds the screenshot into the robot receipt"""
    pdf = PDF()
    pdf.add_watermark_image_to_pdf(image_path=screenshot_path, source_path=pdf_path, output_path=pdf_path)

def order_another_bot():
    """Clicks on the 'Order Another' button to order another bot"""
    page = browser.page()
    page.click("#order-another")

def archive_receipts():
    """Archives all the receipt PDFs into a single ZIP archive"""
    lib = Archive()
    lib.archive_folder_with_zip("./output/receipts", "./output/receipts.zip")

def clean_up():
    """Cleans up the folders where receipts and screenshots are saved"""
    shutil.rmtree("./output/receipts")
    shutil.rmtree("./output/screenshots")
