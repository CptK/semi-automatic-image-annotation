# Semi-automatic Image Annotator
Image Annotation Tool with YOLO Bounding Box Suggestions. The following GIF shows a demonstration of the
tool on some images from the [Dogs vs. Cats](https://www.kaggle.com/c/dogs-vs-cats) dataset.

![Demonstration](https://github.com/CptK/semi-automatic-image-annotation/blob/main/Cats-vs-dogs.gif)

## Limitations / Future Work
- Only saving to YOLO format is supported.
- The dataset is only saved once all images in the original directory have been processed. One can not save and continue later.
- Only images from one source can be processed. It could be beneficial to be able to pass multiple data sources.
- Bounding Boxes cannot be changed. They can only be deleted and redrawn in the desired way.
- It is not possible to zoom into the images to draw Bounding Boxes more precisely.
- Design.
