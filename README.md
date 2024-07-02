Lizard Wizard
=============

Calcium imaging analysis for the Arc Institute.



# Resources

* [calcium_image_analysis codebase](https://github.com/ArcInstitute/calcium_image_analysis)


# Workflow

## Input

* Params
  * Directory of images (`*.czi` files)
  * Output directory


## Processing

* Create sample sheet
  * Python script to create csv file of images
* Load sample sheet as channel
* If `spot_check > 0`, randomly subsample images
* For each image:
  * run `zeiss_caiman_process` 
    * mask each image
      * cellpose detection
    * run `caiman` on each image
      * [setup_cluster() info](https://github.com/flatironinstitute/CaImAn/blob/e7e86411e80639c81d8ea58026660913739704f7/docs/source/Getting_Started.rst#cluster-setup-and-shutdown)
  


