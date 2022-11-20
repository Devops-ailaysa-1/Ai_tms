from ai_workspace.models import Job
from datetime import datetime
from ai_tm.models import WordCountGeneral


def get_languages(proj):

    jobs = Job.objects.filter(project=proj.id)
    sl = jobs[0].source_language.language
    tl = ""
    for job in jobs:
        tl += job.target_language.language
        if job != jobs.last():
            tl += ", "

    return sl + " --> " + tl

def write_project_header(worksheet, proj):

    worksheet.write('A1', 'Project analysis report')

    # Row 2
    worksheet.write('A2', 'Project:')
    worksheet.write('B2', proj.project_name)

    # Row 3
    worksheet.write('A3', 'Languages')
    worksheet.write('B3', get_languages(proj))

    # Row 4
    worksheet.write('A4', 'Date:')
    worksheet.write('B4', datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

def write_common_rows(worksheet, row_no):
    # Writing first row
    worksheet.write(f'A{row_no}', "Total")
    worksheet.write(f'B{row_no}', "Weighted")
    worksheet.write(f'C{row_no}', "New")
    worksheet.write(f'D{row_no}', "Repetition")
    worksheet.write(f'E{row_no}', "50-74%")
    worksheet.write(f'F{row_no}', "75-84%")
    worksheet.write(f'G{row_no}', "85-94%")
    worksheet.write(f'H{row_no}', "95-99%")
    worksheet.write(f'I{row_no}', "100%")
    worksheet.write(f'J{row_no}', "101%")
    worksheet.write(f'K{row_no}', "102%")

    # Writing second row
    worksheet.write(f'B{row_no + 1}', "Payable rate")
    worksheet.write(f'C{row_no + 1}', "100%")
    worksheet.write(f'D{row_no + 1}', "30%")
    worksheet.write(f'E{row_no + 1}', "100%")
    worksheet.write(f'F{row_no + 1}', "60%")
    worksheet.write(f'G{row_no + 1}', "60%")
    worksheet.write(f'H{row_no + 1}', "60%")
    worksheet.write(f'I{row_no + 1}', "30%")
    worksheet.write(f'J{row_no + 1}', "30%")
    worksheet.write(f'K{row_no + 1}', "30%")

def write_commons(worksheet, proj):

    # For project
    proj_row = 6
    write_common_rows(worksheet, proj_row)

    tasks = proj.get_tasks
    for task in tasks:
        proj_row += 5
        write_common_rows(worksheet, proj_row)

def write_data_rows(worksheet, row_no, new, rep, c100, \
                       c95_99, c85_94, c75_84, c50_74, c101, c102, raw):

    wwc = round(new + (0.3 * rep) + c50_74 + (0.6 * c75_84) + (0.6 * c85_94) + (0.6 * c95_99) + \
                  (0.3 * c100) + (0.3 * c101) + (0.3 * c102))

    worksheet.write(f'A{row_no}',raw)
    worksheet.write(f'B{row_no}', wwc)
    worksheet.write(f'C{row_no}', new)
    worksheet.write(f'D{row_no}', rep)
    worksheet.write(f'E{row_no}', c50_74)
    worksheet.write(f'F{row_no}', c75_84)
    worksheet.write(f'G{row_no}', c85_94)
    worksheet.write(f'H{row_no}', c95_99)
    worksheet.write(f'I{row_no}', c100)
    worksheet.write(f'J{row_no}', c101)
    worksheet.write(f'K{row_no}', c102)

def write_task_details(worksheet, proj, proj_row):

    tasks = proj.get_tasks
    for task in tasks:
        proj_row += 2
        worksheet.write(f'A{proj_row}', "Task: ")
        worksheet.write(f'B{proj_row}', task.file.filename + ", " + task.job.source_language.language \
                        + " --> " + task.job.target_language.language)
def write_data(worksheet, proj):

    # Initializing word count values
    pnew, prep, p100, p95_99, p85_94, p75_84, p50_74, p101, p102, praw = \
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0

    proj_row = 8

    write_task_details(worksheet, proj, proj_row)

    # Adding word count from each task
    task_wcs = WordCountGeneral.objects.filter(project_id=proj.id)
    for tk_wc in task_wcs:
        pnew += tk_wc.new_words
        prep += tk_wc.repetition
        p100 += tk_wc.tm_100
        p95_99 += tk_wc.tm_95_99
        p85_94 += tk_wc.tm_85_94
        p75_84 += tk_wc.tm_75_84
        p50_74 += tk_wc.tm_50_74
        p101 += tk_wc.tm_101
        p102 += tk_wc.tm_102
        praw += tk_wc.raw_total

        proj_row += 5

        write_data_rows(worksheet, proj_row, tk_wc.new_words, tk_wc.repetition, tk_wc.tm_100, tk_wc.tm_95_99, tk_wc.tm_85_94,\
                        tk_wc.tm_75_84, tk_wc.tm_50_74, tk_wc.tm_101, tk_wc.tm_102, tk_wc.raw_total)

    write_data_rows(worksheet, 8, pnew, prep, p100, p95_99, p85_94, p75_84, p50_74, p101, p102, praw)





