# multimaze_recorder
Tools to operate Matthias' high-throughput recording setup

This repository includes tools to operate the imaging source camera using tiscamera software and dedicated python scripts to record and analyze the data.

## Scripts

### Trigger_images.py

This script is used to capture images using Arduino hardware triggering. This is the one used when the "hardware trigger" checkbox is checked in the GUI.

## GUI

### About the metadata registry

You might notice that known variables are always present in the table. They can be removed before saving and won't show in the final metadata.json file. It's a wanted feature of the GUI. The reason all the know variables are always displayed is twofolds: 

1) One might forget the exact syntax used for a given variable (e.g. "Date" vs "date" vs "day" etc.). Once one has been chosen (e.g. "date"), it will automatically show up on subsequent experiments of the same type which reduces the risk of syntax issues.
2) If a new variable is set and an older folder is opened, the new variable will also show up, reminding the user that this needs to be updated, reducing the risk of unforeseen issues down the line. In practice, this second reason is less likely to be an issue because usually, older experiments will have some default value for newly set variables that can be used if no other value is found in the metadata. For instance, if older experiments were all performed with a controlled genotype, then after setting a "genotype" variable, if none is found in a given experiment, it can be safely defaulted to Control. However, it makes the defaulting implicit.