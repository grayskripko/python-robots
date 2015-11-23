from googleplaces import GooglePlaces  # https://github.com/slimkrazy/python-google-places
import os
import csv

google_places = GooglePlaces("AIzaSyD4GwWevOZYPFeUhWoT7gRzhZHO2biPAU8")
# TYPE_CONVENIENCE_STORE TYPE_FOOD TYPE_SHOPPING_MALL TYPE_STORE
entries = []
queries_str = "Costco\nAndronico\'s\nBianchini\'s\nErewhon\nFalletti Foods\nFresh & Easy\nGelsons\n" \
              "Mollie Stones\nPetco\nRainbow Grocer\nRalphs\nSafeway\nSmart & Final\nSuper King Markets\n" \
              "Target\nTrader Joes\nVons\nWalgreens\nWalmart\nWhole Food Markets"
queries = queries_str.split("\n")

for i in range(len(queries)):
    query_result = google_places.text_search(query="California supermarket \"" + queries[i] + "\"",
                                             types=["grocery_or_supermarket"])
    # query_result = google_places.nearby_search(location='California', keyword='Costco',
    #                                            radius=50000,
    #                                            types=["grocery_or_supermarket"])

    if query_result.has_attributions:
        print(query_result.html_attributions)

    for place in query_result.places:
        place.get_details()  # print (place.details)
        entry = {
            "name": place.name,
            "formatted_address": place.formatted_address,
            "lat": place.geo_location["lat"],
            "lng": place.geo_location["lng"],

            "local_phone_number": place.local_phone_number,
            "map_pointer_url": place.url,
            "website": place.website}
        entries.append(entry)

    if len(entries) > 200:
        keys = entries[0].keys()
        with open(os.environ['OUT'] + '/' + str(i) + '.csv', 'w', newline='') as stream:
            dict_writer = csv.DictWriter(stream, keys)
            dict_writer.writeheader()
            dict_writer.writerows(entries)
        entries = []
