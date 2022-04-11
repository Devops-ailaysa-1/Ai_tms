
from .utils import set_ref_tags_to_runs, get_runs_and_ref_ids
from django.apps import apps

def set_segment_tags_in_source_and_target(sender, instance, created, *args, **kwargs):

    if created:
        instance.tagged_source, _ ,instance.target_tags = (
            set_ref_tags_to_runs(instance.coded_source, get_runs_and_ref_ids(instance.
                coded_brace_pattern, instance.coded_ids_aslist))
        )
        # print("Tagged source ---> ", instance.tagged_source)
        # print("Target tags ---> ", instance.target_tags)
        instance.save()

def create_segment_controller(sender, instance, created, *args, **kwargs):
    if created:
        model = apps.get_model("ai_workspace_okapi.segmentcontroller")
        obj = model(base_segment_id=instance.id)
        obj.save()

        print("new segment controller created successfully!!!")

