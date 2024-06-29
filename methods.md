# Quantification & Colocalization

## Methods
The following contains a description of the methods used in the scripts written in \texttt{Python 3.8.15} to obtain a quantification for the three-channel colocalization analysis. 

### Preprocessing
In short, the script (`data_preparation.py`) combines the individual grey-scale images of all three different markers into one image and stored as a bitmap, where TOM20 is stored in the red colour channel, hence CHCHD2 is green and DAPI blue.  
Further preprocessing (`thresholding.py`) of the images includes background noise subtraction and thresholding. For this, the rolling ball algorithm implementation of Scikit-image (\cite{van2014scikit}) with a radius of 50 pixels was used.  
Afterwards, Gaussian blur and thresholding was applied to each image individually using the \texttt{OpenCV} library (\cite{opencv}). For blurring, the kernal size was chosen to be $(3,3)$. This adds minimal blur to the image, so two directly adjacent fluorescent signals can overlap and be considered as colocalized.  
For thresholding, Otsu's method was used on the respective colour channels of DAPI and TOM20, while the channel containing CHCHD2 information was thresholded using the triangle method if set as a parameter in the script (\cite{opencv}). All values below the threshold were set to zero, while all other values remained unchanged.

### Quantification
The script then created binary masks of colocalized markers, i.e. taking all pixels of two different colour channels into account that are detected in the same position. 
The masks are then used to calculate the amount of colocalized pixels above the threshold for each marker, thus quantifying the number of overlapping pixels. 
To obtain the percentage of a marker that is colocalized with another, it can be calculated by dividing the colocalized pixels by the total amount present within an image.  
For comparing amounts of active TOM20 or CHCHD2 signals of different data sets, the amounts of active markers per image were normalized by the amount of DAPI signal per image to account for the fact that different images do not necessarily contain the same amount and size of cells. Additionally, the mean TOM20 and CHCHD2 intensities per image of the remaining signals were extracted and stored along all other obtained data in a CSV file.
A Mann-Whitney-U-test was used to test for differences between data sets (cell lines or treatments) because equal variances and normal distributions could not be validated.  


## References 

```bibtex
@article{van2014scikit,
  title={scikit-image: image processing in Python},
  author={Van der Walt, Stefan and Sch{\"o}nberger, Johannes L and Nunez-Iglesias, Juan and Boulogne, Fran{\c{c}}ois and Warner, Joshua D and Yager, Neil and Gouillart, Emmanuelle and Yu, Tony},
  journal={PeerJ},
  volume={2},
  pages={e453},
  year={2014},
  publisher={PeerJ Inc.}
} 

@article{opencv,
    author = {Bradski, G.},
    citeulike-article-id = {2236121},
    journal = {Dr. Dobb's Journal of Software Tools},
    keywords = {bibtex-import},
    posted-at = {2008-01-15 19:21:54},
    priority = {4},
    title = {{The OpenCV Library}},
    year = {2000}
}
```
