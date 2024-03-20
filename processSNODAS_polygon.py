import os
import glob
import random
from tqdm import tqdm
import rioxarray as rxr
import rasterio
import geopandas as gpd
from shapely.geometry import Point, mapping
from datetime import datetime

'''These functions are to extract SNODAS SWE values [meters] for a polygon shapefile AOI'''

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

                    
                    
def area_clip(input_tif_path, output_path, clip_aoi_path, cwd):
    '''inner function of process_tif_files. Clips raster files to AOI'''
    
    # Open the input raster file
    input_ds = rxr.open_rasterio(input_tif_path,masked=True).squeeze()
    crop_extent = gpd.read_file(f"{cwd}{clip_aoi_path}")
    
    # Perform the clipping
    clipped_ds = input_ds.rio.clip(crop_extent.geometry.apply(mapping))
    clipped_ds.rio.to_raster(output_path)
    

    
def process_tif_files(input_directory, output_directory, clip_aoi_path, cwd):
    '''clips all tif files in a directory to a polygon shapefile AOI'''
    
    # Ensure the output directory exists
    os.makedirs(f"{cwd}{output_directory}", exist_ok=True)
    
    # Find all .tif files in the input directory
    tif_files = glob.glob(os.path.join(f"{cwd}{input_directory}", '*.tif'))
    
    prefix='_clipped_'
    
    for tif_file in tqdm(tif_files, desc="Processing Files", unit="file"):
        # Generate output file path with the specified prefix
        output_file = os.path.join(f"{cwd}{output_directory}", f"{prefix}{os.path.basename(tif_file)}")
        
        # Perform clipping
        area_clip(tif_file, output_file, clip_aoi_path, cwd)
        
        # Print the progress bar update
        tqdm.write(f"Clipped: {os.path.basename(tif_file)} -> {os.path.basename(output_file)}")


        
def extract_datetime_from_filename(filename):
    ''' Inner function of extract_multiple_dates.Finds date to extract from SNODAS tiff filename'''
    # Extract the date part from the filename
    date_str = filename.split('_')[-2]

    # Parse the date string into a datetime object
    try:
        datetime_obj = datetime.strptime(date_str, '%Y%m%d')
        formatted_datetime = datetime_obj.strftime('%m-%d-%Y')
        return formatted_datetime
    except ValueError:
        print(f"Error: Unable to parse date from {filename}")
        return None

    if formatted_datetime:
        print(f"Formatted datetime from '{filename}': {formatted_datetime}")
    else:
        print("Datetime extraction failed.")
    

    
def extract_multiple_dates(input_tif_directory, output_csv_path, cwd):
    '''Extracts SNODAS SWE value [meters] for every lat,long in clipped area'''
    # Find all .tif files in the input directory
    tif_files = glob.glob(os.path.join(input_tif_directory, '*.tif'))
    tif_files = sorted(tif_files)
  
    # Flag to indicate the first file
    first_file_processed = False

    for tif_file in tqdm(tif_files, desc="Processing Files", unit="file"):
        # Check if it's the first file to initiate formatted df
        if not first_file_processed:
            rds = rxr.open_rasterio(tif_file,masked=True)
            rds = rds.squeeze().drop("spatial_ref").drop("band")

            formatted_datetime = extract_datetime_from_filename(tif_file)
            rds.name = formatted_datetime
            df = rds.to_dataframe().reset_index()
            df_formatted = rds.to_dataframe().reset_index()
            df_formatted[formatted_datetime] = df[formatted_datetime]/1000
            
            if 'x' in df_formatted.columns and 'y' in df_formatted.columns:
                df_formatted.rename(columns={'x': 'Long', 'y': 'Lat'}, inplace=True)

            first_file_processed = True
            
        else:
            rds = rxr.open_rasterio(tif_file,masked=True)
            rds = rds.squeeze().drop("spatial_ref").drop("band")

            formatted_datetime = extract_datetime_from_filename(tif_file)
            rds.name = formatted_datetime
            df = rds.to_dataframe().reset_index()
            df_formatted[formatted_datetime] = df[formatted_datetime]/1000
            pass
        
#     display(df_formatted)    
    df_formatted.to_csv(output_csv_path)