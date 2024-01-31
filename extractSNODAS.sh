#!/bin/bash
# Dane Liljestrand
# 2023-01-30
# Convert NOHRSC SNODAS .tar files to daily .tif files of either SWE or Snow Depth. 

year=2022

# "01_Jan" "02_Feb" "03_Mar" "04_Apr" "05_May" "06_Jun" "07_Jul" "08_Aug" "09_Sep" "10_Oct" "11_Nov" "12_Dec"

for month in "01_Jan" "02_Feb" "03_Mar"; do
    #extract
    DIR="data/$year/$month"
    mkdir -p data/$year/$month/extracted
    oDIR="data/$year/$month/extracted"
    for filename in "$DIR"/*.tar; do
    #for filename in ~/$year/$month/*; do
        tar -xvf $filename -C "$oDIR" --wildcards --no-anchored '*1034*' '*1036*'
    done

    # #unzip
    DIR="data/$year/$month/extracted"
    for filename in "$DIR"/*.gz; do
    #for filename in ~/$year/$month/*; do
        gunzip -vf $filename *1034* *1036*
    done

#     #rename
#     for filename in "$DIR"/; do
#         rename .dat .bil "$DIR"/*.dat
#     done
    
    #rename with mv if linux does not have rename command
    for file in "$DIR"/*.dat; do
    if [ -f "$file" ]; then
        new_file="${file%.dat}.bil"
        mv "$file" "$new_file"
    fi
    done


    #create Header file
    DIR="data/$year/$month/extracted"
    # Loop through all .bil files in the directory
    for bil_file in "$DIR"/*.bil; do
        # Extract file information
        filename="${bil_file%.*}"
        day_type=$(echo "$filename" | cut -d'_' -f1)

        # Create header file name
        hdr_file="${filename}.hdr"

        header_content="nrows 3351\nncols 6935\nnbands 1\nnbits 16\nbyteorder M\nlayout bil\nskipbytes 0\nulxmap -124.729583333332\nulymap 52.8704166666656\nxdim 0.008333333333333\nydim 0.008333333333333\npixeltype SIGNEDINT\nnodata -9999"

        # Write header content to the header file
        echo -e "$header_content" > "$hdr_file"

        echo "Header file '$hdr_file' created for '$bil_file'"
    done


    #create projection file
    DIR="data/$year/$month/extracted"
    # Loop through all .bil files in the directory
    for bil_file in "$DIR"/*.bil; do
        # Extract file information
        filename="${bil_file%.*}"
        day_type=$(echo "$filename" | cut -d'_' -f1)

        # Create header file name
        prj_file="${filename}.prj"


        proj_content="GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563
    ]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.017453292519943295]]"

        # Write proj content to the proj file
        echo -e "$proj_content" > "$prj_file"

        echo "Projection file '$prj_file' created for '$bil_file'"
    done


    #### Convert to Tiffs
    DIR="data/$year/$month/extracted"
    # Specify the output folder
    output_folder="tiffs"

    # Create the output folder if it doesn't exist
    mkdir -p "data/$year/$month/extracted/$output_folder"

    # Loop through the specified number of files
    for bil_file in "$DIR"/*.bil; do
        # Input file name
        input_file="$bil_file"

        # Check if the input file contains "1034" - SWE data, "1036" for snow depth
        if [[ $input_file == *"1034"* ]]; then
            # Extract datestamp from the input filename
            datestamp=$(echo "$input_file" | grep -oP '\d{8}')

            # Output file name with full path
            output_file="data/$year/$month/extracted/$output_folder/us_swe_${datestamp}_${i}.tif"

            # Run gdal_translate command
            gdal_translate -of GTiff -ot Int16 -a_nodata -9999 -co "TFW=YES" -co "COMPRESS=LZW" -stats "$input_file" "$output_file"

            echo "Conversion completed for $input_file. Output: $output_file"
        else
            echo "Skipping $input_file as it does not contain '1034'."
        fi
    done


    ### remove tar files
    DIR="data/$year/$month"
    for tar_file in "$DIR"/*.tar; do
        rm "$tar_file"
    done
done