import csv

from prettytable import PrettyTable


def get_mi_reader(filename):
    fieldnames = ["Index", "Qty", "Description", "Specs", "Value", "Package", "Ref. Mouser", "References"]
    with open(filename, 'r') as csvfile:
        return {row['Ref. Mouser'].replace('-', '').lower().strip(): row for row in
                csv.DictReader(csvfile, fieldnames=fieldnames)}


def get_mouser_reader(filename):
    fieldnames = ["index", "Mouser No", " Mfr. No", "Manufacturer", "Customer No", "Description", "RoHS", "Lifecycle",
                  "Order Qty.", "Price (EUR)", "Ext: (EUR)"]
    with open(filename, 'r') as csvfile:
        return {row['Mouser No'].replace('-', '').lower().strip(): row for row in
                csv.DictReader(csvfile, fieldnames=fieldnames)}


def get_set_from_mi_bom(bom):
    return set([i for i in bom if i and i != 'ref. mouser'])


mouser = get_mouser_reader("BOMs/mouser_order.csv")

branches = get_mi_reader("BOMs/Branches.csv")
kinks = get_mi_reader("BOMs/Kinks.csv")
ripples = get_mi_reader("BOMs/Ripples.csv")
shades = get_mi_reader("BOMs/Shades.csv")
tides = get_mi_reader("BOMs/Tides.csv")

branches_set = get_set_from_mi_bom(branches)
kinks_set = get_set_from_mi_bom(kinks)
ripples_set = get_set_from_mi_bom(ripples)
shades_set = get_set_from_mi_bom(shades)
tides_set = get_set_from_mi_bom(tides)

common_parts = {part: 0 for part in (tides_set | kinks_set)}
# common_parts = {part: 0 for part in (branches_set | ripples_set | shades_set) & (tides_set | kinks_set)}

t = PrettyTable(['Line #', 'Part #', 'Description', 'Ordered qty', 'Needed qty', 'Difference'])

for i, p in enumerate(common_parts):
    for bom in (kinks, tides):
        # for bom in (branches, kinks, ripples, shades, tides):
        try:
            common_parts[p] += int(bom[p]['Qty'])
        except KeyError:
            pass

    try:
        t.add_row((i + 1, p, mouser[p]['Description'], mouser[p]['Order Qty.'], common_parts[p],
                   int(mouser[p]['Order Qty.']) - common_parts[p]))
    except KeyError:
        print "%s not found in your order" % (p,)

print t
