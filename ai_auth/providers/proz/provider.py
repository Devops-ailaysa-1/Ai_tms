from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.account.models import EmailAddress


class ProzAccount(ProviderAccount):
    pass


class ProzProvider(OAuth2Provider):

    id = 'Proz'
    name = 'Proz'
    account_class = ProzAccount

    def extract_uid(self, data):
        return str(data['uuid'])

    def extract_common_fields(self, data):
        return dict(email=data['email'],
                    first_name=data['contact_info']['first_name'],
                    last_name=data['contact_info']['last_name'],)

    def get_default_scope(self):
        scope = ['public']
        return scope
    
    def get_auth_params(self, request, action):
        ret = super(ProzProvider, self).get_auth_params(request, action)
        # if action == AuthAction.REAUTHENTICATE:
        #     ret["prompt"] = "select_account consent"
        print("ret",ret)
        return ret

    
    def extract_email_addresses(self, data):
        ret = []
        email = data.get("email")
        if email and data.get("email_verified"):
            ret.append(EmailAddress(email=email, verified=True, primary=True))
        return ret


providers.registry.register(ProzProvider)