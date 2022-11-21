from ai_workspace.models import Job
from datetime import datetime
from ai_tm.models import WordCountGeneral


def get_languages(proj):

    jobs = Job.objects.filter(project=proj.id)
    sl = jobs[0].source_language.language
    tl = ""
    for job in jobs:
        tl += job.target_language.language
        if job != jobs[len(jobs) - 1]:
            tl += ", "

    return sl + " --> " + tl

def write_project_header(workbook, worksheet, proj):

    # Setting format properties
    align_format = workbook.add_format({
        'text_wrap': True, 'align': 'left',
            })
    worksheet.set_column('A:K', 20)

    worksheet.write('A1', 'Project analysis report', align_format)

    # Row 2
    worksheet.write('A2', 'Project:', align_format)
    worksheet.write('B2', proj.project_name, align_format)

    # Row 3
    worksheet.write('A3', 'Languages', align_format)
    worksheet.write('B3', get_languages(proj), align_format)

    # Row 4
    worksheet.write('A4', 'Date:', align_format)
    worksheet.write('B4', datetime.now().strftime("%d/%m/%Y %H:%M:%S"), align_format)

def write_common_rows(workbook, worksheet, row_no):

    # Setting formatting properties
    common_format = workbook.add_format(
        {
            'text_wrap': True,
            'align': 'center',
            'border': 2,
        }
    )

    # Writing first row
    worksheet.write(f'A{row_no}', "Total", common_format)
    worksheet.write(f'B{row_no}', "Weighted", common_format)
    worksheet.write(f'C{row_no}', "New", common_format)
    worksheet.write(f'D{row_no}', "Repetition", common_format)
    worksheet.write(f'E{row_no}', "50-74%", common_format)
    worksheet.write(f'F{row_no}', "75-84%", common_format)
    worksheet.write(f'G{row_no}', "85-94%", common_format)
    worksheet.write(f'H{row_no}', "95-99%", common_format)
    worksheet.write(f'I{row_no}', "100%", common_format)
    worksheet.write(f'J{row_no}', "101%", common_format)
    worksheet.write(f'K{row_no}', "102%", common_format)

    # Writing second row
    worksheet.write(f'B{row_no + 1}', "Payable rate", common_format)
    worksheet.write(f'C{row_no + 1}', "100%", common_format)
    worksheet.write(f'D{row_no + 1}', "30%", common_format)
    worksheet.write(f'E{row_no + 1}', "100%", common_format)
    worksheet.write(f'F{row_no + 1}', "60%", common_format)
    worksheet.write(f'G{row_no + 1}', "60%", common_format)
    worksheet.write(f'H{row_no + 1}', "60%", common_format)
    worksheet.write(f'I{row_no + 1}', "30%", common_format)
    worksheet.write(f'J{row_no + 1}', "30%", common_format)
    worksheet.write(f'K{row_no + 1}', "30%", common_format)

def write_commons(workbook, worksheet, proj):

    # For project
    proj_row = 6
    write_common_rows(workbook, worksheet, proj_row)

    tasks = proj.get_tasks
    for task in tasks:
        proj_row += 5
        write_common_rows(workbook, worksheet, proj_row)

def write_data_rows(workbook, worksheet, row_no, new, rep, c100, \
                       c95_99, c85_94, c75_84, c50_74, c101, c102, raw):

    # Setting format properties
    data_format = workbook.add_format(
        {
            'text_wrap': True,
            'align': 'center',
            'border': 2,
        }
    )

    # Format for WWC
    wwc_format = workbook.add_format(
        {
            'text_wrap': True,
            'align': 'center',
            'border': 2,
            'bold': True,
        }
    )


    wwc = round(new + (0.3 * rep) + c50_74 + (0.6 * c75_84) + (0.6 * c85_94) + (0.6 * c95_99) + \
                  (0.3 * c100) + (0.3 * c101) + (0.3 * c102))

    worksheet.write(f'A{row_no}',raw, data_format)
    worksheet.write(f'B{row_no}', wwc, wwc_format)
    worksheet.write(f'C{row_no}', new, data_format)
    worksheet.write(f'D{row_no}', rep, data_format)
    worksheet.write(f'E{row_no}', c50_74, data_format)
    worksheet.write(f'F{row_no}', c75_84, data_format)
    worksheet.write(f'G{row_no}', c85_94, data_format)
    worksheet.write(f'H{row_no}', c95_99, data_format)
    worksheet.write(f'I{row_no}', c100, data_format)
    worksheet.write(f'J{row_no}', c101, data_format)
    worksheet.write(f'K{row_no}', c102, data_format)

def write_task_details(workbook, worksheet, proj, proj_row):
    # Setting format properties
    align_format = workbook.add_format({
        'text_wrap': True, 'align': 'left',
    })

    tasks = proj.get_tasks
    for task in tasks:
        if task == tasks[0]:
            proj_row += 2
        else:
            proj_row += 5
        worksheet.write(f'A{proj_row}', "Task: ", align_format)
        worksheet.write(f'B{proj_row}', task.file.filename + ", " + task.job.source_language.language \
                        + " --> " + task.job.target_language.language, align_format)
def write_data(workbook, worksheet, proj):

    # Initializing word count values
    pnew, prep, p100, p95_99, p85_94, p75_84, p50_74, p101, p102, praw = \
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0

    proj_row = 8

    write_task_details(workbook, worksheet, proj, proj_row)

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

        write_data_rows(workbook, worksheet, proj_row, tk_wc.new_words, tk_wc.repetition, tk_wc.tm_100, tk_wc.tm_95_99, tk_wc.tm_85_94,\
                        tk_wc.tm_75_84, tk_wc.tm_50_74, tk_wc.tm_101, tk_wc.tm_102, tk_wc.raw_total)

    write_data_rows(workbook, worksheet, 8, pnew, prep, p100, p95_99, p85_94, p75_84, p50_74, p101, p102, praw)





