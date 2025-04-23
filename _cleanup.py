import json


def csv_to_json(csv_file):
    """
    convert csv to json
    csv has no header and is in shape of: sku, name, r, g, b

    json should be in shape of: brand: sku, name, color

    color should be a list of lists such that there can be an arbitrary number of colors
    """

    csv_data: list = []
    with open(csv_file, 'r') as f:
        csv_data = f.readlines()

    json_data: dict = {}
    for line in csv_data:
        print(line)
        sku, name, r, g, b = line.strip().split(',')
        color = [int(r), int(g), int(b)]
        if sku not in json_data:
            skein = {'name': name.strip(), 'color': [color]}
            print(skein)
            json_data[sku] = skein

    # make new json file
    with open('catalogs/dmc.json', 'w') as f:
        f.write(json.dumps(json_data, indent=4))


csv_to_json('catalogs/_dmc.csv')