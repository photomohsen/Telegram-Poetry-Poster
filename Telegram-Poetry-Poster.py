import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import random
import arabic_reshaper
from bidi.algorithm import get_display
from persiantools.jdatetime import JalaliDate
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv('bot_token')
CHAT_ID = os.getenv('chat_id')

def download_font(url, font_path):
    response = requests.get(url)
    with open(font_path, 'wb') as f:
        f.write(response.content)

def get_poem_lines():
    response = requests.get('https://api.ganjoor.net/api/ganjoor/hafez/faal')
    if response.status_code == 200:
        poem = response.json()
        verses = poem['verses']
        if len(verses) > 1:
            odd_indices = [i for i in range(len(verses) - 1) if i % 2 == 0]
            random_index = random.choice(odd_indices)
            random_lines = "\n".join([verses[random_index]['text'], verses[random_index + 1]['text']])
        else:
            random_lines = verses['text']
        return random_lines
    return None

def post_to_telegram(image_path, poem_text):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto'
    with open(image_path, 'rb') as image_file:
        data = {'chat_id': CHAT_ID, 'caption': poem_text}
        files = {'photo': image_file}
        response = requests.post(url, data=data, files=files)
    return response.status_code

def convert_to_persian_numbers(number_str):
    persian_digits = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    return ''.join(persian_digits.get(digit, digit) for digit in number_str)

def get_persian_day_name(weekday):
    persian_days = [
        'شنبه', 'یک‌شنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه'
    ]
    return persian_days[weekday]

def main():
    # Download the Vazirmatn font
    font_url = "https://github.com/rastikerdar/vazirmatn/blob/master/fonts/ttf/Vazirmatn-Regular.ttf?raw=true"
    font_path = "Vazirmatn-Regular.ttf"
    download_font(font_url, font_path)

    # Fetch a random image from the Picsum Photos API
    response = requests.get('https://picsum.photos/1200')
    image_data = response.content

    # Open the image using PIL
    image = Image.open(BytesIO(image_data))

    # Get the poem lines
    poem_lines = get_poem_lines()

    # Get the Persian date and day name
    persian_date = JalaliDate.today()
    persian_date_str = persian_date.strftime("%Y/%m/%d")
    persian_date_str = convert_to_persian_numbers(persian_date_str)
    persian_day_name = get_persian_day_name(persian_date.weekday())
    persian_date_text = f"{persian_day_name} {persian_date_str}"

    if poem_lines:
        # Reshape and display the text correctly for Arabic/Persian languages
        reshaped_text = arabic_reshaper.reshape(poem_lines)
        bidi_text = get_display(reshaped_text)

        # Reshape and display the Persian date text correctly
        # Reshape and display "فال حافظ"
        reshaped_faale_hafez = arabic_reshaper.reshape("فال حافظ-")
        reshaped_date_text = arabic_reshaper.reshape(persian_date_text)
        bidi_date_text = get_display(reshaped_date_text) + get_display(reshaped_faale_hafez)

        # Create a new image with extra space for the box and frame
        new_width = image.width + 20
        new_height = image.height + 280  # Increased height to accommodate the date ribbon
        new_image = Image.new("RGB", (new_width, new_height), "white")

        # Paste the original image onto the new image with a frame of 10 pixels
        new_image.paste(image, (10, 90))  # Adjusted position to leave space for the date ribbon

        # Draw the text box on the new image
        draw = ImageDraw.Draw(new_image)

        # Load the Vazirmatn font file and set the font size
        font_size = 60
        font = ImageFont.truetype(font_path, font_size)

        # Draw the Persian date ribbon at the top
        date_bbox = draw.textbbox((0, 0), bidi_date_text, font=font)
        date_position = ((new_width - (date_bbox - date_bbox)) // 2, 10)
        draw.text(date_position, bidi_date_text, font=font, fill="black")

        # Calculate the position to center the text
        text_bbox = draw.textbbox((0, 0), bidi_text, font=font)
        text_position = ((new_width - (text_bbox - text_bbox)) // 2,
                         (new_height - (text_bbox - text_bbox)) // 2 + image.height // 2 + 30)

        draw.text(text_position, bidi_text, font=font, fill="black")

        # Save the image with text and frame
        image_path = "image_with_text_and_frame.png"
        new_image.save(image_path)

        # Send the image to Telegram with the caption
        status_code = post_to_telegram(image_path, poem_lines)

        print("Message sent successfully!" if status_code == 200 else f"Failed to send message. Status code: {status_code}")

if __name__ == "__main__":
    main()