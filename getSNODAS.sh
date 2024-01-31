#!/bin/bash
# Dane Liljestrand
# 2024-01-30
# Retrieves NOHRSC SNODAS data from National Snow and Ice Data Center (NSDIC) through NOAA server. 

mkdir -p data

year=2022

mkdir -p data/$year

cd data/$year


# "01_Jan" "02_Feb" "03_Mar" "04_Apr" "05_May" "06_Jun" "07_Jul" "08_Aug" "09_Sep" "10_Oct" "11_Nov" "12_Dec"

for months in "01_Jan" "02_Feb" "03_Mar"
	do
		mkdir -p $months
		cd $months
		wget -r -nd --no-check-certificate --reject "index.html*" -np -e robots=off https://noaadata.apps.nsidc.org/NOAA/G02158/masked/$year/$months/
		cd ..
	done
