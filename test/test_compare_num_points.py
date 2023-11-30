import laspy

def open_las_and_read_number_of_points(path_to_las):
    # works with laz files too
    with laspy.open(path_to_las) as fh:
        points_from_header = fh.header.point_count
    return points_from_header

def open_csv_and_read_number_of_points(path_to_csv, point_cloud_name):
    import csv
    
    with open(path_to_csv, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if point_cloud_name in row["name"]:
                return int(row["count"])
            
    print("Could not match a given point cloud in the csv file.")
    print(f"CSV file: {path_to_csv}, point cloud: {point_cloud_name}")

def get_referenced_number_of_points(path_to_data, extra_name):
    if path_to_data.endswith((".las", ".laz")):
        return open_las_and_read_number_of_points(path_to_data)
    if path_to_data.endswith(".csv"):
        return open_csv_and_read_number_of_points(path_to_data, extra_name)


def test_compare_number_of_points(path_to_las, reference_data, extra_name = None):
    points_from_data = open_las_and_read_number_of_points(path_to_las)
    print(f"Points from data: {points_from_data}")

    reference_number_of_points = get_referenced_number_of_points(reference_data, extra_name)
    print(f"Reference number of points: {reference_number_of_points}")

    assert reference_number_of_points == points_from_data
    print("Number of points match!")


if __name__ == "__main__":
    import sys

    las_file_to_be_tested = sys.argv[1]
    reference_data = sys.argv[2]
    point_cloud_name = None
    if len(sys.argv) == 4:
        point_cloud_name = sys.argv[3]
    test_compare_number_of_points(las_file_to_be_tested, reference_data, point_cloud_name)
