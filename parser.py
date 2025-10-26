import json

def parse_flight_data(cash_data, points_data):

    cash_data = json.loads(cash_data)
    points_data = json.loads(points_data)
    flights = {}

    for slice_data in cash_data.get('slices', []):
        flight_number = slice_data['segments'][0]['flight']['flightNumber']
        if flight_number not in flights:
            flights[flight_number] = {}
        
        flights[flight_number]['departure_time'] = slice_data['segments'][0]['legs'][0]['departureDateTime'].split('T')[1].split('.')[0]
        flights[flight_number]['arrival_time'] = slice_data['segments'][0]['legs'][0]['arrivalDateTime'].split('T')[1].split('.')[0]
        
        for pricing in slice_data.get('pricingDetail', []):
            if pricing.get('productType') == 'COACH':
                if 'allPassengerDisplayTotal' in pricing:
                    flights[flight_number]['cash_price_usd'] = pricing['allPassengerDisplayTotal']['amount']
                break

    for slice_data in points_data.get('slices', []):
        flight_number = slice_data['segments'][0]['flight']['flightNumber']
        if flight_number not in flights:
            flights[flight_number] = {}

        for pricing in slice_data.get('pricingDetail', []):
            if pricing.get('productType') == 'COACH':
                flights[flight_number]['points_required'] = pricing.get('perPassengerAwardPoints', 0)
                if 'allPassengerDisplayTotal' in pricing:
                    flights[flight_number]['taxes_fees_usd'] = pricing['allPassengerDisplayTotal']['amount']
                break

    output_flights = []
    for flight_number, data in flights.items():
        if 'cash_price_usd' in data and 'points_required' in data and data.get('points_required', 0) > 0:
            cash_price = data['cash_price_usd']
            taxes = data.get('taxes_fees_usd', 0)
            points = data['points_required']
            
            cpp = round((cash_price - taxes) / points * 100, 2)
            
            output_flights.append({
                "flight_number": f"AA{flight_number}",
                "departure_time": data.get('departure_time'),
                "arrival_time": data.get('arrival_time'),
                "points_required": points,
                "cash_price_usd": cash_price,
                "taxes_fees_usd": taxes,
                "cpp": cpp
            })

    search_metadata = {
        "origin": cash_data['responseMetadata']['origin']['code'],
        "destination": cash_data['responseMetadata']['destination']['code'],
        "date": cash_data['responseMetadata']['departureDate'],
        "passengers": 1,
        "cabin_class": "economy"
    }

    result = {
        "search_metadata": search_metadata,
        "flights": output_flights,
        "total_results": len(output_flights)
    }

    return json.dumps(result, indent=2)
