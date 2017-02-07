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


def scale_mi_bom(bom, qty):
    for k in bom:
        if k and k != 'ref. mouser':
            bom[k]['Qty'] = qty * int(bom[k]['Qty'])

    return bom

mouser = get_mouser_reader("BOMs/mouser_order.csv")

branches = get_mi_reader("BOMs/Branches.csv")
kinks = get_mi_reader("BOMs/Kinks.csv")
ripples = get_mi_reader("BOMs/Ripples.csv")
shades = get_mi_reader("BOMs/Shades.csv")
tides = get_mi_reader("BOMs/Tides.csv")

tides = scale_mi_bom(tides, 2)

branches_set = get_set_from_mi_bom(branches)
kinks_set = get_set_from_mi_bom(kinks)
ripples_set = get_set_from_mi_bom(ripples)
shades_set = get_set_from_mi_bom(shades)
tides_set = get_set_from_mi_bom(tides)

# common_parts = {part: 0 for part in (tides_set)}
# common_parts = {part: 0 for part in (tides_set | kinks_set)}
common_parts = {part: 0 for part in (shades_set) & (tides_set | kinks_set)}
# common_parts = {part: 0 for part in (branches_set | ripples_set | shades_set | tides_set | kinks_set)}

t = PrettyTable(['Line #', 'Part #', 'Description', 'Ordered qty', 'Needed qty', 'Difference',
                 'Order at least', 'MPart #'])

line_no = 0
for part_no in common_parts:
    for bom in (shades,):
        # for bom in (kinks, tides):
        # for bom in (branches, kinks, ripples, shades, tides):
        try:
            common_parts[part_no] += int(bom[part_no]['Qty'])
        except KeyError:
            pass

    try:
        if int(mouser[part_no]['Order Qty.']) - common_parts[part_no] < 3:
            line_no += 1
            t.add_row(
                (line_no, mouser[part_no]['Mouser No'], mouser[part_no]['Description'], mouser[part_no]['Order Qty.'],
                 common_parts[part_no], int(mouser[part_no]['Order Qty.']) - common_parts[part_no],
                 abs(int(mouser[part_no]['Order Qty.']) - common_parts[part_no]), mouser[part_no]['Mouser No']))
    except KeyError:
        print "%s not found in your order" % (part_no,)

print t
