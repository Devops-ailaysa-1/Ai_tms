
from .utils import set_ref_tags_to_runs, get_runs_and_ref_ids

def set_segment_tags_in_source_and_target(sender, instance, created, *args, **kwargs):
    print("signal created---->", created)
    if created:
        instance.tagged_source, _ ,instance.target_tags = (
            set_ref_tags_to_runs(instance.coded_source, get_runs_and_ref_ids(instance.
                coded_brace_pattern, instance.coded_ids_aslist))
        )
        instance.save()