"""
Name: Zachary Winship
CS230: Section 2
Data: "nuclear_explosions.csv" (Nuclear Explosion Data)
URL: Link to your web application on Streamlit Cloud (if posted)

Description:

This website analyzes nuclear explosion data interactively, it allows the user to explore energy outputs the explosions as well as the explosions type,
both of which are filtered for the chosen country. The website allows the user to see visuals like line plots, pie charts, and lat_long maps to help aid there
exploration of the dataset.
"""
import streamlit as st
import pandas as pd
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import pydeck as pdk

img = Image.open("bikini_atoll_test_photo_2.jpg")


data = pd.read_csv("nuclear_explosions.csv")


# Cleaning any leading or trailing variable names, making then all lowercase
# I also removed any spaces and periods in the variable names I like to have underscore instead of periods
data.columns = data.columns.str.strip().str.lower().str.replace(" ", "_").str.replace(".", "_")

# These columns were spelt wrong for some reason
data['data_yield_upper'] = data['data_yeild_upper']
data['data_yield_lower'] = data['data_yeild_lower']


# Running this shows no missing values (2046 Non-Null) because the range of the df is 2046
data.info()


# In this code I wanted to a little extra data cleaning
# I noticed there wasn't a column for just the date of the observation, so I googled to if there was a pandas function
# To combine these three date columns, https://pandas.pydata.org/docs/reference/api/pandas.to_datetime.html
# On that website it explains how to use the function, I told the function which columns to look for
# Originally it wasn't working because as seen above from the data.info(), these columns where int64
# So I used the .astype(str) which it specifies using on the website. Now there is a new column with the whole data
# E.G 1945-07-16
data['date'] = pd.to_datetime(data['date_year'].astype(str) + '-' +
                               data['date_month'].astype(str) + '-' +
                               data['date_day'].astype(str))



# Creating a new df because the map has to include the column names at latitude and longitude
lat_long_data = data.rename(columns={'location_cordinates_longitude': 'longitude'})
lat_long_data = lat_long_data.rename(columns={'location_cordinates_latitude': 'latitude'})



# Function to convert kilotons into joules
def tnt_to_energy(kilotons, conversion_factor=4184000000000):
    return kilotons * conversion_factor

# Function to get the country average for data_yield
# Because data_yield has an upper and lower bound I take the average of the two as a new column and then take the average of country inputed into the function
# Also takes the argument of whether the user wants to convert to joules, if yes it uses the function above, by default it is false, unless the checkbox is checked
def get_country_average(data, country, energy=False):
    country_data = data[data['weapon_source_country'] == country]
    country_data['average_yield'] = (country_data['data_yield_upper'] + country_data['data_yield_lower']) / 2
    average_yield = country_data['average_yield'].mean()
    if energy:
        return tnt_to_energy(average_yield)
    else:
        return average_yield

# Function for creating a dictionary of the data, it creates an initial dictionary for each country, and then within each country is another dictionary
# This dictionary has keys which are the explosion type, and values which are the count of that type
def create_explosion_type_dict(data):
    country_explosion_dict = {}
    countries = data['weapon_source_country'].unique()
    for country in countries:
        try:
            country_data = data[data['weapon_source_country'] == country]
            explosion_counts = {}
            for data_type in country_data['data_type'].unique():
                count = len(country_data[country_data['data_type'] == data_type])
                explosion_counts[data_type] = count
            country_explosion_dict[country] = explosion_counts
        except:
            print("Error in processing", country)
            continue
    return country_explosion_dict


# Putting the image on the website based on the video from Prof. Frydenburg
st.image(img, width = 1000)
st.title("Nuclear Explosion Data Analysis, CS 230-2")


st.header("Average Explosion Energy Calculation by Country")

# Creating a list of the options for the country select box
countries = data["weapon_source_country"].unique()
# These streamlit functions are used to input the country of choice and if the energy should be converted to joules
energy_country = st.selectbox("Select a Country for Energy Analysis", countries)
energy_option = st.checkbox("Convert from Kilotons to Joules", value = False)
# Creating the min and max values that the user can choose for the date range based on the observations in the df
min_date = data['date'].min()
max_date = data['date'].max()
date_input= [min_date, max_date]
# Intializing the subset data for if the date_input is left blank
data_subset = data

# I thought it would be interesting to filter the data based on dates
# My thought behind this was to see if explosion energy increased a certain time frame, e.g. did the U.S test bigger bombs
# In the 1960s or the 1970s. So I googled this to see if streamlit had this widget, and I found the below link
# https://docs.streamlit.io/develop/api-reference/widgets/st.date_input
# The user is prompted for a date range and then the data is subset to include all observations within this range
if st.checkbox("Select Observation Date Range"):
    date_input = st.date_input("Select date range of Observations (Leave Blank to Include All)", value=[min_date, max_date], min_value = min_date, max_value = max_date)
    data_subset = data[(data['date'] >= pd.to_datetime(date_input[0])) & (data['date'] <= pd.to_datetime(date_input[1]))]

# Widget to display the average explosion energy for the chosen country, uses the above python function get_country_average
if st.button("Calculate Average Explosion Energy"):
    output = get_country_average(data_subset, energy_country, energy = energy_option)
    if energy_option:
        st.write("The average energy for ", energy_country, "is: ", round(output, 2), "Joules")
    else:
        st.write("The average energy for ", energy_country, "is: ", round(output, 2), "Kilotons")

# Again subsets the data by the time frame determined above, and then subsets again by the country chosen
# Then sorts the data by the created column "date"
# Plots the data with date on the x-axis and energy of the explosion on the y-axis, includes labels and titles
# Again my thought behind this was to show when a selected country was using its most powerful nuclear bombs
if st.button("Plot Nuclear Test Energy for Chosen Country and Time"):
    data_subset = data[(data['date'] >= pd.to_datetime(date_input[0])) & (data['date'] <= pd.to_datetime(date_input[1]))]
    data_subset['data_yield_avg'] = (data_subset['data_yield_upper'] + data_subset['data_yield_lower']) / 2
    data_subset = data_subset[data_subset['weapon_source_country'] == energy_country]
    data_sub_sort = data_subset.sort_values(by='date')
    plt.plot(data_sub_sort['date'], data_sub_sort['data_yield_avg'])
    plt.title('Nuclear Test Energy over Chosen Time')
    plt.xlabel('Date')
    plt.ylabel('Nuclear Test Energy (Kilotons)')
    st.pyplot(plt)



st.header("Number of Explosion Type's by Country")

# Allows the user to choose another country for analysis, and then creates a dictionary for just this country, with the types of explosions and count of each

test_type_country = st.selectbox("Select a Country for Test Type Analysis", countries)
country_explosion_dict = create_explosion_type_dict(data)
explosion_data = country_explosion_dict[test_type_country]

# Allows the user to select as many explosion types as the country has
# The user can leave this blank to include all types in the output
keys_input = st.multiselect("Select Explosion Type to Display # (Leave Blank to See All Types)", explosion_data.keys())
# filters the data for only the types selected
key_only_data = data[data['data_type'].isin(keys_input)]
# filters the explosion_data dictionary to only include the keys and respective values if it is in the keys_input
filtered_explosion_data = {key: value for key, value in explosion_data.items() if key in keys_input}

# Creates two different sets of keys and values which will be used later, if the user leaves keys_input blank it will use the keys and values
# If the user enters a value for keys_input it will use the filtered keys and values
keys = explosion_data.keys()
values = explosion_data.values()
keys_filtered = filtered_explosion_data.keys()
values_filtered = filtered_explosion_data.values()


total = 0

# Widget to show the explosion type data for the chosen country and types
if st.button("Show Explosion Type Data"):
    st.write("Number of Explosion by test type for", test_type_country)
    # This includes all types if keys_input is left blank, else it uses the filtered keys and values
    # Displays the count of each key and value in the dictionary, hence it is displaying the type of explosion and how many times it was done
    if len(keys_input) == 0:
        for key, value in explosion_data.items():
                st.write(key, value)
                total += value
    else:
        for key in keys_input:
            st.write(key, explosion_data[key])
            total += explosion_data[key]
    # Displays the total explosions for the chosen types
    st.write("Total Number of Chosen Explosions", total)

    # Again iterates for if keys_input is left blank
    # Plots a countplot used in the PowerPoint slides (Ch. 16, Slide 24)
    # Plots each type and the count of that type
    if len(keys_input) == 0:
        sns.countplot(data = data[data["weapon_source_country"] == test_type_country], x = 'data_type', color = "red")
        plt.title(f"Histogram of Chosen Types for {test_type_country}")
        plt.xlabel("Explosion Type")
        plt.ylabel("Number of Tests")
        st.pyplot(plt)
    else:
        sns.countplot(data = key_only_data[key_only_data["weapon_source_country"] == test_type_country], x = 'data_type', color="red")
        plt.title(f"Histogram of Chosen Types for {test_type_country}")
        plt.xlabel("Explosion Type")
        plt.ylabel("Number of Tests")
        st.pyplot(plt)

    # Removes the plots created above to start plotting the next function, I had to google how to do this, because without it, it was overlapping the plots
    plt.clf()

    # Again iterates for if keys_input is left blank
    # Creates a pie chart for the explosion types chosen
    if len(keys_input) == 0:
        plt.pie(values, labels = keys)
        plt.title(f"Pie Chart of Chosen Types for {test_type_country}")
        st.pyplot(plt)
    else:
        plt.pie(values_filtered, labels = keys_filtered)
        plt.title(f"Pie Chart of Chosen Types for {test_type_country}")
        st.pyplot(plt)


# For each of the maps below I used the links on the project description for pdk.Deck, the links I used are also below
# https://deckgl.readthedocs.io/en/latest/layer.html
# https://deckgl.readthedocs.io/en/latest/tooltip.html

# This first maps plots the location of each explosion and allows the user to hover on the point and see the country that detonated the bomb and also the kilotons of that bomb
# My points were originally very small so a specified a minimum for the radius of the point
# Also the points are black by default and the map is black, so I changed the color to yellow by googling the RGB index for yellow, that's the [255, 255, 0]
st.header("Map of All Nuclear Test Locations")
chart = pdk.Deck(layers=[pdk.Layer("ScatterplotLayer",lat_long_data,pickable=True, get_position='[longitude, latitude]', radius_min_pixels=2, get_fill_color = [255, 255, 0])], tooltip = {"text": "{weapon_source_country}: {data_yield_upper} (Kilotons)"})
st.pydeck_chart(chart)

# This second map creates a heat map of the energy output of each bomb
# The maps plots the location of the bomb and then uses the data_yield_upper to assign the weight of the heat on the map
# I thought it would be a cool additional map to show where the highest energy bombs have been dropped in the world
st.header("Heat Map of Explosion Energy Output")
chart = pdk.Deck(layers=[pdk.Layer("HeatmapLayer",lat_long_data,pickable=True,get_position='[longitude, latitude]', get_weight='data_yield_upper'  )])
st.pydeck_chart(chart)





