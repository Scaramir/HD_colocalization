"""
This script is used to threshold images with different methods and save the thresholded images.
The thresholded images are used to create the masks for the segmentation and naively analyse the data.
This makes it easier to preprocess whole folders with the same technique instead of having to use ImageJ.
(c) 2024, Maximilian Otto, Berlin.
"""

# ----------------------------------------------------------------------------------------------- #
# Set the working directory, where all the data is stored:
#wd = "images/Cortical Organoids"
wd = "images/round2"

# The threshold will be applied to the following folders/conditions:
#folders_list = ["Antimycin A", "EDHB", "hypoxy", "normal"]
folders_list = ["CHCHD2-AAV", "DMSO", "GFP-AAV", "NZ", "UT"]
# folders_list = ["DMSO"]

ch_prefix = "c0" # prefix for all channels
ch1_suffix = "0" # Hoechst
ch2_suffix = "1" # EGFP
ch3_suffix = "2" # TOM20
ch4_suffix = "3" # CHCHD2

# Choose a threshold mode
threshold_mode = "otsu_triangle_otsu_triangle_gauss"
# Other options:
#  - "otsu_otsu_otsu_otsu_gauss"
#  - "super_low_intensities_5_filtered"
#  - "triangle_on_dapi_intensity_greater_1_on_rest"
#  - "otsu_on_dapi_intensity_greater_7_on_rest"
#  - "otsu_on_dapi_only",
#  - "otsu",
#  - "triangle",
#  - "low_intensities_filtered"
#  - "adaptive"
#  - "background_filtered_combo"

# Set an additional Background Substraction with Rolling ball method 
# for all methods that don't have it already
# set to True to activate, or False to disable
# Round2 images were too big to apply this method
additional_background_substraction = False

# Want to apply a gaussian blur filter too?
# this affects the thresholding results and increases the overlap fluorecence signal
gauss_blur_filter = True
# ----------------------------------------------------------------------------------------------- #

import os, glob
import cv2
from tqdm import tqdm
import skimage.restoration as restoration

pic_folder_path = os.path.join(wd, folders_list[0])
os.chdir(pic_folder_path)

# Read the `*.bmp file`
# input: "file name" string
def read_image(file):
    # read the image in while maintaining the original bit-depth ('-1')
    # NOTE: the image is read in BGR format when using OpenCV
    img = cv2.imread(file, -1)
    return img

## Read 4 corresponding greyscale images
def read_4_color_channels_from_rgb(file_name):
    base_channel = ch_prefix + ch1_suffix
    ch1 = cv2.imread(file_name, -1)[:,:,-1]
    ch2 = cv2.imread(file_name.replace(base_channel, ch_prefix + ch2_suffix), -1)[:,:,-1]
    ch3 = cv2.imread(file_name.replace(base_channel, ch_prefix + ch3_suffix), -1)[:,:,-1]
    ch4 = cv2.imread(file_name.replace(base_channel, ch_prefix + ch4_suffix), -1)[:,:,-1]
    return ch1, ch2, ch3, ch4


def substract_background(img, background_substraction, radius=100):
    # Apply a bacground substraction method to the image
    # Rolling Ball method from skimage.restoration
    if background_substraction:
        img -= restoration.rolling_ball(img, radius=radius, num_threads=16)
    return img

# Apply thresholding to every color channel of the image.
# input: "folder name" string
def thresholding(pic_folder_path, pic_sub_folder_name, mode = "low_intensities_filtered", gaussian_blur = True, additional_background_substraction = True):
    if not os.path.isdir(pic_folder_path + f"/../{pic_sub_folder_name}_thresholded_{mode}_{additional_background_substraction}"):
        os.makedirs(pic_folder_path + f"/../{pic_sub_folder_name}_thresholded_{mode}_{additional_background_substraction}")
    # We're gonna save the images here:
    os.chdir(pic_folder_path + f"/../{pic_sub_folder_name}_thresholded_{mode}_{additional_background_substraction}")

    if mode == "background_filtered_combo":
        additional_background_substraction = True

    for file in tqdm(glob.glob(pic_folder_path+"/*"+ch_prefix+ch1_suffix+"*"), desc=f"Applying {mode} thresholding"):
        thresholded_file_name = file.replace("combined", f"_{mode}_thresholded_{additional_background_substraction}")
        thresholded_file_name = os.path.basename(thresholded_file_name)
        if os.path.isfile(thresholded_file_name):
            continue

        ch1, ch2, ch3, ch4 = read_4_color_channels_from_rgb(file)

        if gaussian_blur:
            # Apply a Gaussian blur filter to the image
            # sigma 0.5 leads to a kernal size of (3x3) = ((6*sigma+1) x (6*sigma+1)) 
            ch1 = cv2.GaussianBlur(ch1, (0, 0), 0.5)
            ch2 = cv2.GaussianBlur(ch2, (0, 0), 0.5)
            ch3 = cv2.GaussianBlur(ch3, (0, 0), 0.5)
            ch4 = cv2.GaussianBlur(ch4, (0, 0), 0.5)

        ch1 = substract_background(ch1, additional_background_substraction)
        ch2 = substract_background(ch2, additional_background_substraction)
        ch3 = substract_background(ch3, additional_background_substraction)
        ch4 = substract_background(ch4, additional_background_substraction)


        if mode == "triangle":
            # Apply triangle thresholding to every channel
            _, ch1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            _, ch2 = cv2.threshold(ch2, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            _, ch3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            _, ch4 = cv2.threshold(ch4, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)

        if mode == "adaptive":
            # Apply cv adaptive thresholding to every channel
            ch1 = cv2.adaptiveThreshold(ch1, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 0)
            ch2 = cv2.adaptiveThreshold(ch2, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 0)
            ch3 = cv2.adaptiveThreshold(ch3, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 0)
            ch4 = cv2.adaptiveThreshold(ch4, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 0)

        if mode == "otsu":
            # Apply Otsu's thresholding to every channel
            _, ch1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, ch2 = cv2.threshold(ch2, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, ch3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, ch4 = cv2.threshold(ch4, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)

        if mode == "otsu_on_dapi_only":
            # Apply Otsu's thresholding to only the DAPI channel
            _, ch1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)

        if mode == "otsu_on_dapi_intensity_greater_7_on_rest":
            # Apply Otsu's thresholding to only the DAPI channel
            _, ch1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            # Every value >1 remains the same, every value <=1 is set to 0
            ch2[ch2 < 8] = 0
            ch3[ch3 < 8] = 0
            ch4[ch4 < 8] = 0

        if mode == "triangle_on_dapi_intensity_greater_1_on_rest":
            # Apply Otsu's thresholding to only the DAPI channel
            _, ch1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            # Every value >1 remains the same, every value <=1 is set to 0
            ch2[ch2 < 2] = 0
            ch3[ch3 < 2] = 0
            ch4[ch4 < 2] = 0

        if mode == "super_low_intensities_5_filtered":
            # Every value >5 remains the same, every value <=5 is set to 0
            ch1[ch1 < 6] = 0
            ch2[ch2 < 6] = 0
            ch3[ch3 < 6] = 0
            ch4[ch4 < 6] = 0

        if mode == "low_intensities_filtered":
            ch1[ch1 < 11] = 0
            ch2[ch2 < 11] = 0
            ch3[ch3 < 11] = 0
            ch4[ch4 < 11] = 0

        if mode == "blue_otsu_red_triangle_green_5":
            _, ch1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            ch2[ch2 < 5] = 0
            _, ch3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)

        # For cortical organoids I used: 
        if mode == "background_filtered_combo":
            _, ch1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, ch2 = cv2.threshold(ch2, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            _, ch3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)

        # For NPCs we can use the following:
        if mode == "otsu_triangle_otsu_triangle_gauss":
            _, ch1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, ch2 = cv2.threshold(ch2, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            _, ch3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, ch4 = cv2.threshold(ch4, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)

        if mode == "otsu_otsu_otsu_otsu_gauss":
            _, ch1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, ch2 = cv2.threshold(ch2, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, ch3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, ch4 = cv2.threshold(ch4, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)


        cv2.imwrite(os.getcwd()+"/"+thresholded_file_name, ch1)
        cv2.imwrite(os.getcwd()+"/"+thresholded_file_name.replace(ch_prefix+ch1_suffix, ch_prefix+ch2_suffix), ch2)
        cv2.imwrite(os.getcwd()+"/"+thresholded_file_name.replace(ch_prefix+ch1_suffix, ch_prefix+ch3_suffix), ch3)
        cv2.imwrite(os.getcwd()+"/"+thresholded_file_name.replace(ch_prefix+ch1_suffix, ch_prefix+ch4_suffix), ch4)
    return

if __name__ == "__main__":
    for sub_folder_name in folders_list:
        pic_folder_path = os.path.join(wd, sub_folder_name)
        os.chdir(pic_folder_path)
        thresholding(pic_folder_path, sub_folder_name, mode = threshold_mode, gaussian_blur = gauss_blur_filter, additional_background_substraction = additional_background_substraction)
