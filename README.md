# Quantification & Colocalization

This repository contains the files used to quantify and analyze the colocalizaiton of three different fluorescent markers per image.  
The markers are:
 - DAPI (blue)
 - CHCHD2 (green)
 - TOMM20 (red) 

The following scripts work on whole folders can be run in a juypyter notebook or as a normal python3 script:
 - `data_preparation.py`: contains the functions used to prepare the data for the analysis, i.e. to read the images in `tiff-format`, check the file format and to merge the greyscale images of each marker into a single RGB8 image and save them in `bmp-format`.
 - `thresholding.py`: contains the functions used to threshold the images. Different methdos are available, from hardcoded thresholds to combinations of Otsu's method and Triangle Thresholding. A Rolling Ball Background Subtraction and Gaussian Blur are applied to the images before thresholding, if desired. This is used to remove the background and to smooth the images before analyzing them. It does not require ImageJ.
 - `quantification_5_cell_lines.py`: Obtain a bunch of values about the markers in the images. The values are saved in a `csv-file`. This is for five specific cell lines and produces the corresponding box and scatter plots to compare them. The pairwise differences of the classes (cell lines) get compared with the Mann-Whitney-U-Test due to no validation of a normal distribution. The significance levels are shown in the resulting plots. The results (`quantification_results.csv`) contain the
   - colocalizations of the markers for every marker for each image
   - the amount of pixels (or area) of the markers
   - the mean intensity of each marker (also colocalized)
   - the relative amount of signal of each marker in regards to the area of DAPI. This normalizes the signal of the markers in regards to the size and amount of the nuclei in each image.

The data is available upon request.  
Also, i will further update this repository with more detailed information about the scripts and the analysis.  
