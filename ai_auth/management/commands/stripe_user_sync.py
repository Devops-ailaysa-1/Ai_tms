"""
sync_customer command.
"""
from django.core.management.base import BaseCommand

from ai_auth.models import AiUser
from djstripe.sync import sync_subscriber
from djstripe.models import Customer
from django.db.models import Q
from django.db.models import F
from django.db.models import Count
import logging
logger = logging.getLogger('django')

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

        parser.add_argument(
            '--sync',
            action='store_true',
            help='Sync subscribers(excl. deleted)',
        )

    def handle(self, *args, **options):
        """Call sync_subscriber on Subscribers without customers associated to them."""

        custs_outsync=Customer.objects.filter(~Q(subscriber__email=F('email')))
        custs_insync=Customer.objects.filter(Q(subscriber__email=F('email')))
        deleted_count=AiUser.objects.filter(email__icontains='deleted').count()
        user_null_cust = []
        user_multi_cust=[]

        for count,email,id in AiUser.objects.annotate(num_count =Count('djstripe_customers')).values_list('num_count','email','id'):
            if count> 1:
                user_multi_cust.append(id)
            elif count ==0:
                user_null_cust.append(id)


        if options['delete']:
            custs_outsync.delete()


        if options['all']:
            qs = AiUser.objects.filter(~Q(email__icontains='deleted')&~Q(email='AnonymousUser'))
        else:
            qs = AiUser.objects.filter(Q(djstripe_customers__isnull=True) & ~Q(email__icontains='deleted')&~Q(email='AnonymousUser'))

        logger.info(f"AiUser None Customer : [{len(user_null_cust)}]  Multiple Customer: [{len(user_multi_cust)}]")
        logger.info(f"Stripe Customer emails Out-Of-Sync:[{custs_outsync.count()}] In-Sync:[{custs_insync.count()}] ")

        if options['sync']:
            count = 0
            total = qs.count()
            for subscriber in qs:
                count += 1
                perc = int(round(100 * (float(count) / float(total))))
                logger.info(
                    "[{0}/{1} {2}%] Syncing {3} [{4}]".format(
                        count, total, perc, subscriber.email, subscriber.pk
                    )
                )
                sync_subscriber(subscriber)