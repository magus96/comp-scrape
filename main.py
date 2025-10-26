import asyncio
import json
from selenium_driverless import webdriver
from selenium_driverless.scripts.network_interceptor import (
    NetworkInterceptor,
    InterceptedRequest,
    RequestPattern,
    RequestStages
)
from parser import parse_flight_data
import random
import subprocess
import os

# Start Xvfb virtual display
xvfb_process = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1280x720x24'])
os.environ['DISPLAY'] = ':99'

urls = [
    "https://www.aa.com/booking/search?locale=en_US&fareType=Lowest&pax=1&adult=1&type=OneWay&searchType=Revenue&cabin=&carriers=ALL&travelType=personal&slices=%5B%7B%22orig%22:%22LAX%22,%22origNearby%22:false,%22dest%22:%22JFK%22,%22destNearby%22:false,%22date%22:%222025-12-15%22%7D%5D",
    "https://www.aa.com/booking/search?locale=en_US&fareType=Lowest&pax=1&adult=1&type=OneWay&searchType=AWARDS&cabin=&carriers=ALL&travelType=personal&slices=%5B%7B%22orig%22:%22LAX%22,%22origNearby%22:false,%22dest%22:%22JFK%22,%22destNearby%22:false,%22date%22:%222025-12-15%22%7D%5D"
]

async def fetch_url(driver, url_idx, url):
    print(f"Fetching URL {url_idx}...")
    response_data = []
    
    try:
        async def on_request(data: InterceptedRequest):
            await data.continue_request()

        async def on_response(data: InterceptedRequest):
            if "booking/api/search/itinerary" in data.request.url:
                try:
                    body_text = await data.body
                    if isinstance(body_text, bytes):
                        body_text = body_text.decode('utf-8')
                    body = json.loads(body_text)
                    response_data.append(body)
                    await data.continue_response()
                except Exception as e:
                    print(f"  Error parsing response: {e}")
                    try:
                        body_text = await data.body
                        response_data.append(body_text)
                        await data.continue_response()
                    except Exception as e2:
                        print(f"  Error getting body: {e2}")
        
        async with NetworkInterceptor(
            driver,
            on_response=on_response,
            on_request=on_request,
            patterns=[RequestPattern.AnyResponse, RequestPattern.AnyRequest]
        ) as interceptor:
            
            print(f"  Navigating to URL {url_idx}...")
            await driver.get(url, wait_load=True)
            
            start_time = asyncio.get_event_loop().time()
            timeout = 40.0
            request_count = 0
            
            async for data in interceptor:
                request_count += 1
                
                if asyncio.get_event_loop().time() - start_time > timeout:
                    print(f"  Timeout waiting for API response (checked {request_count} requests)")
                    break
                
                if response_data:
                    break
        
        if not response_data:
            print(f"  Warning: No response data captured for URL {url_idx}")
            return None
        
        return response_data
        
    except Exception as e:
        print(f"  Error: {str(e)}")
        return None

async def fetch_all_urls(driver):
    results = []
    for idx, url in enumerate(urls):
        data = await fetch_url(driver, idx, url)
        results.append(data)
    
    return results

async def fetch_all_data(max_retries=3):
    attempt = 0
    
    while attempt < max_retries:
        attempt += 1
        print(f"\n--- Attempt {attempt} ---")
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,720")
        try:
            async with webdriver.Chrome(options=options) as driver:
                all_data = await fetch_all_urls(driver)
                
                if all(data is not None for data in all_data):
                    print("\nSuccessfully fetched data from all URLs")
                    return all_data
                else:
                    print(f"Retrying... ({attempt}/{max_retries})")
                    
        except Exception as e:
            print(f"Error: {str(e)}")
            if attempt < max_retries:
                print(f"Retrying... ({attempt}/{max_retries})")
                await asyncio.sleep(1)
    
    raise Exception(f"Failed to fetch data after {max_retries} attempts")

async def main():
    try:
        all_data = await fetch_all_data(max_retries=3)
        
        parsed_data = parse_flight_data(
            json.dumps(all_data[0][0]) if isinstance(all_data[0][0], dict) else str(all_data[0][0]), 
            json.dumps(all_data[1][0]) if isinstance(all_data[1][0], dict) else str(all_data[1][0])
        )
        print(parsed_data)
        
        with open('output.json', 'w') as f:
            f.write(parsed_data)
        
        
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())