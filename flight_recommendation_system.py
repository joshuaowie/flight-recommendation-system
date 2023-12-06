import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

import chart_studio.plotly as py
import plotly.express as px
import cufflinks as cf

init_notebook_mode(connected=True)
cf.go_offline()

import requests
import pandas as pd
from typing import Dict
import json
import streamlit as st
from functools import reduce
# %matplotlib inline

# to display integer or float values to 2 decimal numbers
pd.options.display.float_format = '{:20,.2f}'.format


# set page layout size
st.set_page_config(layout="wide")

# Application title
st.write("""
# Flight Recommendation System

This app recommends flights based on the most cost-effective options. 
""")

# sub header
st.write(" ## Please make sure to Enter flight search parametes at the side bar before continuing below!!! ")

# side header title
st.sidebar.header("Enter flight details")

# Input widgets
# departure date input
departure_date = st.sidebar.date_input("Enter departure date")
st.sidebar.write('Your departure date is:', departure_date)

# string value of inputted date
string_date = str(departure_date)
date_text = str(departure_date) + " 00:00:00.0"

# origin input
origin = st.sidebar.text_input('Enter origin code', 'LOS')
st.sidebar.write('The current origin code is ', origin)

# destination input
destination = st.sidebar.text_input('Enter destination code', 'ABV')
st.sidebar.write('The current destination is ', destination)

# cabin class input
cabin_class = st.sidebar.selectbox(
    'Enter cabin class', ('economy', 'business', 'first'))
st.sidebar.write('You selected: ', cabin_class)

cabin_class_b = st.sidebar.selectbox(
    'Enter travelbeta cabin class in capital letters', ('ECONOMY', 'BUSINESS', 'FIRST'))
st.sidebar.write('You selected:  ', cabin_class_b)

# wakanow cabin class input
wakanow_ticket_class = st.sidebar.selectbox(
    'Select Ticket class where Y(Economy), C(Business), "W"(Premium Economy), "F"(First Class)',
    ('Y', 'W', 'C', 'F'))
st.sidebar.write('You selected:', wakanow_ticket_class)

# number of adults input
adults = st.sidebar.number_input('Insert number of Adults', 1, 100, 1)
st.sidebar.write('The current number of adults is ', adults)

# Tiqwa API key input
# tiqwa_api_key = st.sidebar.text_input("Enter Tiqwa API Key")
# st.sidebar.write('Your Tiqwa API Key is ', tiqwa_api_key)

tiqwa_api_key = "sandbox_YmRiM2RlMmEtNmY5ZS00NmU0LWI1MjQtZDZmZGViYjFhYzQ5"

# to make multiple buttons clickable one after the other
if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

# session state to remeber actions of the buttons clicked


def callback():
    st.session_state.button_clicked = True

# allow_output_mutation=True
# Link actions performed by each button to scrape tiqwa flights
if (st.sidebar.button('Scrape Travelbeta', key=1, on_click=callback) or st.session_state.button_clicked):
    @st.cache_data()
    def tiqwa():
        url: str = "https://sandbox.tiqwa.com/v1/flight/search"

        params: Dict = {

            "departure_date": departure_date,
            "return_date": "",
            "origin": origin,
            "destination": destination,
            "adults": adults,
            "cabin": cabin_class
        }

        headers = {
            "Authorization": "Bearer " + tiqwa_api_key,
            "Content-Type": "application/json"
        }

        # use get request to collect the flight contents of Tiqwa api
        response = requests.get(url, params=params, headers=headers)

        request = response.json()

        # turn the json file to dataframe
        tiqwa_data = pd.DataFrame(request)

        # select price table from the dataframe
        price = tiqwa_data[['id', 'amount', 'currency', 'outbound_stops']]

        # flatten outbound flights cloumn to a dataframe table
        outbound = pd.json_normalize(json.loads(tiqwa_data.to_json(
            orient='records')), record_path='outbound', meta=['id'])

        # merge price and outbound tables
        tiqwa_merge = pd.merge(price, outbound, on='id')

        # select the required flight fields from the merged table
        tiqwa_flights = tiqwa_merge[['id', 'amount', 'currency', 'cabin_type', 'departure_time', 'arrival_time', 'duration', 'airline_details.code', 'airline_details.name',
                                    'flight_number', 'airport_from', 'airport_to', 'outbound_stops']]
        tiqwa_flights = tiqwa_flights.add_prefix('travelbeta_')
        # visualize the final table
        return tiqwa_flights
else:
    st.sidebar.write('No Travelbeta Data scraped please scrape data')

# assign tiqwa scraped dataframe function to variable
tiqwa_data = tiqwa()



# Preprocess dataframe to show correct form of tiqwa data
tiqwa_data['flight_number'] = tiqwa_data['travelbeta_flight_number'].str.replace(
    '-', '')
tiqwa_data.drop(
    tiqwa_data.index[tiqwa_data['travelbeta_airport_from'] != origin], inplace=True)
tiqwa_data.reset_index(drop=True, inplace=True)


# Link actions performed by each button to scrape wakanow flights
if (st.sidebar.button('Scrape Wakanow Flight', key=2, on_click=callback) or st.session_state.button_clicked):
    @st.cache_data()
    def wakanow():
        wakanow_url: str = "https://flights.wakanow.com/api/flights/Search"

        wakanow_data: Dict = {"FlightSearchType": "Oneway", "Adults": adults, "Children": 0, "Infants": 0, "GeographyId": "NG", "Ticketclass": wakanow_ticket_class, "TargetCurrency": "NGN", "Itineraries": [
            {"Destination": destination, "Departure": origin, "DepartureDate": string_date, "Ticketclass": wakanow_ticket_class}], "FlightRequestView": "{\"FlightSearchType\":\"Oneway\",\"Adults\":1,\"Children\":0,\"Infants\":0,\"GeographyId\":\"NG\",\"Ticketclass\":\"Y\",\"TargetCurrency\":\"NGN\",\"Itineraries\":[{\"Destination\":\"LON\",\"Departure\":\"LOS\",\"DepartureDate\":\"8/26/2022\",\"Ticketclass\":\"Y\",\"DepartureLocationMetaData\":{\"AirportCode\":\"LOS\",\"Description\":\"Murtala Muhammed International Airport (LOS)\",\"CityCountry\":\"Lagos, Nigeria\",\"City\":\"Lagos\",\"Country\":\"Nigeria\",\"Prority\":9},\"DestinationLocationMetaData\":{\"AirportCode\":\"LON\",\"Description\":\"Heathrow (LHR)\",\"CityCountry\":\"London, United Kingdom\",\"City\":\"London\",\"Country\":\"United Kingdom\",\"Prority\":10},\"ReturnDate\":null}]}"}

        wakanow_headers: Dict = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
        }

        # use POST request to collect the flight code for wakanow flight content
        first_request = requests.post(wakanow_url, data=json.dumps(
            wakanow_data), headers=wakanow_headers)
        
        result_code: str = first_request.json()
        
        # use get request to collect the flight contents of wakanow website
        result_request = requests.get(
            f"https://flights.wakanow.com/api/flights/SearchV2/{result_code}/NGN", headers=wakanow_headers)

        # Make sure that the request as successul

        # wakanow search data
        flight_result = result_request.json()['SearchFlightResults']

        # search results data as a dataframe
        wakanow_data = pd.json_normalize(flight_result, max_level=1)

        # select required columns from the dataframe
        flight_combination = wakanow_data[[
            'FlightId', 'FlightCombination.Flights', 'FlightCombination.Price']]

        # flatten out the flightcombinations nested json table
        hi = pd.json_normalize(json.loads(
            flight_combination.to_json(orient='records')), max_level=1)

        # rename columns to appropriate properties to avoid nameclashes during merge
        hi.rename({'FlightId': 'SearchId', 'FlightCombination.Price.Amount': 'amount',
                   'FlightCombination.Price.CurrencyCode': 'currency'}, axis=1, inplace=True)

        # flatten out the flights column to retrieve flight details
        flights = pd.json_normalize(json.loads(hi.to_json(
            orient='records')), record_path='FlightCombination.Flights', meta=['SearchId'])
        # drop missing values if any on FlightId column
        flights.dropna(subset=['FlightId'], how='any', inplace=True)
        # reset index
        flights.reset_index(drop=True, inplace=True)

        # flightlegs dataframe i.e the inbetween flight routes
        flightlegs = pd.json_normalize(json.loads(flights.to_json(
            orient='records')), record_path='FlightLegs', meta=['SearchId'])

        # merge hi and flights tables
        wakanow_merge = pd.merge(hi, flights, on='SearchId')
        wakanow_merge.drop('FlightCombination.Flights',
                           axis=1, inplace=True)
        wakanow_merge = pd.merge(
            wakanow_merge, flightlegs[['SearchId', 'CabinClassName']], on='SearchId')

        # select required flight features in a table
        wakanow_flights = wakanow_merge[['SearchId', 'amount', 'currency', 'CabinClassName', 'DepartureTime', 'ArrivalTime', 'TripDuration',
                                        'Airline', 'AirlineName', 'Name', 'DepartureCode', 'ArrivalCode', 'Stops']]

        wakanow_flights = wakanow_flights.add_prefix('wakanow_')
        return wakanow_flights

else:
    st.sidebar.write('No Wakanow Data scraped please scrape data')

# assign scraping function to variable
wakanow_data = wakanow()
wakanow_d = wakanow()



# Preprocess dataframe to show correct form of data
wakanow_d['wakanow_FlightNumber'] = wakanow_d['wakanow_Airline'] + \
    wakanow_d['wakanow_Name']
wakanow_d['flight_number'] = wakanow_d['wakanow_FlightNumber']
wakanow_d.drop(
    wakanow_d.index[wakanow_d['wakanow_DepartureCode'] != origin], inplace=True)
wakanow_d.reset_index(drop=True, inplace=True)

# Link actions performed by each button to scrape travelstart flights
if (st.sidebar.button('Scrape Travelstart Flight', key=3, on_click=callback) or st.session_state.button_clicked):
    @st.cache_data()
    def travelstart():
        travelstart_url: str = "https://wapi.travelstart.com/website-services/api/search/?affid=ng-adwords-brand&gclid=CjwKCAjwrZOXBhACEiwA0EoRD2l3p-TJt9jX6NQq7_17MPfPiIJ6cMWbDi1-5-XQZrv-EoVIl9RC0hoCrA8QAvD_BwE&gclsrc=aw.ds&language=en&correlation_id=ae2a22e4-0c64-4a28-81c3-01fd9a2d1690"

        travelstart_data: Dict = {"tripType": "oneway", "isNewSession": True, "travellers": {"adults": adults, "children": 0, "infants": 0}, "moreOptions": {"preferredCabins": {"display": "Economy", "value": cabin_class}, "isCalendarSearch": False}, "outboundFlightNumber": "", "inboundFlightNumber": "", "itineraries": [{"id": "979eed77-cb21-48df-9e7f-00644fb1ce4a", "origin": {"value": {"type": "airport", "city": "Lagos", "airport": "Murtala Muhammed International Airport", "iata": origin, "code": origin, "country": "Nigeria", "countryIata": "NG", "locationId": "airport_LOS"}, "display": "Lagos Murtala Muhammed International Airport"}, "destination": {
            "value": {"type": "city", "city": "London", "airport": "All Airports", "iata": destination, "code": destination, "country": "United Kingdom", "countryIata": "GB", "locationId": "GB_city_LON"}, "display": "London All Airports"}, "departDate": string_date, "returnDate": "null"}], "searchIdentifier": "", "locale": {"country": "NG", "currentLocale": "en", "locales": []}, "userProfileUsername": "", "businessLoggedOnToken": "", "isDeepLink": False}

        travelstart_headers: Dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "ts-country": "NG",
            "ts-language": "en",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        }

        # use get request to collect the flight contents of travelstart
        first_request = requests.post(travelstart_url, data=json.dumps(
            travelstart_data), headers=travelstart_headers)

        result: str = json.loads(first_request.text)

        # dataframe from json flight data
        travelstart_data = pd.DataFrame(result)

        # itineraries table
        itineraries_index = travelstart_data.loc['itineraries']['response']
        itineraries = pd.json_normalize(itineraries_index, max_level=0)

        # price table
        price = itineraries[['id', 'amount', 'currencyCode']]
        price['amount'] = price['amount'].astype(float)

        # flatte out the list of nested json table to get flight details
        odolist = pd.json_normalize(json.loads(itineraries.to_json(
            orient='records')), record_path='odoList', meta=['id'])

        # flatten out list of nested json to get flight segments
        travelstart = pd.json_normalize(json.loads(odolist.to_json(
            orient='records')), record_path='segments', meta=['id'])

        # merge price and flight details(travelstart) table
        travelstart_merge = pd.merge(price, travelstart, on='id')

        # select required flight details and price
        travelstart_flights = travelstart_merge[['id', 'amount', 'currencyCode', 'cabinClass', 'departureDateTime', 'arrivalDateTime',
                                                'duration', 'airlineCode', 'flightNumber', 'origCode', 'destCode', 'technicalStops']]

        travelstart_flights = travelstart_flights.add_prefix(
            'travelstart_')
        return travelstart_flights

else:
    st.sidebar.write('No Travelstart Data scraped please scrape data')

# assign scraping funtion to variable
travelstart_data = travelstart()
travelstart_d = travelstart()

# Preprocess dataframe to show correct form of travelstart data
travelstart_d.drop(
    travelstart_d.index[travelstart_d['travelstart_origCode'] != origin], inplace=True)
travelstart_d.reset_index(drop=True, inplace=True)
travelstart_d['flight_number'] = travelstart_d['travelstart_flightNumber']



if (st.sidebar.button('Scraper', key=4, on_click=callback) or st.session_state.button_clicked):
    @st.cache_data()
    def travelbeta():
        travelbeta_url: str = "https://api.travelbeta.com/v1/api/flight"

        travelbeta_data: Dict = {"tripDetails": [{"originAirportCode": origin, "destinationAirportCode": destination, "departureDate": date_text, "cabinType": cabin_class_b}], "flightType": "ONE_WAY",
                                 "numberOfAdult": adults, "numberOfChildren": 0, "numberOfInfant": 0, "uniqueSession": "1LcgSi4QOi7yGZ4", "directFlight": True, "refundable": False, "isDayFlight": True, "prefferedAirlineCodes": []}

        travelbeta_headers: Dict = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "x-api-key": "24c9mti53ykc31z1t5u5",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        }

        # use get request to collect the flight contents of travelbeta
        first_request = requests.post(travelbeta_url, data=json.dumps(
            travelbeta_data), headers=travelbeta_headers)

        result: str = json.loads(first_request.text)

        # take note to assign cabin type to final dataframe
        # dataframe of travelstart flight data
        flights_df = pd.json_normalize(result, max_level=1)

        # flatten out nested jsons in dataframe
        travelbeta = pd.json_normalize(json.loads(flights_df.to_json(
            orient='records')), record_path='data.airPricedIternaryList')

        # convert amount in kobo to naira
        travelbeta['amountInNaira'] = travelbeta['amountInKobo'] / 100

        # origin to destination data and drop airline name to avoid name clashes during merge
        lists = pd.json_normalize(json.loads(travelbeta.to_json(
            orient='records')), record_path='airOriginDestinationList', meta=['id'])
        lists.drop('airlineName', axis=1, inplace=True)

        # merge both dataframes into a single dataframe
        travelbeta_merge = pd.merge(travelbeta, lists, on='id')

        # select required information from the dataframe
        travelbeta_flights = travelbeta_merge[['id', 'amountInNaira', 'firstDepartureTime', 'lastArrivalTime', 'totalFlightTimeInMs',
                                               'airlineCode', 'airlineName', 'originCityCode', 'destinationCityCode', 'totalStop']]

        travelbeta_flights = travelbeta_flights.add_prefix('travelbeta_')

        return travelbeta_flights

else:
    st.sidebar.write('Check scraper')

travelbeta_data = travelbeta()







# Link actions performed by button to combine flights
if st.button('Combine all Flight data', key=5):
    tiq_flights = pd.concat(
        [tiqwa_data, travelstart_data, wakanow_data], axis=1)

    # flight_slice = tiq_flights[['travelbeta_flight_number', 'travelbeta_amount', 'travelbeta_departure_time', 'travelbeta_airline_details.name', 'travelbeta_airport_from', 'travelbeta_airport_to',
    #                             'wakanow_FlightNumber', 'wakanow_amount', 'wakanow_DepartureTime', 'wakanow_AirlineName', 'wakanow_DepartureCode', 'wakanow_ArrivalCode',
    #                             'travelstart_flightNumber', 'travelstart_amount', 'travelstart_departureDateTime', 'travelstart_airlineCode', 'travelstart_origCode', 'travelstart_destCode']]

    all_flights = pd.concat(
        [wakanow_data, travelstart_data, travelbeta_data], axis=1)

    st.dataframe(all_flights)
    st.write('------')


    data_frames = [tiqwa_data, wakanow_d, travelstart_d]

    df_merged = reduce(lambda left, right: pd.merge(
    left, right, on=['flight_number'], how='outer'), data_frames)
    flight_route = df_merged[['flight_number', 'travelbeta_flight_number', 'travelbeta_amount', 'travelbeta_departure_time', 'travelbeta_airline_details.name', 'travelbeta_airport_from', 'travelbeta_airport_to',
                        'wakanow_FlightNumber', 'wakanow_amount', 'wakanow_DepartureTime', 'wakanow_AirlineName', 'wakanow_DepartureCode', 'wakanow_ArrivalCode',
                        'travelstart_flightNumber', 'travelstart_amount', 'travelstart_departureDateTime',  'travelstart_airlineCode', 'travelstart_origCode', 'travelstart_destCode']]
    flight_route.dropna(
    subset=['travelbeta_flight_number'], how='any', inplace=True)
    flight_route.dropna(
    subset=['wakanow_FlightNumber'], how='any', inplace=True)
    flight_route.dropna(
    subset=['travelstart_flightNumber'], how='any', inplace=True)
    flight_route.reset_index(drop=True, inplace=True)

    flight_route.drop_duplicates(subset="flight_number", keep='first', inplace=True)
    flight_route.reset_index(drop=True, inplace=True)

    flight_route['wakanow_flightAmount_increase_by_travelbeta'] = flight_route['wakanow_amount'] - \
    flight_route['travelbeta_amount']
    flight_route['travelstart_flightAmount_increase_by_travelbeta'] = flight_route['travelstart_amount'] - \
    flight_route['travelbeta_amount']
    flight_route['wakanow_flightAmount_Percentageincrease_by_travelbeta'] = (
    (flight_route['wakanow_amount'] - flight_route['travelbeta_amount']) / flight_route['travelbeta_amount']) * 100
    flight_route['travelstart_flightAmount_Percentageincrease_by_travelbeta'] = (
    (flight_route['travelstart_amount'] - flight_route['travelbeta_amount']) / flight_route['travelbeta_amount']) * 100
    flight_route['travelbeta_flight_route'] = flight_route['travelbeta_airport_from'] + \
    "-" + flight_route['travelbeta_airport_to']


    st.write('#### Similar Flights Data by Flight Number')
    st.dataframe(flight_route)
    st.write('------')
else:
    st.write("No Combined data! Press to combine scraped data")

# Warning text to fully display page contents
st.markdown(
    "### close sidebar tab to fully view recommended flight options below!")

# assign dataframe contents to be displayed on dashboard
for i in range(len(flight_route)):
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Flight Number",
                f"{flight_route['flight_number'].iloc[i]}")
    col2.metric("Flight Route",
                f"{flight_route['travelbeta_flight_route'].iloc[i]}")
    col3.metric(f"Travelbeta {flight_route['travelbeta_departure_time'].iloc[i]}",
                f"NGN {flight_route['travelbeta_amount'].iloc[i]}", f"0%")
    col4.metric(f"Wakanow {flight_route['wakanow_DepartureTime'].iloc[i]}", f"NGN {flight_route['wakanow_amount'].iloc[i]}",
                f"{flight_route['wakanow_flightAmount_Percentageincrease_by_travelbeta'].iloc[i]}%")
    col5.metric(f"Travelstart {flight_route['travelstart_departureDateTime'].iloc[i]}",
                f"NGN {flight_route['travelstart_amount'].iloc[i]}", f"{flight_route['travelstart_flightAmount_Percentageincrease_by_travelbeta'].iloc[i]}%")




# flight data analysis

fig = px.bar(all_flights, y=['wakanow_amount', 'travelstart_amount', 'travelbeta_amountInNaira'], labels={'value': 'company flight amount'},
             hover_data=['wakanow_DepartureCode', 'wakanow_ArrivalCode', 'wakanow_DepartureTime', 'wakanow_ArrivalTime'])

fig.update_layout(bargap=0.2)


# create wakanow subplots layout
fig_wakanow = make_subplots(rows=1, cols=2, shared_yaxes=False, subplot_titles=(
    "Wakanow Airline by Amounts", "Wakanow Arrival and Departure Time by Amount Distribution"))

# add subplots to the layout
fig_wakanow.add_trace(go.Histogram(
    x=wakanow_data['wakanow_AirlineName'], y=wakanow_data['wakanow_amount'], name="airline flights amounts", histfunc="sum"), 1, 1)

fig_wakanow.add_trace(go.Histogram(
    x=wakanow_data['wakanow_ArrivalTime'], y=wakanow_data['wakanow_amount'], name="arrival time", histfunc="sum"), 1, 2)

fig_wakanow.add_trace(go.Histogram(x=wakanow_data['wakanow_DepartureTime'],
                      y=wakanow_data['wakanow_amount'], name="departure time", histfunc="sum"), 1, 2)


# Update xaxis properties
fig_wakanow.update_xaxes(title_text="airlines", row=1, col=1)
fig_wakanow.update_xaxes(title_text="arrival and departure time", row=1, col=2)


# Update yaxis properties
fig_wakanow.update_yaxes(title_text="price amount ", row=1, col=1)
fig_wakanow.update_yaxes(title_text="price amount",  row=1, col=2)


# update layout
fig_wakanow.update_layout(showlegend=True, bargap=0.2,
                          title_text="Wakanow plots")


# create travelstart subplots layout
fig_travelstart = make_subplots(rows=1, cols=2, shared_yaxes=False, subplot_titles=(
    "Travelstart Airline by Amounts", "Travelstart Arrival and Departure Time by Amount Distribution"))

# add subplots to the layout
fig_travelstart.add_trace(go.Histogram(x=travelstart_data['travelstart_airlineCode'],
                          y=travelstart_data['travelstart_amount'], name="airline flights amounts", histfunc="sum"), 1, 1)

fig_travelstart.add_trace(go.Histogram(x=travelstart_data['travelstart_arrivalDateTime'],
                          y=travelstart_data['travelstart_amount'], name="arrival time", histfunc="sum"), 1, 2)

fig_travelstart.add_trace(go.Histogram(x=travelstart_data['travelstart_departureDateTime'],
                          y=travelstart_data['travelstart_amount'], name="departure time", histfunc="sum"), 1, 2)


# Update xaxis properties
fig_travelstart.update_xaxes(title_text="airlines", row=1, col=1)
fig_travelstart.update_xaxes(
    title_text="arrival and departure time", row=1, col=2)


# Update yaxis properties
fig_travelstart.update_yaxes(title_text="price amount ", row=1, col=1)
fig_travelstart.update_yaxes(title_text="price amount", row=1, col=2)


# update layout
fig_travelstart.update_layout(
    showlegend=True, bargap=0.2, title_text="Travelstart plots")


# create travelbeta subplot layout
fig_travelbeta = make_subplots(rows=1, cols=2, shared_yaxes=False, subplot_titles=(
    "Travelbeta Airline by Amounts", "Travelbeta Arrival and Departure Time by Amount Distribution"), )
#                     specs=[[{"colspan": 2}, None]
#                            [{"colspan": 2}, None]])

# add subplots to the layout
fig_travelbeta.add_trace(go.Histogram(x=travelbeta_data['travelbeta_airlineName'],
                         y=travelbeta_data['travelbeta_amountInNaira'], name="airline flights amounts", histfunc="sum"), 1, 1)

fig_travelbeta.add_trace(go.Histogram(x=travelbeta_data['travelbeta_lastArrivalTime'],
                         y=travelbeta_data['travelbeta_amountInNaira'], name="arrival time", histfunc="sum"), 1, 2)

fig_travelbeta.add_trace(go.Histogram(x=travelbeta_data['travelbeta_firstDepartureTime'],
                         y=travelbeta_data['travelbeta_amountInNaira'], name="departure time", histfunc="sum"), 1, 2)


# Update xaxis properties
fig_travelbeta.update_xaxes(title_text="airlines", row=1, col=1)
fig_travelbeta.update_xaxes(
    title_text="arrival and departure time", row=1, col=1)


# Update yaxis properties
fig_travelbeta.update_yaxes(title_text="price amount ", row=1, col=1)
fig_travelbeta.update_yaxes(title_text="price amount", row=1, col=2)


# update layout
fig_travelbeta.update_layout(
    showlegend=True, bargap=0.2, title_text="Travelbeta plots")


st.write(fig)
st.write(fig_wakanow)
st.write(fig_travelstart)
st.write(fig_travelbeta)


