from argparse import ArgumentParser
from members import Group


def main():
    parser = ArgumentParser("Sparro")
    parser.add_argument('-d', "--data", help="path of the data json file. Look for data.json for an example", required=True, type=str)
    parser.add_argument("-n", '--name', help="Group Name (optional)", default="Test Group", required=False, type=str)
    parser.add_argument('-o', '--out', help="Output json path", default="matched_result.json", required=False, type=str)
    args = parser.parse_args()
    json_data_path = args.data
    assert json_data_path.endswith(".json"), "data path must be a json file, look data.json for example"
    assert args.out.endswith(".json"), "Output path must be a .json file"
    group = Group(gr_name=args.name)
    with open(json_data_path, "rb") as jsf:
        jsd = jsf.read().decode("utf-8")
        group.read_members_from_json(jsd, mode="json_string")
    group.sparrow()  # initial match
    matches = group.get_all_matches(output_path=args.out, fmt="json")
    print(f"\nFind the matched result below (result is also written on {args.out} file): \n")
    print(matches)

if __name__ == "__main__":
    main()
