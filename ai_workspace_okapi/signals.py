
from .utils import set_ref_tags_to_runs, get_runs_and_ref_ids, get_translation
from django.apps import apps
from django.db.models import Q


def set_segment_tags_in_source_and_target(sender, instance, created, *args, **kwargs):

    if created:
        instance.tagged_source, _ ,instance.target_tags = (
            set_ref_tags_to_runs(instance.coded_source, get_runs_and_ref_ids(instance.
                coded_brace_pattern, instance.coded_ids_aslist))
        )

        instance.save()

def create_segment_controller(sender, instance, created, *args, **kwargs):
    if created:
        model = apps.get_model("ai_workspace_okapi.segmentcontroller")
        obj = model(base_segment_id=instance.id)
        obj.save()

        print("new segment controller created successfully!!!")


def translate_segments(sender, instance, created, *args, **kwargs):
    from ai_workspace.models import TaskAssign
    if created:
        task_assign_obj = TaskAssign.objects.filter(
            Q(task__document__document_text_unit_set__text_unit_segment_set=instance.id) &
            Q(step_id=1)).first()
        if task_assign_obj.pre_translate == True or task_assign_obj.task.job.project.pre_translate == True:
            target = get_translation(
                task_assign_obj.mt_engine_id,
                instance.source,
                instance.text_unit.document.source_language_code,
                instance.text_unit.document.target_language_code,
                user_id = instance.owner_pk
                )
            instance.target = target
            instance.save()
