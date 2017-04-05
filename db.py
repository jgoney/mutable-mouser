import csv
import sqlite3

from prettytable import PrettyTable


def init_db():
    conn = sqlite3.connect('inventory.sqlite')
    c = conn.cursor()
    try:
        c.execute('DROP TABLE items;')
        c.execute(open('inventory.sql', 'r').read())
        conn.commit()
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()


def add_mouser_invoice(invoice):
    fieldnames = ["index", "mouser_number", "manufacturer_number", "manufacturer", "customer_number", "description",
                  "rohs", "lifecycle", "qty", "price", "total"]

    with open(invoice, 'r', encoding='utf-8') as csvfile:
        array = [row for row in csv.DictReader(csvfile, delimiter=';', fieldnames=fieldnames)]
        array = array[9:]

        conn = sqlite3.connect('inventory.sqlite')
        c = conn.cursor()

        for i in array:
            if i['mouser_number']:
                try:
                    c.execute(
                        """
                        INSERT INTO items
                        VALUES (:mouser_number, :manufacturer_number, :manufacturer, :customer_number,
                          :description, :rohs, :lifecycle, :qty, :price, :total);
                        """, i)
                except sqlite3.IntegrityError:
                    # print("%s exists, updating quantity by %s" % (i['mouser_number'], i['qty']))
                    c.execute(
                        """
                        UPDATE items
                        SET qty = qty + :qty
                        WHERE mouser_number =:mouser_number;
                        """, i)

        conn.commit()
        conn.close()


def subtract_invoice(invoice, fieldnames):
    with open(invoice, 'r', encoding='utf-8') as csvfile:
        conn = sqlite3.connect('inventory.sqlite')
        c = conn.cursor()

        array = [row for row in csv.DictReader(csvfile, delimiter=';', fieldnames=fieldnames)]
        array = array[3:]
        for row in array:
            if row['mouser_number']:
                # print("deincrementing %s by %s" % (row['mouser_number'], row['qty']))
                c.execute(
                    """
                    UPDATE items
                    SET qty = qty - :qty
                    WHERE mouser_number =:mouser_number;
                    """, row)

                conn.commit()
        conn.close()


def subtract_mutable_invoice(invoice):
    fieldnames = ["index", "qty", "description", "specs", "value", "package", "mouser_number", "references"]
    return subtract_invoice(invoice, fieldnames)


def subtract_synthrotek_invoice(invoice):
    fieldnames = ["mfg part number", "qty", "Mfg Part Number", "Mfg Name", "mouser_number", "Description", "Price",
                  "Min/Mult", "Stock", "Lead Time", "Lifecycle", "NCNR", "RoHS", "Suggested Replacement",
                  "RoHS Replacement", "PB Free", "Package Type", "Package Quantity", "Package Price", "Data Sheet URL",
                  "Product Image"]

    return subtract_invoice(invoice, fieldnames)


def check_invoice(invoice, fieldnames, invoice_type):
    with open(invoice, 'r', encoding='utf-8') as csvfile:
        conn = sqlite3.connect('inventory.sqlite')
        c = conn.cursor()

        array = [row for row in csv.DictReader(csvfile, delimiter=';', fieldnames=fieldnames)]

        if invoice_type == 'mutable':
            array = array[3:]
        elif invoice_type == 'synthrotek':
            array = array[1:]
        elif invoice_type == 'ubraids':
            array = array[7:]

        table_rows = []

        for row in array:
            if row['mouser_number']:
                c.execute(
                    """
                    SELECT mouser_number, manufacturer, description, qty
                    FROM items
                    WHERE mouser_number =:mouser_number
                    """, row)

                query = c.fetchone()
                item = None

                if not query:
                    # print("%s not found, %s needed for %s" % (row['mouser_number'], row['qty'], invoice))

                    table_rows.append((row['mouser_number'], row['description'], 0, row['qty'],
                                       0 - int(row['qty']), abs(0 - int(row['qty'])), invoice))

                    item = {'mouser_number': row['mouser_number'], 'qty': row['qty']}

                else:
                    # print(query)
                    if query[-1] < int(row['qty']):
                        # item = {'mouser_number': row['mouser_number'], 'qty': abs(query[-1] - int(row['qty']))}
                        item = {'mouser_number': row['mouser_number'], 'qty': row['qty']}

                        table_rows.append((row['mouser_number'], row['description'], query[-1], row['qty'],
                                           query[-1] - int(row['qty']), abs(query[-1] - int(row['qty'])), invoice))

                if item:
                    try:
                        c.execute(
                            """
                            INSERT INTO orders
                            VALUES (:mouser_number, :qty);
                            """, item)
                        conn.commit()
                    except sqlite3.IntegrityError:
                        c.execute(
                            """
                            UPDATE orders
                            SET qty = qty + :qty
                            WHERE mouser_number =:mouser_number;
                            """, item)
                        conn.commit()

        conn.close()
        return table_rows


def check_synthrotek_invoice(invoice):
    fieldnames = ["mfg part number", "qty", "Mfg Part Number", "Mfg Name", "mouser_number", "description",
                  "Price",
                  "Min/Mult", "Stock", "Lead Time", "Lifecycle", "NCNR", "RoHS", "Suggested Replacement",
                  "RoHS Replacement", "PB Free", "Package Type", "Package Quantity", "Package Price",
                  "Data Sheet URL",
                  "Product Image"]
    return check_invoice(invoice, fieldnames, 'synthrotek')


def check_mutable_invoice(invoice):
    fieldnames = ["component_ids", "qty", "description", "specs", "value", "package", "mouser_number", "references"]

    return check_invoice(invoice, fieldnames, 'mutable')


def check_other_invoice(invoice, invoice_type):
    fieldnames = ["mouser_number", "manufacturer_number", "manufacturer", "customer_number", "description",
                  "rohs", "lifecycle", "qty", "price", "total"]

    return check_invoice(invoice, fieldnames, invoice_type)


def init_new_order():
    conn = sqlite3.connect('inventory.sqlite')
    c = conn.cursor()
    try:
        c.execute('DROP TABLE orders;')
        c.execute(open('order.sql', 'r').read())
        conn.commit()
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()

    add_mouser_invoice('BOMs/mouser_order_1.csv')
    add_mouser_invoice('BOMs/mouser_order_2.csv')
    add_mouser_invoice('BOMs/mouser_order_3.csv')
    add_mouser_invoice('BOMs/mouser_order_4.csv')
    add_mouser_invoice('BOMs/mouser_order_5.csv')

    subtract_synthrotek_invoice('BOMs/AtariPunkConsole.csv')
    subtract_synthrotek_invoice('BOMs/DLY.csv')
    subtract_synthrotek_invoice('BOMs/CombineOr.csv')

    # Remove one STM32F103CBT6 from inventory from first failed Tides build
    conn = sqlite3.connect('inventory.sqlite')
    c = conn.cursor()
    c.execute(
        """
        UPDATE items
        SET qty = qty - 1
        WHERE mouser_number =?;
        """, ('511-STM32F103CBT6',))

    conn.commit()

    # Also account for missing 270 Ohm resistors
    c.execute(
        """
        UPDATE items
        SET qty = 1
        WHERE mouser_number =?;
        """, ('652-CR0603FX-2700ELF',))

    conn.commit()
    conn.close()

    subtract_mutable_invoice('BOMs/Shades.csv')
    subtract_mutable_invoice('BOMs/Branches.csv')
    subtract_mutable_invoice('BOMs/Tides.csv')
    subtract_mutable_invoice('BOMs/Kinks.csv')
    subtract_mutable_invoice('BOMs/Tides.csv')
    subtract_mutable_invoice('BOMs/Ripples.csv')
    subtract_mutable_invoice('BOMs/Peaks.csv')
    subtract_mutable_invoice('BOMs/Shades.csv')

    # Account for destroyed STM32F405RGT6 chip (failed Clouds build)  511-STM32F405RGT6
    conn = sqlite3.connect('inventory.sqlite')
    c = conn.cursor()
    c.execute(
        """
        UPDATE items
        SET qty = qty - 1
        WHERE mouser_number =?;
        """, ('511-STM32F405RGT6',))

    conn.commit()

    init_new_order()

    t = PrettyTable(['Part #', 'Description', 'You have', 'Needed qty', 'Difference', 'Order at least', 'Needed for'])

    invoices = ('BOMs/Clouds.csv', 'BOMs/Peaks.csv', 'BOMs/Veils.csv', 'BOMs/Links.csv')
    for i in invoices:
        for row in check_mutable_invoice(i):
            t.add_row(row)

    # for row in check_synthrotek_invoice('BOMs/AtariPunkConsole.csv'):
    #     t.add_row(row)

    for row in check_other_invoice('BOMs/uBraids.csv', 'ubraids'):
        t.add_row(row)

    print(t.get_string(sortby="Part #"))

    """
140-50S5-101J-RC not found, 4 needed for BOMs/MSTDualVCA.csv
291-2.2K-RC not found, 2 needed for BOMs/MSTDualVCA.csv
291-39K-RC not found, 2 needed for BOMs/MSTDualVCA.csv
291-5.1K-RC not found, 2 needed for BOMs/MSTDualVCA.csv
291-7.5K-RC not found, 1 needed for BOMs/MSTDualVCA.csv
595-TL074CN not found, 1 needed for BOMs/MSTDualVCA.csv
649-DILB18P223TLF not found, 1 needed for BOMs/MSTDualVCA.csv
871-B41827A9106M000 not found, 2 needed for BOMs/MSTDualVCA.csv
    """
