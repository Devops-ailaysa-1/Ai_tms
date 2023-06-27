from ai_workspace.models import Job
from datetime import datetime
from ai_tm.models import WordCountGeneral
import xml.etree.ElementTree as ET

import heapq
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Collection,
    Hashable,
    Iterable,
    Mapping,
    Sequence,
    overload,
)

from rapidfuzz._utils import ScorerFlag
from rapidfuzz.fuzz import WRatio, ratio
from rapidfuzz.utils import default_process
import rapidfuzz


def get_languages(proj):

    jobs = Job.objects.filter(project=proj.id)
    sl = jobs[0].source_language.language
    tl = ""
    for job in jobs:
        if job.target_language:
            tl += job.target_language.language
        if job != jobs[len(jobs) - 1]:
            tl += ", "

    return sl + " --> " + tl

def write_project_header(workbook, worksheet, proj):

    # Setting format properties
    align_format = workbook.add_format({
        'text_wrap': True, 'align': 'left',
            })

    align_left = workbook.add_format(
        {
            'align': 'left',
        }
    )
    worksheet.set_column('A:B', 20)
    worksheet.set_column('C:K', 15)

    worksheet.write('A1', 'Project analysis report', align_format)

    # Row 2
    worksheet.write('A2', 'Project:', align_format)
    worksheet.write('B2', proj.project_name, align_format)

    # Row 3
    worksheet.write('A3', 'Languages', align_format)
    worksheet.write('B3', get_languages(proj), align_left)

    # Row 4
    worksheet.write('A4', 'Date:', align_format)
    worksheet.write('B4', datetime.now().strftime("%d/%m/%Y"), align_format)

def write_common_rows(workbook, worksheet, row_no):

    # Setting formatting properties
    common_format = workbook.add_format(
        {
            'text_wrap': True,
            'align': 'center',
            'border': 1,
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

    tasks = proj.get_mtpe_tasks
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
            'border': 1,
        }
    )

    # Format for WWC
    wwc_format = workbook.add_format(
        {
            'text_wrap': True,
            'align': 'center',
            'border': 1,
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
        # 'text_wrap': True,
        'align': 'left',
    })

    tasks = proj.get_mtpe_tasks
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
    task_wcs = WordCountGeneral.objects.filter(project_id=proj.id).order_by('tasks','-id').distinct('tasks')
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





def tmx_read(files,job):
    from ai_tm.api_views import remove_tags
    sl = job.source_language_code
    tl = job.target_language_code
    source = []
    for file in files:
        tree = ET.parse(file.tmx_file.path)
        root=tree.getroot()
        for tag in root.iter('tu'):
            tt = None
            for node in tag.iter('tuv'):
                lang = node.get('{http://www.w3.org/XML/1998/namespace}lang')
                if lang.split('-')[0] == tl:
                    tt = True
            for node in tag.iter('tuv'):
                lang = node.get('{http://www.w3.org/XML/1998/namespace}lang')
                if tt:
                    if lang.split('-')[0] == sl:
                        for item in node.iter('seg'):
                            text =  (''.join(item.itertext()))
                            if text!=None:
                                source.append(remove_tags(text))
    return source



def tmx_read_with_target(files,job):
    from ai_tm.api_views import remove_tags
    sl = job.source_language_code
    tl = job.target_language_code
    tm_lists = []
    out = None
    source = None
    for file in files:
        tree = ET.parse(file.tmx_file.path)
        root=tree.getroot()
        for tag in root.iter('tu'):
            tt = None
            for node in tag.iter('tuv'):
                lang = node.get('{http://www.w3.org/XML/1998/namespace}lang')
                if lang.split('-')[0] == tl:
                    tt = True
            for node in tag.iter('tuv'):
                lang = node.get('{http://www.w3.org/XML/1998/namespace}lang')
                if tt:
                    if lang.split('-')[0] == sl:
                        for item in node.iter('seg'):
                            text =  (''.join(item.itertext()))
                            source = remove_tags(text)
                    if lang.split('-')[0] == tl:
                        for item in node.iter('seg'):
                            text =  (''.join(item.itertext()))
                            target = remove_tags(text)
                        if source:
                            out = {'source':source,'target':target}
            if out:
                tm_lists.append(out)
    return tm_lists





############################From RapidFuzz###########################################

def _get_scorer_flags_py(scorer: Any, kwargs: dict[str, Any]) -> tuple[int, int]:
    params = getattr(scorer, "_RF_ScorerPy", None)
    if params is not None:
        flags = params["get_scorer_flags"](**kwargs)
        return (flags["worst_score"], flags["optimal_score"])
    return (0, 100)

def extract_iter(
    query: Sequence[Hashable] | None,
    choices: Iterable[Sequence[Hashable] | None]
    | Mapping[Any, Sequence[Hashable] | None],
    *,
    scorer: Callable[..., int | float] = WRatio,
    processor: Callable[..., Sequence[Hashable]] | None | bool = default_process,
    score_cutoff: int | float | None = None,
    score_hint: int | float | None = None,
    **kwargs: Any,
) ->Iterable[tuple[Sequence[Hashable], int | float, Any]]:
    worst_score, optimal_score = _get_scorer_flags_py(scorer, kwargs)
    lowest_score_worst = optimal_score > worst_score

    if query is None:
        return

    if processor is True:
        processor = default_process
    elif processor is False:
        processor = None

    if score_cutoff is None:
        score_cutoff = worst_score

    # preprocess the query
    if processor is not None:
        query = processor(query)

    choices_iter: Iterable[tuple[Any, Sequence[Hashable] | None]]
    choices_iter = choices.items() if hasattr(choices, "items") else enumerate(choices)  # type: ignore[union-attr]
    for key, choice in choices_iter:
        if choice is None:
            continue

        if processor is None:
            score = scorer(
                query, choice.get('source'), processor=None, score_cutoff=score_cutoff, **kwargs
            )
        else:
            score = scorer(
                query,
                processor(choice.get('source')),
                processor=None,
                score_cutoff=score_cutoff,
                **kwargs,
            )

        if lowest_score_worst:
            if score >= score_cutoff:
                yield (choice, score, key)
        else:
            if score <= score_cutoff:
                yield (choice, score, key)



def tm_fetch_extract(
    query: Sequence[Hashable] | None,
    choices: Collection[Sequence[Hashable] | None]
    | Mapping[Any, Sequence[Hashable] | None],
    *,
    scorer: Callable[..., int | float] = WRatio,
    processor: Callable[..., Sequence[Hashable]] | None | bool = default_process,
    limit: int | None = 5,
    score_cutoff: int | float | None = None,
    score_hint: int | float | None = None,
    **kwargs: Any,
) ->list[tuple[Sequence[Hashable], int | float, Any]]:
    worst_score, optimal_score = _get_scorer_flags_py(scorer, kwargs)
    lowest_score_worst = optimal_score > worst_score

    if limit is None:
        limit = len(choices)

    result_iter = extract_iter(
        query, choices, processor=processor, scorer=scorer, score_cutoff=score_cutoff, **kwargs
    )
    if lowest_score_worst:
        return heapq.nlargest(limit, result_iter, key=lambda i: i[1])
    return heapq.nsmallest(limit, result_iter, key=lambda i: i[1])








# from ai_workspace.models import Job
# from datetime import datetime
# from ai_tm.models import WordCountGeneral,CharCountGeneral
# import xml.etree.ElementTree as ET

# import heapq
# from typing import (
#     TYPE_CHECKING,
#     Any,
#     Callable,
#     Collection,
#     Hashable,
#     Iterable,
#     Mapping,
#     Sequence,
#     overload,
# )

# from rapidfuzz._utils import ScorerFlag
# from rapidfuzz.fuzz import WRatio, ratio
# from rapidfuzz.utils import default_process
# import rapidfuzz


# def get_languages(proj):

#     jobs = Job.objects.filter(project=proj.id)
#     sl = jobs[0].source_language.language
#     tl = ""
#     for job in jobs:
#         if job.target_language:
#             tl += job.target_language.language
#         if job != jobs[len(jobs) - 1]:
#             tl += ", "

#     return sl + " --> " + tl

# def write_project_header(workbook, worksheet, proj):

#     # Setting format properties
#     align_format = workbook.add_format({
#         'text_wrap': True, 'align': 'left',
#             })

#     align_left = workbook.add_format(
#         {
#             'align': 'left',
#         }
#     )
#     worksheet.set_column('A:C', 20)
#     worksheet.set_column('D:L', 15)

#     worksheet.write('A1', 'Project analysis report', align_format)

#     # Row 2
#     worksheet.write('A2', 'Project:', align_format)
#     worksheet.write('B2', proj.project_name, align_format)

#     # Row 3
#     worksheet.write('A3', 'Languages', align_format)
#     worksheet.write('B3', get_languages(proj), align_left)

#     # Row 4
#     worksheet.write('A4', 'Date:', align_format)
#     worksheet.write('B4', datetime.now().strftime("%d/%m/%Y"), align_format)

# def write_common_rows(workbook, worksheet, row_no):

#     # Setting formatting properties
#     common_format = workbook.add_format(
#         {
#             'text_wrap': True,
#             'align': 'center',
#             'border': 1,
#         }
#     )

#     # Writing first row
#     worksheet.write(f'A{row_no}', "", common_format)
#     worksheet.write(f'B{row_no}', "Total", common_format)
#     worksheet.write(f'C{row_no}', "Weighted", common_format)
#     worksheet.write(f'D{row_no}', "New", common_format)
#     worksheet.write(f'E{row_no}', "Repetition", common_format)
#     worksheet.write(f'F{row_no}', "50-74%", common_format)
#     worksheet.write(f'G{row_no}', "75-84%", common_format)
#     worksheet.write(f'H{row_no}', "85-94%", common_format)
#     worksheet.write(f'I{row_no}', "95-99%", common_format)
#     worksheet.write(f'J{row_no}', "100%", common_format)
#     worksheet.write(f'K{row_no}', "101%", common_format)
#     worksheet.write(f'L{row_no}', "102%", common_format)

#     # Writing second row
#     worksheet.write(f'A{row_no + 1}', "", common_format)
#     worksheet.write(f'B{row_no + 1}', "", common_format)
#     worksheet.write(f'C{row_no + 1}', "Payable rate", common_format)
#     worksheet.write(f'D{row_no + 1}', "100%", common_format)
#     worksheet.write(f'E{row_no + 1}', "30%", common_format)
#     worksheet.write(f'F{row_no + 1}', "100%", common_format)
#     worksheet.write(f'G{row_no + 1}', "60%", common_format)
#     worksheet.write(f'H{row_no + 1}', "60%", common_format)
#     worksheet.write(f'I{row_no + 1}', "60%", common_format)
#     worksheet.write(f'J{row_no + 1}', "30%", common_format)
#     worksheet.write(f'K{row_no + 1}', "30%", common_format)
#     worksheet.write(f'L{row_no + 1}', "30%", common_format)



# def write_commons(workbook, worksheet, proj):

#     # For project
#     proj_row = 6
#     write_common_rows(workbook, worksheet, proj_row)

#     tasks = proj.get_mtpe_tasks
#     for task in tasks:
#         proj_row += 6
#         write_common_rows(workbook, worksheet, proj_row)

# def write_data_rows(workbook, worksheet, row_no, new, rep, c100, \
#                        c95_99, c85_94, c75_84, c50_74, c101, c102, raw):

#     # Setting format properties
#     data_format = workbook.add_format(
#         {
#             'text_wrap': True,
#             'align': 'center',
#             'border': 1,
#         }
#     )

#     # Format for WWC
#     wwc_format = workbook.add_format(
#         {
#             'text_wrap': True,
#             'align': 'center',
#             'border': 1,
#             'bold': True,
#         }
#     )


#     wwc = round(new + (0.3 * rep) + c50_74 + (0.6 * c75_84) + (0.6 * c85_94) + (0.6 * c95_99) + \
#                   (0.3 * c100) + (0.3 * c101) + (0.3 * c102))

#     worksheet.write(f'B{row_no}',raw, data_format)
#     worksheet.write(f'C{row_no}', wwc, wwc_format)
#     worksheet.write(f'D{row_no}', new, data_format)
#     worksheet.write(f'E{row_no}', rep, data_format)
#     worksheet.write(f'F{row_no}', c50_74, data_format)
#     worksheet.write(f'G{row_no}', c75_84, data_format)
#     worksheet.write(f'H{row_no}', c85_94, data_format)
#     worksheet.write(f'I{row_no}', c95_99, data_format)
#     worksheet.write(f'J{row_no}', c100, data_format)
#     worksheet.write(f'K{row_no}', c101, data_format)
#     worksheet.write(f'L{row_no}', c102, data_format)

# def write_task_details(workbook, worksheet, proj, proj_row):
#     # Setting format properties
#     align_format = workbook.add_format({
#         # 'text_wrap': True,
#         'align': 'left',
#     })

#     tasks = proj.get_mtpe_tasks
#     for task in tasks:
#         if task == tasks[0]:
#             proj_row += 3
#         else:
#             proj_row += 6
#         worksheet.write(f'A{proj_row}', "Task: ", align_format)
#         worksheet.write(f'B{proj_row}', task.file.filename + ", " + task.job.source_language.language \
#                         + " --> " + task.job.target_language.language, align_format)
# def write_data(workbook, worksheet, proj):

#     common_format = workbook.add_format(
#         {
#             'text_wrap': True,
#             'align': 'center',
#             'border': 1,
#         }
#     )

#     # Initializing word count values
#     pnew, prep, p100, p95_99, p85_94, p75_84, p50_74, p101, p102, praw = \
#     0, 0, 0, 0, 0, 0, 0, 0, 0, 0

#     proj_row = 8

#     write_task_details(workbook, worksheet, proj, proj_row)

#     # Adding word count from each task
#     worksheet.write(f'A{proj_row}', "Word",common_format)
#     task_wcs = WordCountGeneral.objects.filter(project_id=proj.id).order_by('tasks','-id').distinct('tasks')
#     for tk_wc in task_wcs:
#         pnew += tk_wc.new_words
#         prep += tk_wc.repetition
#         p100 += tk_wc.tm_100
#         p95_99 += tk_wc.tm_95_99
#         p85_94 += tk_wc.tm_85_94
#         p75_84 += tk_wc.tm_75_84
#         p50_74 += tk_wc.tm_50_74
#         p101 += tk_wc.tm_101
#         p102 += tk_wc.tm_102
#         praw += tk_wc.raw_total

#         proj_row += 6
#         worksheet.write(f'A{proj_row}', "Word",common_format)
#         write_data_rows(workbook, worksheet, proj_row, tk_wc.new_words, tk_wc.repetition, tk_wc.tm_100, tk_wc.tm_95_99, tk_wc.tm_85_94,\
#                         tk_wc.tm_75_84, tk_wc.tm_50_74, tk_wc.tm_101, tk_wc.tm_102, tk_wc.raw_total)
    
#     write_data_rows(workbook, worksheet, 8, pnew, prep, p100, p95_99, p85_94, p75_84, p50_74, p101, p102, praw)

#     proj_row =9
#     worksheet.write(f'A{proj_row}', "Char",common_format)
#     task_ccs=CharCountGeneral.objects.filter(project_id=proj.id).order_by('tasks','-id').distinct('tasks')
#     for tk_cc in task_ccs:
#         pnew += tk_cc.new_words
#         prep += tk_cc.repetition
#         p100 += tk_cc.tm_100
#         p95_99 += tk_cc.tm_95_99
#         p85_94 += tk_cc.tm_85_94
#         p75_84 += tk_cc.tm_75_84
#         p50_74 += tk_cc.tm_50_74
#         p101 += tk_cc.tm_101
#         p102 += tk_cc.tm_102
#         praw += tk_cc.raw_total

#         proj_row += 6
#         worksheet.write(f'A{proj_row}', "Char",common_format)
#         write_data_rows(workbook, worksheet, proj_row, tk_cc.new_words, tk_cc.repetition, tk_cc.tm_100, tk_cc.tm_95_99, tk_cc.tm_85_94,\
#                         tk_cc.tm_75_84, tk_cc.tm_50_74, tk_cc.tm_101, tk_cc.tm_102, tk_cc.raw_total)

#     write_data_rows(workbook, worksheet, 9, pnew, prep, p100, p95_99, p85_94, p75_84, p50_74, p101, p102, praw)





# def tmx_read(files,job):
#     from ai_tm.api_views import remove_tags
#     sl = job.source_language_code
#     tl = job.target_language_code
#     source = []
#     for file in files:
#         tree = ET.parse(file.tmx_file.path)
#         root=tree.getroot()
#         for tag in root.iter('tu'):
#             tt = None
#             for node in tag.iter('tuv'):
#                 lang = node.get('{http://www.w3.org/XML/1998/namespace}lang')
#                 if lang.split('-')[0] == tl:
#                     tt = True
#             for node in tag.iter('tuv'):
#                 lang = node.get('{http://www.w3.org/XML/1998/namespace}lang')
#                 if tt:
#                     if lang.split('-')[0] == sl:
#                         for item in node.iter('seg'):
#                             text =  (''.join(item.itertext()))
#                             if text!=None:
#                                 source.append(remove_tags(text))
#     return source



# def tmx_read_with_target(files,job):
#     from ai_tm.api_views import remove_tags
#     sl = job.source_language_code
#     tl = job.target_language_code
#     tm_lists = []
#     out = None
#     source = None
#     for file in files:
#         tree = ET.parse(file.tmx_file.path)
#         root=tree.getroot()
#         for tag in root.iter('tu'):
#             tt = None
#             for node in tag.iter('tuv'):
#                 lang = node.get('{http://www.w3.org/XML/1998/namespace}lang')
#                 if lang.split('-')[0] == tl:
#                     tt = True
#             for node in tag.iter('tuv'):
#                 lang = node.get('{http://www.w3.org/XML/1998/namespace}lang')
#                 if tt:
#                     if lang.split('-')[0] == sl:
#                         for item in node.iter('seg'):
#                             text =  (''.join(item.itertext()))
#                             source = remove_tags(text)
#                     if lang.split('-')[0] == tl:
#                         for item in node.iter('seg'):
#                             text =  (''.join(item.itertext()))
#                             target = remove_tags(text)
#                         if source:
#                             out = {'source':source,'target':target}
#             if out:
#                 tm_lists.append(out)
#     return tm_lists





# ############################From RapidFuzz###########################################

# def _get_scorer_flags_py(scorer: Any, kwargs: dict[str, Any]) -> tuple[int, int]:
#     params = getattr(scorer, "_RF_ScorerPy", None)
#     if params is not None:
#         flags = params["get_scorer_flags"](**kwargs)
#         return (flags["worst_score"], flags["optimal_score"])
#     return (0, 100)

# def extract_iter(
#     query: Sequence[Hashable] | None,
#     choices: Iterable[Sequence[Hashable] | None]
#     | Mapping[Any, Sequence[Hashable] | None],
#     *,
#     scorer: Callable[..., int | float] = WRatio,
#     processor: Callable[..., Sequence[Hashable]] | None | bool = default_process,
#     score_cutoff: int | float | None = None,
#     score_hint: int | float | None = None,
#     **kwargs: Any,
# ) ->Iterable[tuple[Sequence[Hashable], int | float, Any]]:
#     worst_score, optimal_score = _get_scorer_flags_py(scorer, kwargs)
#     lowest_score_worst = optimal_score > worst_score

#     if query is None:
#         return

#     if processor is True:
#         processor = default_process
#     elif processor is False:
#         processor = None

#     if score_cutoff is None:
#         score_cutoff = worst_score

#     # preprocess the query
#     if processor is not None:
#         query = processor(query)

#     choices_iter: Iterable[tuple[Any, Sequence[Hashable] | None]]
#     choices_iter = choices.items() if hasattr(choices, "items") else enumerate(choices)  # type: ignore[union-attr]
#     for key, choice in choices_iter:
#         if choice is None:
#             continue

#         if processor is None:
#             score = scorer(
#                 query, choice.get('source'), processor=None, score_cutoff=score_cutoff, **kwargs
#             )
#         else:
#             score = scorer(
#                 query,
#                 processor(choice.get('source')),
#                 processor=None,
#                 score_cutoff=score_cutoff,
#                 **kwargs,
#             )

#         if lowest_score_worst:
#             if score >= score_cutoff:
#                 yield (choice, score, key)
#         else:
#             if score <= score_cutoff:
#                 yield (choice, score, key)



# def tm_fetch_extract(
#     query: Sequence[Hashable] | None,
#     choices: Collection[Sequence[Hashable] | None]
#     | Mapping[Any, Sequence[Hashable] | None],
#     *,
#     scorer: Callable[..., int | float] = WRatio,
#     processor: Callable[..., Sequence[Hashable]] | None | bool = default_process,
#     limit: int | None = 5,
#     score_cutoff: int | float | None = None,
#     score_hint: int | float | None = None,
#     **kwargs: Any,
# ) ->list[tuple[Sequence[Hashable], int | float, Any]]:
#     worst_score, optimal_score = _get_scorer_flags_py(scorer, kwargs)
#     lowest_score_worst = optimal_score > worst_score

#     if limit is None:
#         limit = len(choices)

#     result_iter = extract_iter(
#         query, choices, processor=processor, scorer=scorer, score_cutoff=score_cutoff, **kwargs
#     )
#     if lowest_score_worst:
#         return heapq.nlargest(limit, result_iter, key=lambda i: i[1])
#     return heapq.nsmallest(limit, result_iter, key=lambda i: i[1])
