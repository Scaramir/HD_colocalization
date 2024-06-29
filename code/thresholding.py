"""
This script is used to threshold images with different methods and save the thresholded images.
The thresholded images are used to create the masks for the segmentation and naively analyse the data.
This makes it easier to preprocess whole folders with the same technique instead of having to use ImageJ.
(c) 2023, Maximilian Otto, Berlin.
"""

# ----------------------------------------------------------------------------------------------- #
# Set the working directory, where all the data is stored:
#wd = "images/Cortical Organoids"
wd = "images/305_308_70qP_306_050_in_one_plot/images/raw_data"

# The threshold will be applied to the following folders/conditions:
#folders_list = ["Antimycin A", "EDHB", "hypoxy", "normal"]
folders_list = [""]

# Choose a threshold mode
#threshold_mode = "background_filtered_combo"
threshold_mode = "otsu_triangle_otsu_bg_gauss"
# Other options:
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
additional_background_substraction = True

# Want to apply a gaussian blur filter too?
# this affects the thresholding results and increases the overlap fluorecence signal
gauss_blur_filter = True

# NOTE: 
# This script used:
# Rolling ball method to substract the backhround noise
# Apply a gaussian blur filter to the image to increase the overlap of the signals (fluorescence) 
# Applied OTSU thresholding to the DAPI channel
# Applied triangle thresholding to CHCHD2, because it has a lot of low intensity pixels
# Applied OTSU thresholding to the TOM20 channel 
# Simiar method for NPCs and Cortical Organoids is used, excpet the cv2-thresh methods are different. Besides that, the images got treated the same way :) 
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

def substract_background(img, background_substraction, radius=50):
    # Apply a bacground substraction method to the image
    # Rolling Ball method from skimage.restoration
    if background_substraction:
        background = restoration.rolling_ball(img, radius=radius, num_threads=4)
        img = img - background
    return img

# Apply thresholding to every color channel of the image.
# input: "folder name" string
def thresholding(pic_folder_path, pic_sub_folder_name, mode = "low_intensities_filtered", gaussian_blur = True, additional_background_substraction = True):
    if not os.path.isdir(pic_folder_path + f"/../{pic_sub_folder_name}_thresholded_{mode}_{additional_background_substraction}"):
        os.makedirs(
            pic_folder_path + f"/../{pic_sub_folder_name}_thresholded_{mode}_{additional_background_substraction}")
    # We're gonna save the images here:
    os.chdir(pic_folder_path + f"/../{pic_sub_folder_name}_thresholded_{mode}_{additional_background_substraction}")

    if mode == "background_filtered_combo":
        additional_background_substraction = True

    for file in tqdm(glob.glob(pic_folder_path+"/*combined*"), desc=f"Applying {mode} thresholding"):
        thresholded_file_name = file.replace("combined", f"_{mode}_thresholded_{additional_background_substraction}")
        thresholded_file_name = os.path.basename(thresholded_file_name)
        if os.path.isfile(thresholded_file_name):
            continue

        img = read_image(file)

        # Split the image into its three channels
        ch1 = img[:, :, 0]
        ch1 = substract_background(ch1, additional_background_substraction)
        ch2 = img[:, :, 1]
        ch2 = substract_background(ch2, additional_background_substraction)
        ch3 = img[:, :, 2]
        ch3 = substract_background(ch3, additional_background_substraction)

        if gaussian_blur:
            # Apply a Gaussian blur filter to the image
            # sigma 0.5 leads to a kernal size of (3x3) = ((6*sigma+1) x (6*sigma+1)) 
            ch1 = cv2.GaussianBlur(ch1, (0, 0), 0.5)
            ch2 = cv2.GaussianBlur(ch2, (0, 0), 0.5)
            ch3 = cv2.GaussianBlur(ch3, (0, 0), 0.5)

        if mode == "triangle":
            # Apply triangle thresholding to every channel
            _, th1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            _, th2 = cv2.threshold(ch2, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            _, th3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)

        if mode == "adaptive":
            # Apply cv adaptive thresholding to every channel
            th1 = cv2.adaptiveThreshold(ch1, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 0)
            th2 = cv2.adaptiveThreshold(ch2, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 0)
            th3 = cv2.adaptiveThreshold(ch3, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 0)

        if mode == "otsu":
            # Apply Otsu's thresholding to every channel
            _, th1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, th2 = cv2.threshold(ch2, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, th3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)

        if mode == "otsu_on_dapi_only":
            # Apply Otsu's thresholding to only the DAPI channel
            _, th1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            th2 = ch2
            th3 = ch3

        if mode == "otsu_on_dapi_intensity_greater_7_on_rest":
            # Apply Otsu's thresholding to only the DAPI channel
            _, th1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            # Every value >1 remains the same, every value <=1 is set to 0
            th2 = ch2
            th3 = ch3
            th2[th2 < 8] = 0
            th3[th3 < 8] = 0 

        if mode == "triangle_on_dapi_intensity_greater_1_on_rest":
            # Apply Otsu's thresholding to only the DAPI channel
            _, th1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            # Every value >1 remains the same, every value <=1 is set to 0
            th2 = ch2
            th3 = ch3
            th2[th2 < 2] = 0
            th3[th3 < 2] = 0

        if mode == "super_low_intensities_5_filtered":
            th1 = ch1
            th2 = ch2
            th3 = ch3
            # Every value >5 remains the same, every value <=5 is set to 0
            th1[th1 < 6] = 0
            th2[th2 < 6] = 0
            th3[th3 < 6] = 0

        if mode == "low_intensities_filtered":
            th1 = ch1
            th2 = ch2
            th3 = ch3
            th1[th1 < 11] = 0
            th2[th2 < 11] = 0
            th3[th3 < 11] = 0

        if mode == "blue_otsu_red_triangle_green_5":
            _, th1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            th2 = ch2; th2[th2 < 5] = 0
            _, th3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)

        # For cortical organoids I used: 
        if mode == "background_filtered_combo":
            _, th1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, th2 = cv2.threshold(ch2, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            _, th3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)

        # For NPCs we can use the following:
        if mode == "otsu_triangle_otsu_bg_gauss":
            _, th1 = cv2.threshold(ch1, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)
            _, th2 = cv2.threshold(ch2, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_TRIANGLE)
            _, th3 = cv2.threshold(ch3, 0, 255, cv2.THRESH_TOZERO + cv2.THRESH_OTSU)


        # Merge the three channels into one image
        combined_img = cv2.merge((th1, th2, th3)) # type: ignore
        cv2.imwrite(os.getcwd()+"\\"+thresholded_file_name, combined_img)
    return

if __name__ == "__main__":
    for sub_folder_name in folders_list:
        pic_folder_path = os.path.join(wd, sub_folder_name)
        os.chdir(pic_folder_path)
        thresholding(pic_folder_path, sub_folder_name, mode = threshold_mode, gaussian_blur = gauss_blur_filter, additional_background_substraction = additional_background_substraction)
