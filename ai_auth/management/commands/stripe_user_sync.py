"""
sync_customer command.
"""
from django.core.management.base import BaseCommand

from ai_auth.models import AiUser
from djstripe.sync import sync_subscriber
from djstripe.models import Customer
from django.db.models import Q
from django.db.models import F


class Command(BaseCommand):
    """Sync user data with stripe Customer."""

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete outs-of-sync customer from local database',
        )

        parser.add_argument(
            '--all',
            action='store_true',
            help='Sync all subscribers',
        )
    def handle(self, *args, **options):
        """Call sync_subscriber on Subscribers without customers associated to them."""

        custs_outsync=Customer.objects.filter(~Q(subscriber__email=F('email')))
        custs_insync=Customer.objects.filter(Q(subscriber__email=F('email')))
        deleted_count=AiUser.objects.filter(email__icontains='deleted').count()


        if options['delete']:
            custs_outsync.delete()


        if options['all']:
            qs = AiUser.objects.filter(~Q(email__icontains='deleted')&~Q(email='AnonymousUser'))
        else:
            qs = AiUser.objects.filter(Q(djstripe_customers__isnull=True) & ~Q(email__icontains='deleted')&~Q(email='AnonymousUser'))


        print(f"Customer emails Out-Of-Sync:[{custs_outsync.count()}] In-Sync:[{custs_insync.count()}] ")

        count = 0
        total = qs.count()
        for subscriber in qs:
            count += 1
            perc = int(round(100 * (float(count) / float(total))))
            print(
                "[{0}/{1} {2}%] Syncing {3} [{4}]".format(
                    count, total, perc, subscriber.email, subscriber.pk
                )
            )
            sync_subscriber(subscriber)