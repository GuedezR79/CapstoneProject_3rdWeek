#!/usr/bin/env python
# coding: utf-8

# # PROJECT WEEK 3: SEGMENTING AND CLUSTERING NEIGHBORHOODS IN TORONTO

# ## Importing Libraries

# In[3]:


get_ipython().system('pip install beautifulsoup4')
get_ipython().system('pip install lxml')
import requests # library to handle requests
import pandas as pd # library for data analsysis
import numpy as np # library to handle data in a vectorized manner
import random # library for random number generation

#!conda install -c conda-forge geopy --yes 
from geopy.geocoders import Nominatim # module to convert an address into latitude and longitude values

# libraries for displaying images
from IPython.display import Image 
from IPython.core.display import HTML 


from IPython.display import display_html
import pandas as pd
import numpy as np
    
# tranforming json file into a pandas dataframe library
from pandas.io.json import json_normalize

get_ipython().system('conda install -c conda-forge folium=0.5.0 --yes')
import folium # plotting library
from bs4 import BeautifulSoup
from sklearn.cluster import KMeans
import matplotlib.cm as cm
import matplotlib.colors as colors

print('Folium installed')
print('Libraries imported.')


# # Part 1: Scraping the Wiki Page with Toronto Neighborhood Information/Cleaning the DataFrame

# In[24]:


Wiki_url = "https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M"
source = requests.get(Wiki_url).text


# In[25]:


soup = BeautifulSoup(source, 'xml')


# In[26]:


table=soup.find('table')


# In[27]:


#Defining dataframe which will consist of three columns: PostalCode, Borough, and Neighborhood
column_names = ['Postalcode','Borough','Neighborhood']
df = pd.DataFrame(columns = column_names)


# In[28]:


# Searching all the postcode, borough, neighborhood 
for tr_cell in table.find_all('tr'):
    row_data=[]
    for td_cell in tr_cell.find_all('td'):
        row_data.append(td_cell.text.strip())
    if len(row_data)==3:
        df.loc[len(df)] = row_data


# In[14]:


df


# ### DATA CLEANING

# #### Remove the Column "BOROUGH" when is Not Assigned

# In[115]:


df1 = df[df.Borough != 'Not assigned']
df1.head(10)


# ####  Separate with comma in rows where Postalcode has multiple Neighborhoods

# In[116]:


df1['Neighborhood'].replace(r' \/ ', ', ', regex=True, inplace=True)


# In[123]:


df1.head(10)


# #### If a cell has a Borough but has a Not assigned Neighborhood, then the Neighborhood  will be the same as the Borough

# In[128]:


df1.loc[df1['Neighborhood'] == 'Not assigned', 'Neighborhood'] = df1['Borough']
df1.head(10)


# In[129]:


df1 = df_clean
df_clean.shape


# # Part 2: Getting Lat/Long of each Neighborhood

# ### Importing the .csv file with geographical coordinates

# In[130]:


df_geograph = pd.read_csv('https://cocl.us/Geospatial_data')
df_geograph.head(10)


# ### Merging the DataFrames with Neighborhoods Names and Geographical Coordinates

# In[131]:


df_geograph.rename(columns={'Postal Code':'Postalcode'},inplace=True)
df_merge = pd.merge(df_clean,df_geograph,on='Postalcode')
df_merge.head(10)


# # Part 3: Explore and cluster the neighborhoods in Toronto

# ## Use only those boroughs which name contains Toronto

# In[132]:


df_Tor = df_merge[df_merge['Borough'].str.contains('Toronto',regex=False)]
df_Tor


# In[43]:


df_Tor.shape


# #### We are going to use Geopy module to locate the Toronto City Geographycal Coordinates (latitude and longitude values)

# In[133]:


address = 'Toronto, ON'

geolocator = Nominatim(user_agent="Toronto")
location = geolocator.geocode(address)
latitude_toronto = location.latitude
longitude_toronto = location.longitude
print('The geograpical coordinate of Toronto are {}, {}.'.format(latitude_toronto, longitude_toronto))


# ### Mapping Toronto City and all the select Neighborhoods for analysis, using Folium

# In[134]:


map_toronto = folium.Map(location=[43.6534817,-79.3839347],zoom_start=10)

for lat,lng,borough,neighborhood in zip(df_Tor['Latitude'],df_Tor['Longitude'],df_Tor['Borough'],df_Tor['Neighborhood']):
    label = '{}, {}'.format(neighborhood, borough)
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
    [lat,lng],
    radius=5,
    popup=label,
    color='blue',
    fill=True,
    fill_color='#3186cc',
    fill_opacity=0.7,
    parse_html=False).add_to(map_toronto)
map_toronto


# #### Using Foursquare API to explore the Toronto neighborhoods venues and segment them.

# ### Define Foursquare Credentials and Version

# In[135]:


CLIENT_ID = '0DSAEW3ODANV1R03KD3OF5LX022QGDFPXVKSRH4NBGQLFA2R' # My Foursquare ID
CLIENT_SECRET = '1QI4UHBZ1REKNCE13P4URE0KACPKS2BA2ZMJNG3B50YOZVG1' # My Foursquare Secret
VERSION = '20180604'
LIMIT = 30
print('My credentials:')
print('CLIENT_ID: ' + CLIENT_ID)
print('CLIENT_SECRET:' + CLIENT_SECRET)


# ### Explore Neighborhoods in Toronto

# In[138]:


def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood', 
                  'Neighborhood Latitude', 
                  'Neighborhood Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)


# #### Next, lets create a code to run the above function on each Toronto neighborhood, then, create a new dataframe called Toronto_venues.

# In[139]:


Toronto_venues = getNearbyVenues(names=df_Tor['Neighborhood'],
                                   latitudes=df_Tor['Latitude'],
                                   longitudes=df_Tor['Longitude']
                                  )
Toronto_venues.head() 


# In[140]:


Toronto_venues.shape


# ### Now, lets see how many venues we have by Neighborhood

# In[141]:


Toronto_venues.groupby('Neighborhood').count()


# In[142]:


print('There are {} uniques categories.'.format(len(Toronto_venues['Venue Category'].unique())))


# ## Now, Lets Analyze Each Neighborhood

# ### We are going to use the One-hot encoding, in order to perform the binarization of Venue Categories found. 

# In[143]:


# one hot encoding
Toronto_Binary = pd.get_dummies(Toronto_venues[['Venue Category']], prefix="", prefix_sep="")

# add neighborhood column back to dataframe
Toronto_Binary['Neighborhood'] = Toronto_venues['Neighborhood'] 

# move neighborhood column to the first column
fixed_columns = [Toronto_Binary.columns[-1]] + list(Toronto_Binary.columns[:-1])
Toronto_Binary.head(15)


# In[144]:


# Lets see the Dimensions of the New Dataframe
Toronto_Binary.shape


# #### Next, let's group rows by neighborhood and by taking the mean of the frequency of occurrence of each category

# In[145]:


toronto_grouped = Toronto_Binary.groupby('Neighborhood').mean().reset_index()
toronto_grouped


# In[146]:


toronto_grouped.shape


# #### We are going to print the top 5 most common venues by neighborhood

# In[147]:


num_top_venues = 5

for hood in toronto_grouped['Neighborhood']:
    print("----"+hood+"----")
    temp = toronto_grouped[toronto_grouped['Neighborhood'] == hood].T.reset_index()
    temp.columns = ['venue','freq']
    temp = temp.iloc[1:]
    temp['freq'] = temp['freq'].astype(float)
    temp = temp.round({'freq': 2})
    print(temp.sort_values('freq', ascending=False).reset_index(drop=True).head(num_top_venues))
    print('\n')


# ### Creating a Dataframe which is ordered by the ten most popular venues by neighborhoods

# #### Firstly, let's write a function to sort the venues in descending order.

# In[148]:


def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)
    
    return row_categories_sorted.index.values[0:num_top_venues]


# #### Then, let's create the new dataframe and display the top 10 venues for each neighborhood.

# In[160]:


num_top_venues = 10

indicators = ['st', 'nd', 'rd']

# create columns according to number of top venues
columns = ['Neighborhood']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

# create a new dataframe
neighborhoods_venues_sorted = pd.DataFrame(columns=columns)
neighborhoods_venues_sorted['Neighborhood'] = toronto_grouped['Neighborhood']

for ind in np.arange(toronto_grouped.shape[0]):
    neighborhoods_venues_sorted.iloc[ind, 1:] = return_most_common_venues(toronto_grouped.iloc[ind, :], num_top_venues)

neighborhoods_venues_sorted.head()


# # Cluster Neighborhoods

# ### Run k-means to cluster the neighborhood into 5 clusters.

# In[161]:


# set number of clusters
k = 4

toronto_grouped_clustering = toronto_grouped.drop('Neighborhood', 1)

# run k-means clustering
kmeans = KMeans(n_clusters=k, random_state=0).fit(toronto_grouped_clustering)

# check cluster labels generated for each row in the dataframe
kmeans.labels_ 
# to change use .astype()


# Let's create a new dataframe that includes the cluster as well as the top 10 venues for each neighborhood.

# In[162]:


# add clustering labels
neighborhoods_venues_sorted.insert(0, 'Cluster_Labels', kmeans.labels_)

toronto_merged = df_Tor

# merge toronto_grouped with toronto_data to add latitude/longitude for each neighborhood
toronto_merged = toronto_merged.join(neighborhoods_venues_sorted.set_index('Neighborhood'), on='Neighborhood')

toronto_merged.head() # check the last columns!


# In[163]:


toronto_merged=toronto_merged.dropna()


# In[164]:


toronto_merged['Cluster_Labels'] = toronto_merged.Cluster_Labels.astype(int)


# In[165]:


# create map
map_clusters = folium.Map(location=[latitude_toronto, longitude_toronto], zoom_start=11)

# set color scheme for the clusters
x = np.arange(k)
ys = [i + x + (i*x)**2 for i in range(k)]
colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
rainbow = [colors.rgb2hex(i) for i in colors_array]

# add markers to the map
markers_colors = []
for lat, lon, poi, cluster in zip(toronto_merged['Latitude'], toronto_merged['Longitude'], toronto_merged['Neighborhood'], toronto_merged['Cluster_Labels']):
    label = folium.Popup(str(poi) + ' Cluster ' + str(cluster), parse_html=True)
    folium.CircleMarker(
        [lat, lon],
        radius=5,
        popup=label,
        color=rainbow[cluster-1],
        fill=True,
        fill_color=rainbow[cluster-1],
        fill_opacity=0.7).add_to(map_clusters)
       
map_clusters


# ## Examining Clustering

# ### Cluster 1

# In[166]:


toronto_merged.loc[toronto_merged['Cluster_Labels'] == 0, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# ### Cluster 2

# In[167]:


toronto_merged.loc[toronto_merged['Cluster_Labels'] == 1, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# ### Cluster 3

# In[168]:


toronto_merged.loc[toronto_merged['Cluster_Labels'] == 2, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]


# ### Cluster 4

# In[169]:


toronto_merged.loc[toronto_merged['Cluster_Labels'] == 3, toronto_merged.columns[[1] + list(range(5, toronto_merged.shape[1]))]]

