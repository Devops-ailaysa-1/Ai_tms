
import logging
logger = logging.getLogger('django')


def text_gen_credit_deduct(sender, instance, *args, **kwargs):
    from ai_openai import models as openai_models
    from ai_workspace.api_views import UpdateTaskCreditStatus  
    try:
        to_deduct=openai_models.TextgeneratedCreditDeduction.objects.get(user=instance.user)
        if to_deduct.credit_to_deduce != 0 :
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.user, to_deduct.credit_to_deduce)
            if status_code != 200:
                logger.error("UserCredit Detection failed - UID:",instance.user.uid)
            else:
                to_deduct.credit_to_deduce = 0
                to_deduct.save()
                logger.info(f"Credits Successfully detected for - UID : {instance.user.uid},Credit Deducted : {to_deduct.to_deduct.credit_to_deduce}")
    except openai_models.TextgeneratedCreditDeduction.DoesNotExist:
        pass
    except BaseException as e:
        logger.error(f"UserCredit Detection failed - UID:{instance.user.uid},ERROR:{str(e)}")

    
