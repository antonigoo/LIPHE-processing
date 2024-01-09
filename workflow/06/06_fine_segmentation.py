import sys
import os

# load user configurations from external file
import yaml

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open("user_config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# add functions to path
# os.chdir(config['function_path'])
sys.path.append(os.path.join(config["function_path"], "Functions"))

# custom packages
import lbl_segment


# other python libraries
import glob

input_las_dir = snakemake.input[0]
output_las_dir = snakemake.output.output_dir[0]
output_noise_dir = snakemake.output.output_dir_noise[0]

output_las_dir = os.path.join(output_las_dir, '')  # adds / at the end if it is not there
output_noise_dir = os.path.join(output_noise_dir, '')  # adds / at the end if it is not there

if not os.path.exists(output_las_dir):
    os.makedirs(output_las_dir)

if not os.path.exists(output_noise_dir):
    os.makedirs(output_noise_dir)

input_files_list = glob.glob(input_las_dir + "/*.laz")

for input_file in input_files_list:
    # I guess tree_id == the number at the end of the filename of single tree las
    tree_id = int(
        os.path.basename(input_file).rsplit(".", 1)[0].split("_")[-1]
    )
    print(f"tree id {tree_id}")
    output_pc = output_las_dir + os.path.basename(input_file)
    output_noise = output_noise_dir + os.path.basename(input_file)

    try:
        lbl_segment.lbl_segment(
            path_to_pc=input_file,
            path_to_tree_map=config["tree_map"],
            tree_id=tree_id, 
            output_path_main=output_pc,
            output_path_noise=output_noise,
            write_other=True,
            x_offset=357676.852,
            y_offset=6860035.171,
            ref_dist_max=config["ref_dist_max"]
        )
    except Exception as e:
        print(f"Cloud {input_file} failed, reason:")
        print(e)
        print("Continuing with the next cloud")
