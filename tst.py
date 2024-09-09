from playwright.sync_api import sync_playwright
import pandas as pd
import time
from datetime import datetime

def validate_dates(checkin_date_str, checkout_date_str):
    today = datetime.today().date()
    checkin_date = datetime.strptime(checkin_date_str, '%Y-%m-%d').date()
    checkout_date = datetime.strptime(checkout_date_str, '%Y-%m-%d').date()

    if checkin_date <= today:
        raise ValueError("Check-in date must be greater than today's date.")
    if checkout_date <= checkin_date:
        raise ValueError("Check-out date must be greater than check-in date.")

def main():
    checkin_date = '2024-09-08'
    checkout_date = '2024-09-09'
    city = "islamabad"
    city = city.capitalize()

    try:
        validate_dates(checkin_date, checkout_date)
    except ValueError as e:
        print(f"Date validation error: {e}")
        return  # Exit the script if validation fails

    page_url = f'https://www.booking.com/searchresults.en-us.html?checkin={checkin_date}&checkout={checkout_date}&selected_currency=PKR&ss={city}&ssne={city}&ssne_untouched={city}&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_type=city&group_adults=1&no_rooms=1&group_children=0&sb_travel_purpose=leisure'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(page_url, timeout=60000)

        # Adding a slight delay to ensure page elements load
        time.sleep(10)

        hotels_list = []

        while True:
            print(f'Processing page with {len(hotels_list)} entries.')

            try:
                hotels = page.locator('div[data-testid="property-card"]').all()
                print(f'There are {len(hotels)} hotels on this page.')

                for hotel in hotels:
                    hotel_dict = {}
                    try:
                        hotel_dict['hotel'] = hotel.locator('div[data-testid="title"]').inner_text() if hotel.locator('div[data-testid="title"]').count() > 0 else 'N/A'
                        hotel_dict['price'] = hotel.locator('span[data-testid="price-and-discounted-price"]').inner_text() if hotel.locator('span[data-testid="price-and-discounted-price"]').count() > 0 else 'N/A'
                        hotel_dict['score'] = hotel.locator('div[data-testid="review-score"] > div:first-of-type').inner_text() if hotel.locator('div[data-testid="review-score"] > div:first-of-type').count() > 0 else 'N/A'
                        hotel_dict['avg review'] = hotel.locator('div[data-testid="review-score"] > div:nth-of-type(2) > div:first-of-type').inner_text() if hotel.locator('div[data-testid="review-score"] > div:nth-of-type(2) > div:first-of-type').count() > 0 else 'N/A'
                        hotel_dict['reviews count'] = hotel.locator('div[data-testid="review-score"] > div:nth-of-type(2) > div:nth-of-type(2)').inner_text().split()[0] if hotel.locator('div[data-testid="review-score"] > div:nth-of-type(2) > div:nth-of-type(2)').count() > 0 else 'N/A'
                        hotel_dict['distance'] = hotel.locator('span[data-testid="distance"]').inner_text() if hotel.locator('span[data-testid="distance"]').count() > 0 else 'N/A'
                        hotel_dict['address'] = hotel.locator('span[data-testid="address"]').inner_text() if hotel.locator('span[data-testid="address"]').count() > 0 else 'N/A'
                       
                        # Extract the description text
                        hotel_dict['description'] = hotel.locator('div[class*="c777ccb0a3"]').inner_text() if hotel.locator('div[class*="c777ccb0a3"]').count() > 0 else 'N/A'

                    except Exception as e:
                        print(f"An error occurred while processing a hotel: {e}")
                        hotel_dict['hotel'] = 'Error'
                        hotel_dict['price'] = 'Error'
                        hotel_dict['score'] = 'Error'
                        hotel_dict['avg review'] = 'Error'
                        hotel_dict['reviews count'] = 'Error'
                        hotel_dict['distance'] = 'Error'
                        hotel_dict['address'] = 'Error'
                        hotel_dict['description'] = 'Error'

                    hotels_list.append(hotel_dict)

            except Exception as e:
                print(f"An error occurred while processing hotels: {e}")
                break

            # Scroll down to load more hotels
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(10)  # Wait for more hotels to load
                new_hotels = page.locator('div[data-testid="property-card"]').all()
                if len(new_hotels) <= len(hotels_list):
                    print("No new hotels loaded. Ending scrape.")
                    break  # Exit if no new hotels are loaded
            except Exception as e:
                print(f"An error occurred while scrolling or loading more hotels: {e}")
                break

        df = pd.DataFrame(hotels_list)
        df.to_excel(f'{city}-hotels_list.xlsx', index=False)
        # df.to_csv(f'{city}-hotels_list.csv', index=False)

        browser.close()

if __name__ == '__main__':
    main()