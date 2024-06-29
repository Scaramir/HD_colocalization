# Quantification & Colocalization

This repository contains the files used to quantify and analyze the colocalization of three different fluorescent markers per image of a cell culture. This works with whole folder structure, where each folder within a working directory contains the images of one cell line or treatment condition. If there is just one folder, the analysis is done for all images in this folder and compares the cell lines or treatment in regards to their file names. Some modifications need to be done to the scripts to make them work for different data sets.  
The different cell lines or treatment conditions can be compared to check for significant differences in the amount of signal of the markers or the colocalization of the markers.   
The original images were greyscale images and should contain following markers:
 - DAPI (blue)
 - CHCHD2 (green)
 - TOMM20 (red) 

The following scripts can be run in a juypyter notebook or as a normal python3 scripts:
 - `data_preparation.py`: contains the functions used to prepare the data for the analysis, i.e. to read the images in `tiff-format`, check the file format, and to merge the greyscale images of each marker into a single RGB8 image and save them in `bmp-format`.
 - `thresholding.py`: contains the functions used to threshold the images. Different methdos are available, from hardcoded thresholds to combinations of Otsu's method and Triangle Thresholding. A Rolling Ball Background Subtraction and Gaussian Blur are applied to the images before thresholding, if desired. This is used to remove the background and to smooth the images before analyzing them. It does not require ImageJ.
 - `quantification_5_cell_lines.py`: Obtain a bunch of values about the markers in the images. The values are saved in a `csv-file`. This is for five specific cell lines and produces the corresponding box and scatter plots to compare them. The pairwise differences of the classes (cell lines) get compared with the Mann-Whitney-U-Test due to no validation of a normal distribution. The significance levels are shown in the resulting plots. The results (`quantification_results.csv`) contain the
   - colocalizations of the markers for every marker for each image
   - the amount of pixels (or area) of the markers
   - the mean intensity of each marker (also colocalized)
   - the relative amount of signal of each marker in regards to the area of DAPI. This normalizes the signal of the markers in regards to the size and amount of the nuclei in each image.

# Round 2
`code/round2/` was for analyzing the colocalization of only GFP-positive cells. Therefore, the scripts changed a bit and included an additional marker, pre-processing steps and masks.   
The pipeline consists of the following steps:  
thresholding -> QuPath annotations -> export annotations -> convert lables to masks -> quantification

## Thresholding images:

It can be assumed that imaged were taken with the same settings, therefore, the same thresholding technique was used for all images of the same type.
Images containing the following substrings in their name were assumed to contain the following staining and were thresholded accordingly:

  -  "c00" -> DAPI staining -> Otsu thresholding,
  -  "c01" -> EGFP staining -> Triangle thresholding,
  -  "c02" -> TOM20 staining -> Otsu thresholding,
  -  "c03" -> CHCHD2 staining -> Triangle thresholding,

All images got a gaussian blur with sigma=0.5 applied, resulting in a three pixel blurring radius, to smoothen the images before thresholding.

## Background noise subtraction:

Each image got processed individually. The resolution of the images remained unchanged. Due to the image size and quality of thresholding results, the background noise subtraction of the previous analysis (organoids and NPC cell lines) was not performed.

## Extracting GFP positive cells:

To be sure that the effect of the AAV transduction is analyzed correctly, only cells with stronger GFP signal than the background fluorescence were considered. 
The thresholded images were loaded into *QuPath* and the cells with a stronger marker were **manually annotated**. 
The annotations were exported as JSON files before being converted to TIFF masks. The masks were used during quantification to only analyze the respective areas instead the whole image.

## Quantification:

The images were quantified as previously. For mean intensity, the amount of signal (pixels with brightness > 0) was observed. For the area, the amount of signal was observed.

## Significance testing:  
For this comparison, due to very low sample sizes with unequal variances, a **Welch's t-test** was used to compare the means of the two groups to test whether they differ. 
This is known to be a more conservative method when the sample sizes are small, but the type-I error rate is controlled around the nominal level using this test.