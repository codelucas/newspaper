# -*- coding: utf-8 -*-
"""
Scrape a table from wikipedia using python. Allows for cells spanning multiple rows and/or columns. Outputs csv files for
each table
url: https://gist.github.com/wassname/5b10774dfcd61cdd3f28
authors: panford, wassname, muzzled, Yossi
license: MIT
"""

from bs4 import BeautifulSoup
import requests
import os
import codecs
wiki = "https://en.wikipedia.org/wiki/International_Phonetic_Alphabet_chart_for_English_dialects"
header = {
    'User-Agent': 'Mozilla/5.0'
}  # Needed to prevent 403 error on Wikipedia
page = requests.get(wiki, headers=header)
soup = BeautifulSoup(page.content)

tables = soup.findAll("table", {"class": "wikitable"})

# show tables
for i, table in enumerate(tables):
    print("#"*10 + "Table {}".format(i) + '#'*10)
    print(table.text[:100])
    print('.'*80)
print("#"*80)

for tn, table in enumerate(tables):

    # preinit list of lists
    rows = table.findAll("tr")
    row_lengths = [len(r.findAll(['th', 'td'])) for r in rows]
    ncols = max(row_lengths)
    nrows = len(rows)
    data = []
    for i in range(nrows):
        rowD = []
        for j in range(ncols):
            rowD.append('')
        data.append(rowD)

    # process html
    for i in range(len(rows)):
        row = rows[i]
        rowD = []
        cells = row.findAll(["td", "th"])
        for j in range(len(cells)):
            cell = cells[j]

            #lots of cells span cols and rows so lets deal with that
            cspan = int(cell.get('colspan', 1))
            rspan = int(cell.get('rowspan', 1))
            l = 0
            for k in range(rspan):
                # Shifts to the first empty cell of this row
                while data[i + k][j + l]:
                    l += 1
                for m in range(cspan):
                    cell_n = j + l + m
                    row_n = i + k
                    # in some cases the colspan can overflow the table, in those cases just get the last item
                    cell_n = min(cell_n, len(data[row_n])-1)
                    data[row_n][cell_n] += cell.text
                    print(cell.text)

        data.append(rowD)

    # write data out to tab seperated format
    page = os.path.split(wiki)[1]
    fname = 'output_{}_t{}.tsv'.format(page, tn)
    f = codecs.open(fname, 'w')
    for i in range(nrows):
        rowStr = '\t'.join(data[i])
        rowStr = rowStr.replace('\n', '')
        print(rowStr)
        f.write(rowStr + '\n')

    f.close()
