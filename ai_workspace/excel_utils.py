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



def WriteToExcel():
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet_s = workbook.add_worksheet("Glossary")
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
    worksheet_s.write(0, 2, ugettext("SL_Term"), unlocked)
    worksheet_s.write(0, 3, ugettext("TL_Term"), unlocked)
    worksheet_s.write(0, 4, ugettext("POS"), unlocked)
    worksheet_s.write(0, 5, ugettext("SL_Definition"), unlocked)
    worksheet_s.write(0, 6, ugettext("TL_Definition"), unlocked)
    worksheet_s.write(0, 7, ugettext("Context"), unlocked)
    worksheet_s.write(0, 8, ugettext("Note"), unlocked)
    worksheet_s.write(0, 9, ugettext("SL_Source"), unlocked)
    worksheet_s.write(0, 10, ugettext("TL_Source"), unlocked)
    worksheet_s.write(0, 11, ugettext("Gender"), unlocked)
    worksheet_s.write(0, 12, ugettext("Termtype"), unlocked)
    worksheet_s.write(0, 13, ugettext("Geographical_Usage"), unlocked)
    worksheet_s.write(0, 14, ugettext("Usage Status"), unlocked)
    worksheet_s.write(0, 15, ugettext("Term location"), unlocked)

    # column widths
    sl_term_col_width       = 25
    tl_term_col_width       = 25
    sl_definition_col_width = 20
    tl_definition_col_width = 20
    sl_source_col_width     = 15
    tl_source_col_width     = 15
    geographical_usage_col_width = 20

    # change column widths
    worksheet_s.set_column('C:C', sl_term_col_width, unlocked)  # SL_Term column
    worksheet_s.set_column('D:D', tl_term_col_width, unlocked)  # TL_term column
    worksheet_s.set_column('F:F', sl_definition_col_width, unlocked)  # SL_Definition column
    worksheet_s.set_column('G:G', tl_definition_col_width, unlocked)  # TL_Definition column
    worksheet_s.set_column('J:J', sl_source_col_width, unlocked)  # SL_Source column
    worksheet_s.set_column('K:K', tl_source_col_width, unlocked)  # TL_Source column
    worksheet_s.set_column('N:N', geographical_usage_col_width, unlocked)  # Geo Usage column
    worksheet_s.set_column('O:O', tl_source_col_width, unlocked) #Usage status column
    worksheet_s.set_column('P:P', tl_source_col_width, unlocked) # Term location column

    worksheet_s.set_column('A:A', None, None, {'hidden': True})
    worksheet_s.set_column('B:B', None, None, {'hidden': True})

    worksheet_s.data_validation('E2:E100000',
                                    {'validate': 'list',
                                    'source': ['Verb', 'Noun', 'Adjective', 'Adverb', 'Pronoun', 'Other']
                                    }
                            )
    worksheet_s.data_validation('L2:L100000',
                                    {'validate': 'list',
                                    'source': ['Masculine', 'Feminine', 'Neutral', 'Other']
                                    }
                            )
    worksheet_s.data_validation('M2:M100000',
                                    {'validate': 'list',
                                    'source': ['fullForm', 'acronym', 'abbreviation', 'shortForm', 'variant', 'phrase']
                                    }
                            )
    worksheet_s.data_validation('O2:O100000',
                                    {'validate': 'list',
                                    'source': ['preferred', 'admitted', 'notRecommended', 'obsolete']
                                    }
                            )

    # close workbook
    workbook.close()
    xlsx_data = output.getvalue()
    return xlsx_data
