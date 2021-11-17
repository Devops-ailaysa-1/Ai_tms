from io import BytesIO
import xlsxwriter
from django.utils.translation import ugettext


######### WRITING TEMPLATE LITE #############
def WriteToExcel_lite():
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet_s = workbook.add_worksheet("Glossary_Lite")
    unlocked = workbook.add_format({'locked': False})
    locked =  workbook.add_format({'locked': True})
    header = workbook.add_format({
        'bg_color': '#ffffcc',
        'color': 'black',
        'align': 'centre',
        'valign': 'top',
        'border': 1
    })
    cell = workbook.add_format({
        'align': 'left',
        'valign': 'top',
        'text_wrap': True,
        'border': 1
    })
    cell_center = workbook.add_format({
        'align': 'center',
        'valign': 'top',
        'border': 1
    })


    worksheet_s.protect()
    # write header
    worksheet_s.write(0, 1, ugettext("ID"), header)
    worksheet_s.write(0, 2, ugettext("Source language term"),unlocked)
    worksheet_s.write(0, 3, ugettext("Target language term"),unlocked)


    # column widths
    sl_term_col_width       = 25
    tl_term_col_width       = 25


    # change column widths
    worksheet_s.set_column('C:C', sl_term_col_width,unlocked)  # SL_Term column
    worksheet_s.set_column('D:D', tl_term_col_width,unlocked)  # TL_term column


    worksheet_s.set_column('A:A', None, None, {'hidden': True})
    worksheet_s.set_column('B:B', None, None, {'hidden': True})

    workbook.close()
    xlsx_data = output.getvalue()
    return xlsx_data
