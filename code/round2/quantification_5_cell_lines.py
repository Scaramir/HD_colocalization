"""
The files "data_preparation.py" and "thresholding.py" need to be executed before this script!
This script will create a mask for the image, in which both markers (ch2 and ch3, i.e. CHCHD2 and TOM20) are present.
This will be used as the intersection mask for further analyzations.
The mean intensity per cell line and channel will be calculated, as well as the percentage of a marker's apperance
in the intersection mask, an approximated value for the intensities per cell (Sum(Intensities of CHCHD2-Signal) / area of DAPI).
All those values will be plotted and saved as a `.csv file`.

Change your file path to <where all your image folders to analyze are located>.
The folder name with the images in it should include <"_thresholded_" + threshold_mode> by now.
Example path, where the programm expects some files: 
<"S:/mdc_work/mdc_huntington/images/treated/hypoxy_thresholded_super_low_intensities_filtered">
Select a previously applied thresholding method (threshold_type).
Select if the previously applied gaussian filter was used or not (gaussian_filter).
These declarations are necessary for the script to find the correct files.
Select, if you want to save the colocalization-masks as `.bmp files` or not.

Notice that i will only work and generate plots, if you adjsuted the parts noted with `TODO`.

In case some images are doubled, they can be previously filtered out by searching for "t0" or "Hoechst":
✗ cd Antimycin\ A_thresholded_super_low_intensities_filtered
✗ rm *t0*
✗ rm *Hoechst*
This deletes all files, that contain "t0" or "Hoechst" in their name (case sensitive).

(c) 2023, Maximilian Otto, Berlin.
"""
# ----------------------------------------------------------------------------------------------- #
# TODO: Change settings:

# Path of the folder containing all thresholded folders
#wd = "S:/mdc_work/mdc_huntington/images/NPCs new/"
#wd = "S:/mdc_work/mdc_huntington/images/Cortical Organoids/"
wd = "S:/mdc_work/mdc_huntington/images"

# channel names in the file names to load the correct images
ch_prefix = "c0" # prefix for all channels
ch1_suffix = "0" # Hoechst
ch2_suffix = "1" # EGFP
ch3_suffix = "2" # TOM20
ch4_suffix = "3" # CHCHD2


# Set the normal/control condition folder name so you can compare multiple conditions
# Set to "" if you just have one folder. This folder may contain multiple cell lines.
#pic_condition_folder_path = "raw_data"
#pic_condition_folder_path = "combined"
pic_condition_folder_path = "UT"


# The quantification will be applied to the following list of folders/conditions:
treatment_list = ["round2"]

#within a treatment, we have the follwoing cell lines in separate folders
cell_line_list = ["CHCHD2-AAV", "DMSO", "GFP-AAV", "NZ", "UT"]

# Select the previously executed thrsholding mode, on which the quantification will be performed
threshold_mode = "otsu_otsu_otsu_otsu_gauss_False"

# Set to True or False, wheter you applied a gaussian filter or not
gauss_blur_filter = True   

# Want the area of CHCHD2 and TOM20 (colocalization) saved as an image? 
save_mask_as_bmp = False    
# ----------------------------------------------------------------------------------------------- #

import pandas as pd
import glob
import os
import glob
import cv2
import seaborn as sns
import matplotlib.pyplot as plt
from itertools import combinations
import gc
from tqdm import tqdm
# Easy to use, but deprecated in favor of statannotations package: 
from statannot import add_stat_annotation 

pic_folder_path = os.path.join(wd, pic_condition_folder_path)
pic_folder_path = wd
os.chdir(pic_folder_path)

# Read the *.bmp file
# NOTE: opencv reads the image in BGR format
# input: "file name" string
def read_bmp(file):
    img = cv2.imread(file, -1)
    return img

def read_4_color_channels_from_greyscale(file_name):
    base_channel = ch_prefix + ch1_suffix
    ch1 = cv2.imread(file_name, -1)
    ch2 = cv2.imread(file_name.replace(base_channel, ch_prefix + ch2_suffix), -1)
    ch3 = cv2.imread(file_name.replace(base_channel, ch_prefix + ch3_suffix), -1)
    ch4 = cv2.imread(file_name.replace(base_channel, ch_prefix + ch4_suffix), -1)
    return ch1, ch2, ch3, ch4

def create_mask(ch2, ch3, file, save_mask = False):
    # Split the image into its three channels
    # ch1, ch2, ch3 = cv2.split(img)
    # Create a mask, containing the pixels that are not black in the two desired channels
    #  - We do not care about the ch1/blue channel (it contains the DAPI/Hoechst intensities)
    #  - Keep all the pixels, where both channels are not zero
    #  - This will give us the spots where both markers are present, i.e. the colocalization mask
    mask_chchd2_and_tom20 = cv2.bitwise_and(ch2, ch3)

    # Save the mask as a `.bmp file`
    # TODO: change
    if save_mask & (not os.path.isfile(file.replace("thresholded", "mask"))):
        cv2.imwrite(os.path.basename(file.replace("thresholded", "mask")), mask_chchd2_and_tom20)

    # Transform mask_chchd2_and_tom20_df to a binary mask
    mask_chchd2_and_tom20 = mask_chchd2_and_tom20 > 0
    return mask_chchd2_and_tom20


def calculate_mean_intensity_of_2_markers(pic_folder_path, treatment_var="normal", threshold_mode="triangle_on_dapi_intensity_greater_1_on_rest", gaussian_filter=False, save_mask=False):
    # Lists, in which all values of interest will be stored:
    file_names = []

    ch1_counts_total = []
    ch2_counts_total = []
    ch3_counts_total = []
    ch4_counts_total = []
    ch2_counts_total_normalized = []
    ch3_counts_total_normalized = []
    ch4_counts_total_normalized = []

    mean_intensities_ch1 = []
    mean_intensities_ch2 = []
    mean_intensities_ch3 = []
    mean_intensities_ch4 = []

    mean_intensities_ch2_at_dapi = []
    mean_intensities_ch2_in_mask = []
    mean_intensities_ch3_in_mask = []
    mean_intensities_ch4_in_mask = []

    percentages_ch1_in_chchd2 = []
    percentages_ch2_in_dapi = []
    percentages_ch2_in_chchd2_and_tom20 = []
    percentages_ch3_in_chchd2_and_tom20 = []

    amounts_per_cell_approximation_ch2_in_mask = []
    amounts_per_mito_approximation_ch2_in_mask = []
    intensities_per_cell_approximation_ch2_in_mask = []
    intensities_per_mito_approximation_ch2_in_mask = []

    gaussian_filters = []
    threshold_types = []

    # change the working directory to the folder, where the thresholded images are stored:

    for cell_line_folder in cell_line_list:
        os.chdir(pic_folder_path + "/" + cell_line_folder + "_thresholded_" + threshold_mode)
        cell_line_folder_path = os.path.join(pic_folder_path, cell_line_folder)
        for file in tqdm(glob.glob(cell_line_folder_path + "_thresholded_" + threshold_mode + "/*" + ch_prefix + ch1_suffix + "*.tiff"), desc="Counting pixels for " + cell_line_folder):
            # img = read_bmp(file)

            ch1, ch2, ch3, ch4 = read_4_color_channels_from_greyscale(file)

            # NOTE: swap ch2 and ch4 , because original ch2 is EGFP and ch4 is CHCHD2 in this case. 
            # so let's swap and just add egfp as ch4 to the analysis 
            ch2, ch4 = ch4, ch2

            # Split the image into its three channels and create the colocalization mask:
            mask_chchd2_and_tom20_bin = create_mask(ch2, ch3, file, save_mask)
            # Create a mask, where Dapi and CHCHD2 are colocalized
            dapi_chchd2_mask = cv2.bitwise_and(ch1, ch2)
            dapi_chchd2_mask = dapi_chchd2_mask > 0

            # How many pixles of a color channel have intensity > 0?
            # NOTE: This required the image to be thresholded and checked before
            ch1_count_total = ch1[ch1 > 0].size 
            ch2_count_total = ch2[ch2 > 0].size
            ch3_count_total = ch3[ch3 > 0].size
            ch4_count_total = ch4[ch4 > 0].size

            # Normalize the amounts of each marker by the total amount of DAPI-pixels
            # aka normalizing by nuclei area
            ch2_count_total_normalized = ch2_count_total / ch1_count_total
            ch3_count_total_normalized = ch3_count_total / ch1_count_total
            ch4_count_total_normalized = ch4_count_total / ch1_count_total

            # Get mean intensities of each channel
            ch1_mean_greater_than_zero = ch1[ch1 > 0].mean()
            ch2_mean_greater_than_zero = ch2[ch2 > 0].mean()
            ch3_mean_greater_than_zero = ch3[ch3 > 0].mean()
            ch4_mean_greater_than_zero = ch4[ch4 > 0].mean()

            # Get amount of all values > 0 that are colocalized
            ch2_count_in_mask = ch2[mask_chchd2_and_tom20_bin].size
            ch3_count_in_mask = ch3[mask_chchd2_and_tom20_bin].size
            ch1_count_at_chchd2 = ch1[dapi_chchd2_mask].size # same would be: ch1[(ch2 > 0) & (ch1 > 0)].size                                          
            ch2_count_at_dapi = ch2[dapi_chchd2_mask].size

            # Calculate the percentage of ch1, ch2, and ch3 that are in chchd2_and_tom20
            percentage_of_ch1_in_chchd2 = ch1_count_at_chchd2 / ch1_count_total * 100
            percentage_of_ch2_in_dapi = ch2_count_at_dapi / ch2_count_total * 100
            percentage_of_ch2_in_chchd2_and_tom20 = ch2_count_in_mask / ch2_count_total * 100
            percentage_of_ch3_in_chchd2_and_tom20 = ch3_count_in_mask / ch3_count_total * 100

            # Mean-intensity of the pixel values of a channel, that are not black and lay within in the mask
            ch1_crossover_mean = ch1[mask_chchd2_and_tom20_bin & (ch1 > 0)].mean()
            ch2_at_dapi_mean = ch2[dapi_chchd2_mask].mean()
            ch2_crossover_mean = ch2[mask_chchd2_and_tom20_bin].mean()
            ch3_crossover_mean = ch3[mask_chchd2_and_tom20_bin].mean()

            # Per cell and per mitochondria approximation (ch3 should be TOM20)
            # Area-wise approximation:
            amount_per_cell_approximation_ch2_in_mask = ch2_count_in_mask / ch1_count_total
            amount_per_mito_approximation_ch2_in_mask = ch2_count_in_mask / ch3_count_total
            # Total intensity divided by cell-area approximation:
            intensity_per_cell_approximation_ch2_in_mask = ch2[mask_chchd2_and_tom20_bin].sum() / ch1_count_total
            intensity_per_mito_approximation_ch2_in_mask = intensity_per_cell_approximation_ch2_in_mask * ch1_count_total / ch3_count_total

            # Append the values to the lists:
            file_names.append(os.path.basename(file))

            ch1_counts_total.append(ch1_count_total)
            ch2_counts_total.append(ch2_count_total)
            ch3_counts_total.append(ch3_count_total) 
            ch4_counts_total.append(ch4_count_total)
            ch2_counts_total_normalized.append(ch2_count_total_normalized)
            ch3_counts_total_normalized.append(ch3_count_total_normalized)
            ch4_counts_total_normalized.append(ch4_count_total_normalized)

            mean_intensities_ch1.append(ch1_mean_greater_than_zero)
            mean_intensities_ch2.append(ch2_mean_greater_than_zero)
            mean_intensities_ch3.append(ch3_mean_greater_than_zero)
            mean_intensities_ch4.append(ch4_mean_greater_than_zero)
            mean_intensities_ch2_at_dapi.append(ch1_crossover_mean)
            mean_intensities_ch2_in_mask.append(ch2_crossover_mean)
            mean_intensities_ch3_in_mask.append(ch3_crossover_mean)
            percentages_ch1_in_chchd2.append(percentage_of_ch1_in_chchd2)
            percentages_ch2_in_dapi.append(percentage_of_ch2_in_dapi)
            percentages_ch2_in_chchd2_and_tom20.append(percentage_of_ch2_in_chchd2_and_tom20)
            percentages_ch3_in_chchd2_and_tom20.append(percentage_of_ch3_in_chchd2_and_tom20)
            amounts_per_cell_approximation_ch2_in_mask.append(amount_per_cell_approximation_ch2_in_mask)
            amounts_per_mito_approximation_ch2_in_mask.append(amount_per_mito_approximation_ch2_in_mask)
            intensities_per_cell_approximation_ch2_in_mask.append(intensity_per_cell_approximation_ch2_in_mask)
            intensities_per_mito_approximation_ch2_in_mask.append(intensity_per_mito_approximation_ch2_in_mask)
            gaussian_filters.append(gaussian_filter)
            threshold_types.append(threshold_mode)

    # Create a dataframe with all obtained values to save it as a `csv file` and plot it with seaborn:
    quantification_df = pd.DataFrame({
                        "File name": file_names,
                        # raw amounts:
                        "DAPI amount": ch1_counts_total,
                        "CHCHD2 amount": ch2_counts_total,
                        "TOM-20 amount": ch3_counts_total,
                        "EGFP amount": ch4_counts_total,
                        # amounts normalized by DAPI amount per image:
                        "CHCHD2 amount normalized by DAPI": ch2_counts_total_normalized,
                        "TOM-20 amount normalized by DAPI": ch3_counts_total_normalized,
                        "EGFP amount normalized by DAPI": ch4_counts_total_normalized,
                        # mean intensities of channels:
                        "DAPI intensity (mean)": mean_intensities_ch1,
                        "CHCHD2 intensity (mean)": mean_intensities_ch2,
                        "TOM-20 intensity (mean)": mean_intensities_ch3,
                        "EGFP intensity (mean)": mean_intensities_ch4,
                        "CHCHD2 mean intensity (colocalized with DAPI)": mean_intensities_ch2_at_dapi,
                        "CHCHD2 mean intensity (colocalized with TOM-20)": mean_intensities_ch2_in_mask,
                        "TOM-20 mean intensity (colocalized with CHCHD2)": mean_intensities_ch3_in_mask,
                        # Colocalization percentages:
                        "DAPI colocalized with CHCHD2 (Coverage in %)": percentages_ch1_in_chchd2,
                        "CHCHD2 colocalized with DAPI (Coverage in %)": percentages_ch2_in_dapi,
                        "CHCHD2 colocalized with TOM-20 (Coverage in %)": percentages_ch2_in_chchd2_and_tom20,
                        "TOM-20 colocalized with CHCHD2 (Coverage in %)": percentages_ch3_in_chchd2_and_tom20,
                        # amounts normalized by mito amount per cell, that are colocalized with TOM-20:
                        "CHCHD2 amount per cell (colocalized with TOM-20)": amounts_per_cell_approximation_ch2_in_mask,
                        "CHCHD2 amount per mito (colocalized with TOM-20)": amounts_per_mito_approximation_ch2_in_mask,
                        "CHCHD2 intensity per cell (colocalized with TOM-20)": intensities_per_cell_approximation_ch2_in_mask,
                        "CHCHD2 intensity per mito (colocalized with TOM-20)": intensities_per_mito_approximation_ch2_in_mask,
                        # Additional information:
                        "Gaussian filter": gaussian_filters,
                        "Threshold type": threshold_types,
                        "Condition": treatment_var
                        })

    # Additional information: 
    # Get the cell line from the file name
    # TODO FIXME NOTE:
    # change this for the different file name structures to use this script with different data sets
    # quantification_df["Cell line"] = quantification_df["File name"].str.split("_", expand=True)[2] #organoids or NPCs new
    quantification_df["Cell line"] = quantification_df["File name"].str.split("_", expand=True)[0]

    # Save the dataframe to a csv file
    quantification_df.to_csv(pic_folder_path + "/quantification.csv", index=False)
    return quantification_df

# Run the quantification function
#quantification_df = calculate_mean_intensity_of_2_markers(pic_folder_path, treatment_var="normal", gaussian_filter=gauss_blur_filter, threshold_mode=threshold_mode, save_mask=save_mask_as_bmp)


# Sort dataframe by cell line
def sort_df_by_cell_line(quantification_df):
    return quantification_df.sort_values(by=["cell_line"], inplace=True)
#quantification_df_sorted = sort_df_by_cell_line(quantification_df)

# Plot the boxplots of the quantification dataframe with seaborn and save them as `.png files`
def box_plt_by_cell_line(quantification_df, value_to_plot, pic_folder_path, condition, threshold_mode, show="True"):
    plt.clf()
    sns.set(style="whitegrid")
    sns.set_context("talk")

    sns.catplot(x="Cell line",
                y=value_to_plot,
                kind="box",
                legend=False,
                height=7,
                aspect=0.8,
                data=quantification_df,
                fliersize=0)

    ax = sns.stripplot(x="Cell line",
                        y=value_to_plot,
                        data=quantification_df,
                        jitter=True,
                        dodge=True,
                        marker='o',
                        alpha=0.5,
                        linewidth=0.5)

    # TODO: Change the names of the cell lines to the correct ones
    all_box_pairs = list(combinations(treatment_list, 2))
    # TODO: adjust the statistical test to the correct one. 
    #       Mann-Whitney is used when the data is not normally distributed
    #       t-welch-test is used when the data is normally distributed and the variances are not equal
    #       t-test is used when the data is normally distributed and the variances are equal
    # add_stat_annotation(ax, data=quantification_df, x="Cell line", y=value_to_plot,
    #                     box_pairs=all_box_pairs,
    #                     test="Mann-Whitney", comparisons_correction="bonferroni", text_format="star", loc="outside", verbose=2)

    plt.savefig(pic_folder_path + "/mannwhitneyplot_" + value_to_plot + "_" + condition + ".png", bbox_inches='tight')
    if show:
        plt.show()
    return

# Run the calculation for every treatment of the list of treatments and append the results to the dataframe
# Create plots for each treatment within its seperated folder
def quantification(treatment_list, threshold_mode="triangle_on_dapi_intensity_greater_1_on_rest", gaussian_filter=False, save_mask=False, pic_folder_path=pic_folder_path):
    # Loop through the treatments to quantify each treatment seperately
    complete_df = pd.DataFrame()
    for treatment in treatment_list:
        # Get the path of the folder containing the images
        pic_sub_folder_path = treatment
        pic_folder_path = os.path.join(wd, pic_sub_folder_path)
        os.chdir(pic_folder_path)
        print(f"Calculating condition \"" + treatment + "\"")

        current_quant_df = calculate_mean_intensity_of_2_markers(pic_folder_path, treatment_var=treatment, gaussian_filter=gaussian_filter, threshold_mode=threshold_mode, save_mask=save_mask)
        # add quant data to the complete dataframe
        complete_df = pd.concat([complete_df, current_quant_df], ignore_index=True)

        for column in complete_df.select_dtypes(include=[float, int]):
            box_plt_by_cell_line(current_quant_df, column, pic_folder_path, treatment, threshold_mode, show="False")

        print("########################################################################\n\n\n")
    return complete_df

# Run the quantification function
if __name__ == "__main__":
    complete_df = quantification(treatment_list, threshold_mode, gaussian_filter=gauss_blur_filter, save_mask=save_mask_as_bmp)
