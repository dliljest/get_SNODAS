# get_SNODAS
Bash scripts for downloading and converting SNODAS data from NSIDC (https://nsidc.org/data/g02158/versions/1).

These scripts download dialy binary NOHRSC SNODAS .tar files from https://noaadata.apps.nsidc.org/.

**getSNODAS.sh** retrieves daily files for user selected time period and saves them to a new directory in the cwd. 

**extractSNODAS.sh** converts .tar files to .tif files for processing and removes the large .tar files. 
