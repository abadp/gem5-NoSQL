#*******************************************************************************
# GENERAL CONFIGURATION SCRIPT
# Contains main config parameters for both ckpt generation and simulation runs
#*******************************************************************************

# Path to gem5 repository (local)
gem5_dir = "/absolute/path/to/your/GEM5"

# Disks images and kernel files paths and variables
images_dir = gem5_dir + "/images/"
kernels_dir = images_dir + "kernels/"
disks_dir = images_dir + "disks/"
kernel = "x86_64-vmlinux-3.18.34_ceconfig.smp"
