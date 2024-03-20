import os
import shutil
import rasterio
import pandas as pd
import geopandas as gpd
import numpy as np
import pickle
import rasterio
from datetime import date, datetime, timedelta
from rasterio.transform import from_origin
from shapely.geometry import Polygon, Point

'''These functions are to extract SNODAS SWE values for point locations'''

def copy_tif_files(source_dir, destination_dir, frequency):
    '''Function to move downloaded SNODAS tif files to your working directory.
    *******
    Inputs:
    source_dir - str: path to the location of the extracted SNODAS tifs to copy from
    destination_dir - str: path to the desired output folder
    frequency - string: must be either 'daily', 'weekly', or 'd', 'w'. 
    *******
    Note: weekly frequency is set to pull every Monday SNODAS tif. Adjust as needed, i.e. Sundays.
    '''
    
    # Ensure destination directory exists
    os.makedirs(destination_dir, exist_ok=True)
    
    # Ensure frequency is valid
    if frequency not in ['daily', 'weekly', 'd', 'w']:
        raise ValueError("Frequency must be either 'daily' or 'weekly'")
    if frequency == 'd':
        frequency = 'daily'
    elif frequency == 'w':
        frequency = 'weekly'
        
    if frequency == 'weekly': 
        # Iterate through files in the source directory
        for filename in os.listdir(source_dir):
            if filename.endswith(".tif") and filename.startswith("us_swe_"):
                try:
                    # Extract date from the filename
                    date_str = filename.split("_")[2].rstrip("_")
                    file_date = datetime.strptime(date_str, "%Y%m%d")

                    # Check if the file date is on a Monday. Adjust as needed for week start
                    if file_date.weekday() == 0:
                        # Copy the file to the destination directory
                        source_path = os.path.join(source_dir, filename)
                        destination_path = os.path.join(destination_dir, filename)
                        shutil.copy2(source_path, destination_path)
                        print(f"File '{filename}' copied to '{destination_dir}'")
                except ValueError:
                    print(f"Skipping file '{filename}' due to invalid date format.")
                    
    elif frequency == 'daily': 
        # Iterate through files in the source directory
        for filename in os.listdir(source_dir):
            if filename.endswith(".tif") and filename.startswith("us_swe_"):
                try:
                    # Extract date from the filename
                    date_str = filename.split("_")[2].rstrip("_")
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    
                    # Copy the file to the destination directory
                    source_path = os.path.join(source_dir, filename)
                    destination_path = os.path.join(destination_dir, filename)
                    shutil.copy2(source_path, destination_path)
                    print(f"File '{filename}' copied to '{destination_dir}'")
                    
                except ValueError:
                    print(f"Skipping file '{filename}' due to invalid date format.")

def point_preprocess(input_h5, h5_keys, output_dir):
    '''Function to take in a .h5 dictionary of dataframes and adds geometry based on Lat and Long columns. 
    ******
    Inputs:
    input_h5 - str: Path of the input h5 file to modify
    h5_keys - list: List of strings of keys in the h5 file
    output_dir - str: path of output directory to save output files
    ******
    '''

    # checking if the output folders exist, create if not 
    if not os.path.exists(f"{output_dir}/by_region/"): 
        os.makedirs(f"{output_dir}/by_region/")
#     if not os.path.exists(f"{output_dir}/gdfs/"): 
#         os.makedirs(f"{output_dir}/gdfs/")
        
    # Create an empty list to store GeoDataFrames
    gdfs = []

    # Loop through the list of keys and read each dataset into a Pandas DataFrame
    for key in h5_keys:
        df = pd.read_hdf(input_h5, key=key)

        # List of columns to keep
        columns_to_keep = ['Long', 'Lat']
        # Drop columns not in the list
        df = df[columns_to_keep]

        # Save each DataFrame to a CSV file
        csv_filename = f"{output_dir}/by_region/{key}_COORDS.csv"
        df.to_csv(csv_filename, index=True)

        # Create geometry column
        geometry = [Point(xy) for xy in zip(df['Long'], df['Lat'])]
        gdf = gpd.GeoDataFrame(df, geometry=geometry)

#         # Save GeoDataFrame as GeoJSON
#         geojson_file_path = f'{output_dir}/gdfs/{key}_geo.json'
#         gdf.to_file(geojson_file_path, driver='GeoJSON')

        # Append GeoDataFrame to the list
        gdfs.append(gdf)

#     # Display the DataFrame
#     display(gdfs)

    # Merge all GeoDataFrames
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=False), crs=gdfs[0].crs)

    # Save merged GeoDataFrame as GeoJSON
    merged_geojson_file_path = f'{output_dir}/merged_geo.json'
    merged_gdf.to_file(merged_geojson_file_path, driver='GeoJSON')

    # Save merged GeoDataFrame as CSV
    merged_csv_file_path = f'{output_dir}/merged_data.csv'
    merged_gdf.to_csv(merged_csv_file_path, index=True)
    



def extract_values_from_tif_SINGLE(tif_path, input_csv_path, output_csv_path):
    '''EXTRACT SNODAS SWE AT POINTS FOR 1 DATE TIFF'''
    
    # Read CSV file containing latitude and longitude coordinates
    df = pd.read_csv(input_csv_path, index_col=0)
    coordinates = list(zip(df['Lat'], df['Long']))

    
    with rasterio.open(tif_path) as src:
        values = []

        for lat, lon in coordinates:
            row, col = src.index(lon, lat)
            value = src.read(1, window=((row, row+1), (col, col+1)))
            values.append(value[0][0])

    # Add extracted values to the DataFrame
    df['SNODAS_SWE_m'] = extracted_values
    df['SNODAS_SWE_m'] = df['SNODAS_SWE_m']/1000
    
    # Save the updated DataFrame to a new CSV file
    df.to_csv(output_csv_path, index=True)
    print(f"CSV file saved to {output_csv_path}")

    
    

def extract_values_from_tif_REGION(tif_folder_path, csv_folder_path, output_csv_folder_path):
    '''EXTRACT SNODAS SWE AT POINTS FOR ALL TIFFS IN A DIRECTORY --- BY REGION'''
    
    for csv_file in os.listdir(csv_folder_path):
        if csv_file.endswith('.csv'):
            filename = os.path.basename(csv_file)
            print(filename)
            # Split filename
            split_filename = os.path.splitext(filename)[0]
            
            # Read CSV file containing latitude and longitude coordinates
            df = pd.read_csv(os.path.join(csv_folder_path, csv_file), index_col=0)
            coordinates = list(zip(df['Lat'], df['Long']))
    
            # Loop through all .tif files in the folder
            for tif_file in os.listdir(tif_folder_path):
                if tif_file.endswith('.tif'):
                    tif_path = os.path.join(tif_folder_path, tif_file)

                    # Extract values from GeoTIFF file based on coordinates
                    with rasterio.open(tif_path) as src:
                        values = []

                        for lat, lon in coordinates:
                            row, col = src.index(lon, lat)
                            value = src.read(1, window=((row, row+1), (col, col+1)))
                            values.append(value[0][0])

                    # Parse the date from the file name (assuming it's in the format yyyymmdd)
                    date_str = os.path.splitext(tif_file)[0][7:-1]
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                    df[formatted_date] = values
                    df[formatted_date] = df[formatted_date]/1000
    
            # Replace -9999 values with NaN
            df.replace(-9.999, np.nan, inplace=True)
            
#             # Display the updated DataFrame or save it to a new CSV file
#             display(df)
            
            # Save the updated DataFrame to a new CSV file
            df.to_csv(os.path.join(output_csv_folder_path, split_filename+"_SNODAS_m.csv"), index=True)
            print(f"{split_filename} CSV file saved to {output_csv_folder_path}")

            
def extract_values_from_tif_CONUS(tif_folder_path, csv_folder_path, output_csv_path):
    '''EXTRACT SNODAS SWE [meters] AT POINTS FOR ALL TIFFS IN A DIRECTORY --- BY REGION'''
    
    # Read CSV file containing latitude and longitude coordinates
    df = pd.read_csv(csv_folder_path, index_col=0)
    coordinates = list(zip(df['Lat'], df['Long']))
    
    # Loop through all .tif files in the folder
    for tif_file in os.listdir(tif_folder_path):
        if tif_file.endswith('.tif'):
            tif_path = os.path.join(tif_folder_path, tif_file)

            # Extract values from GeoTIFF file based on coordinates
            with rasterio.open(tif_path) as src:
                values = []

                for lat, lon in coordinates:
                    row, col = src.index(lon, lat)
                    value = src.read(1, window=((row, row+1), (col, col+1)))
                    values.append(value[0][0])

            # Parse the date from the file name (assuming it's in the format yyyymmdd)
            date_str = os.path.splitext(tif_file)[0][7:-1]
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            formatted_date = date_obj.strftime('%Y-%m-%d')
            df[formatted_date] = values
            df[formatted_date] = df[formatted_date]/1000

    # Replace -9999 values with NaN
    df.replace(-9.999, np.nan, inplace=True)

#     # Display the updated DataFrame or save it to a new CSV file
#     display(df)
    
        # Save the updated DataFrame to a new CSV file
    df.to_csv(output_csv_path, index=True)
    print(f"CSV file saved to {output_csv_path}")
    

def combine_csv_files(folder_path, ouput_dictionary_path):
    '''COMBINE CSV FILES INTO DICTIONARY OF DATAFRAMES'''
    dataframes_dict = {}

    # List all files in the folder
    files = os.listdir(folder_path)

    # Filter only CSV files
    csv_files = [file for file in files if file.endswith('.csv')]

    # Read each CSV file and store it as a DataFrame in the dictionary
    for csv_file in csv_files:
        file_path = os.path.join(folder_path, csv_file)
        dataframe_name = os.path.splitext(csv_file)[0][:-16]  # Use regions as the DataFrame keys
        dataframes_dict[dataframe_name] = pd.read_csv(file_path, index_col=0)

    with open(ouput_dictionary_path, 'wb') as pickle_file:
        pickle.dump(dataframes_dict, pickle_file)


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    