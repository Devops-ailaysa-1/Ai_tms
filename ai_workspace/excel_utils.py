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
        'bold': True,
        'bg_color': '#ffffcc',
        'color': 'black',
        'align': 'centre',
        'valign': 'top',
        'border': 1,
        'locked': True
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
    worksheet_s.write(0, 2, ugettext("Source language term"),header)
    worksheet_s.write(0, 3, ugettext("Target language term"),header)


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
        'bold': True,
        'bg_color': '#ffffcc',
        'color': 'black',
        'align': 'centre',
        'valign': 'top',
        'border': 1,
        'locked': True
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
    worksheet_s.write(0, 2, ugettext("Source language term"), header)
    worksheet_s.write(0, 3, ugettext("Target language term"), header)
    worksheet_s.write(0, 4, ugettext("POS"), header)
    worksheet_s.write(0, 5, ugettext("Source language Definition"), header)
    worksheet_s.write(0, 6, ugettext("Target language Definition"), header)
    worksheet_s.write(0, 7, ugettext("Context"), header)
    worksheet_s.write(0, 8, ugettext("Note"), header)
    worksheet_s.write(0, 9, ugettext("Source language Source"), header)
    worksheet_s.write(0, 10, ugettext("Target language Source"), header)
    worksheet_s.write(0, 11, ugettext("Gender"), header)
    worksheet_s.write(0, 12, ugettext("Termtype"), header)
    worksheet_s.write(0, 13, ugettext("Geographical_Usage"), header)
    worksheet_s.write(0, 14, ugettext("Usage Status"), header)
    worksheet_s.write(0, 15, ugettext("Term location"), header)

    # column widths
    sl_term_col_width       = 25
    tl_term_col_width       = 25
    sl_definition_col_width = 30
    tl_definition_col_width = 30
    sl_source_col_width     = 25
    tl_source_col_width     = 25
    geographical_usage_col_width = 20

    # change column widths
    worksheet_s.set_column('C:C', sl_term_col_width, unlocked)  # SL_Term column
    worksheet_s.set_column('D:D', tl_term_col_width, unlocked)  # TL_term column
    worksheet_s.set_column('E:E', sl_source_col_width, unlocked) #POS column
    worksheet_s.set_column('F:F', sl_definition_col_width, unlocked)  # SL_Definition column
    worksheet_s.set_column('G:G', tl_definition_col_width, unlocked)  # TL_Definition column
    worksheet_s.set_column('H:H', tl_source_col_width, unlocked) #context column
    worksheet_s.set_column('I:I', tl_source_col_width, unlocked) #note column
    worksheet_s.set_column('J:J', sl_source_col_width, unlocked)  # SL_Source column
    worksheet_s.set_column('K:K', tl_source_col_width, unlocked)  # TL_Source column
    worksheet_s.set_column('L:L', tl_source_col_width, unlocked)  #Gender column
    worksheet_s.set_column('M:M', tl_source_col_width, unlocked)  #Termtype column
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




def WriteToExcel_wordchoice():
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet_s = workbook.add_worksheet("WordChoice")
    unlocked = workbook.add_format({'locked': False})
    locked =  workbook.add_format({'locked': True})
    header = workbook.add_format({
        'bold': True,
        'bg_color': '#ffffcc',
        'color': 'black',
        'align': 'centre',
        'valign': 'top',
        'border': 1,
        'locked': True
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
    worksheet_s.write(0, 2, ugettext("Source language term"),header)
    worksheet_s.write(0, 3, ugettext("Target language term"),header)
    worksheet_s.write(0, 4, ugettext("POS"), header)

    # column widths
    sl_term_col_width       = 25
    tl_term_col_width       = 25
    sl_source_col_width     = 25


    # change column widths
    worksheet_s.set_column('C:C', sl_term_col_width,unlocked)  # SL_Term column
    worksheet_s.set_column('D:D', tl_term_col_width,unlocked)  # TL_term column
    worksheet_s.set_column('E:E', sl_source_col_width, unlocked) #POS

    worksheet_s.set_column('A:A', None, None, {'hidden': True})
    worksheet_s.set_column('B:B', None, None, {'hidden': True})


    worksheet_s.data_validation('E2:E100000',
                                    {'validate': 'list',
                                    'source': ['Verb', 'Noun', 'Adjective', 'Adverb', 'Pronoun', 'Other']
                                    }
                            )

    workbook.close()
    xlsx_data = output.getvalue()
    return xlsx_data