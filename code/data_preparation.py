"""
-> Because all images were available in 8bit format (which got checked with this script too), 
    the script combines them to RGB8 images. 
(c) 2023, Maximilian Otto, Berlin.
"""

# ----------------------------------------------------------------------------------------------- #
# Global parameters:
# Set the working directory, where all the data is stored:
wd = "S:/images/305_308_70qP"

# The pre-processing will be applied to the following folders/conditions:
folders_list = ["raw_data"]

# Merge three fluorescent channels of the same image into one image.
# Channel name prefix:
#  Example: "c01" + "c02" + "c03" -> "combined"
#  -> ch_prefix = "c0"
ch_prefix = "c0"

# Channel name suffices:
ch_1_suf = "0"
ch_2_suf = "1"
ch_3_suf = "2"

# File format:
input_file_format = ".tiff"

# Combine the images into one RGB-image?
merge_to_rgb: bool = True
output_file_format: str = ".bmp"

# Min. bit-depth we want to check for:
# Has the microscope used a >=12bit-color camera and an according sensitivity? 
# If so, at least some pixels of the images should contain intensities with a higher value than the required min_bit_depth of 8bit.
# Otherwise the images were probably saved as 8bit images. 
# For 16, 24 and 32 bit images, the min_bit_depth should be 12, 16 and 24 respectively.  
min_bit_depth = 8
# ----------------------------------------------------------------------------------------------- #

import exifread
import glob, os
import cv2
from tqdm import tqdm

# Input: amount of bits, e.g. the amount of bits used to store a greyscale image.       
# Return: Max. value of a certain amount of bits. 
# Note: used to get the max. value of a certain "bit-depth"of an image.
def max_bits(min_bit_depth):
    return (1 << min_bit_depth) - 1

# Imaging data in 24bit-tif should have one pixel value higher than 16bit-color values. 
# input: current file name string, max. value of the min. bit-depth (e.g. 255 for 8bit)
# return: Boolean
def is_it_really_16_bit(file, max_value_of_min_bit_depth):
    pic_brighter_than_min_bit_depth = False
    f = open(file, 'rb')
    tags = exifread.process_file(f) #type: ignore
    # Check max. brightness of the image (Larger than max(8bit)):
    if "Image SMaxSampleValue" in tags and str(tags["Image SMaxSampleValue"].values) > max_value_of_min_bit_depth:
        pic_brighter_than_min_bit_depth = True
    return pic_brighter_than_min_bit_depth

# Check each image of a folder for its brightness. Print out the number of images that are darker than 12bit.
def check_bit_depth(pic_folder_path):
    pics_brighter_than_16_bit = 0
    pics_total = 0
    pics_too_dark = []
    max_value_of_min_bit_depth = max_bits(min_bit_depth)
    os.chdir(pic_folder_path)
    print("Searching for pictures with a brightness indicating that they are truly 16 bits and not too dark:")
    print(os.getcwd())
    for file in tqdm(glob.glob("*"+input_file_format), desc = "Checking for bit depth (higher than 8 bit)"):
        pics_total += 1
        if is_it_really_16_bit(file, max_value_of_min_bit_depth) == True:
            pics_brighter_than_16_bit += 1
        else: 
            pics_too_dark.append(os.path.basename(file))
    print("{0} {1} {2} {3}".format(pics_brighter_than_16_bit, "of", pics_total, "are definitely saved with a higher bit depth than 8 bit."))
    if len(pics_too_dark) > 0:
        print("The following files are too dark or they could have been saved in another data format:")
        if len(pics_too_dark) == len([name for name in os.listdir() if os.path.isfile(name)]):
            print("All images are too dark")
        else: 
            for pic in pics_too_dark:
                print(pic)
    return pics_brighter_than_16_bit
# test the first folder. The others are ususally stored in the same format.
#check_bit_depth(pic_folder_path)                


# Merge the three channels of the same image into one image.
# input: "picture folder path" string
def image_merger_to_rgb(pic_folder_path): 
    pics_total = 0
    base_channel = ch_prefix + ch_1_suf
    for file in tqdm(glob.glob(pic_folder_path+"/*"+base_channel+"*"+input_file_format), desc = "Merging three channels into one rgb8 file"):
        if os.path.isfile(file.replace(base_channel, "combined")):
            continue
        ch1 = cv2.imread(file, -1)
        ch2 = cv2.imread(file.replace(base_channel, ch_prefix + ch_2_suf), -1)
        ch3 = cv2.imread(file.replace(base_channel, ch_prefix + ch_3_suf), -1)

        # Combine the channels into one image
        combined_img = cv2.merge((ch1[:,:,0], ch2[:,:,1], ch3[:,:,2]))
        file_replaced = file.replace(base_channel, "combined_")
        cv2.imwrite(file_replaced.replace(input_file_format, output_file_format), combined_img)
        pics_total += 1
    print("Created {0} rgb-images".format(pics_total), end = "\r")


if __name__ == "__main__":
    for sub_folder in folders_list:
        pic_folder_path = os.path.join(wd, sub_folder)
        os.chdir(pic_folder_path)
        check_bit_depth(pic_folder_path)
        if merge_to_rgb:
            image_merger_to_rgb(pic_folder_path)
