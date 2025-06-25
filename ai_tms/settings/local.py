"""
Django settings for ai_tms project.

For Local Environment
"""
from .base import *
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
# import newrelic.agent
# from newrelic.agent import NewRelicContextFormatter
# newrelic.agent.initialize('newrelic.ini')
from dotenv import load_dotenv
load_dotenv(".env.local")


SECRET_KEY = os.getenv("django_secret_key")
DEBUG = (True if os.getenv( "Debug" ) == 'True' else False)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split()


### CORS 

CORS_ORIGIN_ALLOW_ALL= False
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split()
CORS_ORIGIN_WHITELIST = os.getenv("CORS_ORIGIN_WHITELIST", "").split()
CORS_ALLOW_CREDENTIALS = (True if os.getenv( "CORS_ALLOW_CREDENTIALS" ) == 'True' else False)



CSRF_TRUSTED_ORIGINS = [
 "http://localhost:3000",  "http://localhost:4200"
]


INSTALLED_APPS += [
    'dbbackup',
]


# Database
try:
    from ai_tms.local_settings import DATABASES
except Exception as e:
    DATABASES={
        'default':{
            'ENGINE':'django.db.backends.postgresql_psycopg2',
            'DISABLE_SERVER_SIDE_CURSORS': True,
            'NAME':os.getenv( "psql_database" ),
            'USER':os.getenv( "psql_user" ),
            'PASSWORD':os.getenv( "psql_password" ),
            'HOST':os.getenv( "psql_host" ),
            'PORT':os.getenv( "psql_port" ),
        }
    }


# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv( "EMAIL_HOST" )
EMAIL_PORT = int(os.getenv( "EMAIL_PORT" )) if os.getenv("EMAIL_PORT") else None
EMAIL_USE_TLS = (True if os.getenv( "EMAIL_TLS" ) == 'True' else False)
EMAIL_HOST_USER = os.getenv( "EMAIL_HOST_USER" )
EMAIL_HOST_PASSWORD = os.getenv( "EMAIL_HOST_PASSWORD" )
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


### DRF settings

REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
                'rest_framework.throttling.AnonRateThrottle',
                'rest_framework.throttling.UserRateThrottle'
                ]

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
                        'anon': '500/minute',
                        'user': '1500/minute'}



### Allauth Account settings
ACCOUNT_EMAIL_SUBJECT_PREFIX = ''
DEFAULT_FROM_EMAIL =os.getenv("DEFAULT_FROM_EMAIL")
CEO_EMAIL = os.getenv("CEO_EMAIL")
END_POINT = os.getenv('END_POINT')
ACCOUNT_AUTHENTICATION_METHOD = os.getenv("ACCOUNT_AUTHENTICATION_METHOD")
ACCOUNT_USERNAME_REQUIRED = (True if os.getenv( "ACCOUNT_USERNAME_REQUIRED" ) == 'True' else False)
ACCOUNT_EMAIL_REQUIRED = (True if os.getenv( "ACCOUNT_EMAIL_REQUIRED" ) == 'True' else False)
ACCOUNT_UNIQUE_EMAIL = (True if os.getenv( "ACCOUNT_UNIQUE_EMAIL" ) == 'True' else False)
ACCOUNT_USER_MODEL_USERNAME_FIELD = os.getenv("ACCOUNT_USER_MODEL_USERNAME_FIELD" )
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION")
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1


### SOCIAL ACCOUNT
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_QUERY_EMAIL = True
GOOGLE_CALLBACK_URL = os.getenv('GOOGLE_CALLBACK_URL')
PROZ_CALLBACK_URL = os.getenv('PROZ_CALLBACK_URL')




### Django Channel

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
             "hosts": [os.getenv("REDIS_CHANNEL_HOST")],

        },
    },
}

### CACHEOPS Setting

CACHEOPS_REDIS = os.getenv("CACHEOPS_REDIS_HOST")

CACHEOPS_ENABLED = True

CACHEOPS_DEGRADE_ON_FAILURE = True 

CACHEOPS_REDIS = os.getenv("CACHEOPS_REDIS_HOST")

CACHEOPS_DEFAULTS = {
    'timeout': 60 * 60,  # Default cache timeout (1 hour)
}

CACHEOPS = {

    'ai_staff.*': {'ops': 'all', 'timeout': 60*60},

}


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv("CACHE_REDIS_URL"),  
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'KEY_PREFIX': '',  
        },
        'TIMEOUT': 3600,  # Set the default cache timeout to 1 hour (3600 seconds)
    }
}



### CELERY
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL")
CELERY_ACCEPT_CONTENT =os.getenv("CELERY_ACCEPT_CONTENT", "").split()
CELERY_RESULT_SERIALIZER = os.getenv("CELERY_RESULT_SERIALIZER")
CELERY_TASK_SERIALIZER = os.getenv("CELERY_TASK_SERIALIZER")
CELERY_TASK_TRACK_STARTED = True
CELERY_IGNORE_RESULT = False





### Django Backup

DBBACKUP_STORAGE ='storages.backends.s3boto3.S3Boto3Storage'
DBBACKUP_STORAGE_OPTIONS = {
    'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
    'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
    'bucket_name': os.getenv('AWS_STORAGE_BUCKET_NAME'),
    'endpoint_url': 'https://ams3.digitaloceanspaces.com',
    'default_acl': 'private',
    'location': os.getenv('MEDIA_BACKUP_LOCATION')

}

############
### URLS
############

PASSWORD_RESET_URL = os.getenv("PASSWORD_RESET_URL")
CLIENT_BASE_URL = os.getenv("CLIENT_BASE_URL")
SIGNUP_CONFIRM_URL = os.getenv("SIGNUP_CONFIRM_URL")
TRANSEDITOR_BASE_URL = os.getenv("TRANSEDITOR_BASE_URL")
EXTERNAL_MEMBER_ACCEPT_URL = os.getenv("EXTERNAL_MEMBER_ACCEPT_URL")
VENDOR_RENEWAL_ACCEPT_URL = os.getenv("VENDOR_RENEWAL_ACCEPT_URL")
APPLICATION_URL = os.getenv("APPLICATION_URL")
USERPORTAL_URL = os.getenv("USERPORTAL_URL")
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'




#### Storage

USE_SPACES = (True if os.getenv( "USE_SPACES" ) == 'True' else False)

if USE_SPACES:
    # settings
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_ENDPOINT_URL = 'https://ams3.digitaloceanspaces.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    # static settings
    AWS_LOCATION = 'static'
    STATIC_URL = f'https://{AWS_S3_ENDPOINT_URL}/{AWS_LOCATION}/'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    # public media settings
    PUBLIC_MEDIA_LOCATION = 'media'
    MEDIA_URL = f'https://{AWS_S3_ENDPOINT_URL}/{PUBLIC_MEDIA_LOCATION}/'
    DEFAULT_FILE_STORAGE = 'ai_auth.storage_backends.PrivateMediaStorage'
else:
    STATIC_URL = '/static/'
    STATIC_ROOT =  os.path.join(BASE_DIR, 'staticfiles')
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
        # os.path.join(BASE_DIR, 'ai_canvas/static'),

    ]
    MEDIA_ROOT =  os.path.join(BASE_DIR, 'mediafiles')
    MEDIA_URL = '/media/'




LOGGING = {
    'version' : 1,
    'disable_existing_loggers' : False,

    'formatters' : {
        'dev_formatter' : {
            'format' : '{levelname} {asctime} {pathname} {message}',
            'style' : '{',
        },
        # 'fluent_fmt':{
        # '()': 'fluent.handler.FluentRecordFormatter',
        # 'format':{
        #   'level': '%(levelname)s',
        #   'hostname': '%(hostname)s',
        #   'where': '%(module)s.%(funcName)s',
        # }}
    },

    'loggers' : {
        # 'django' : {
        #     'handlers' : ['file',],
        #     'level' : os.environ.get("LOGGING_LEVEL"), # to be received from .env file
        #     'propogate' : True,
        # },

        'django' : {
            'handlers' : ['file_prod'],
            'level' : os.environ.get("LOGGING_LEVEL_PROD"), # to be received from .env file
            'propogate' : True,
        },
        # 'app.debug': {
        #     'handlers': ['fluentdebug'],
        #     'level': 'DEBUG',
        #     'propagate': True,
        # },
        # 'app.info': {
        #     'handlers': ['fluentinfo'],
        #     'level': 'INFO',
        #     'propagate': True,
        # },
        #'': {
        #    'handlers': ['console' ],
        #    'level': 'INFO',
        #    'propagate': False,
        #},
        # 'django.request': {
        #     'handlers': ['fluentdebug'],
        #     'level': 'DEBUG',
        #     'propagate': True,
        # },
    },

    'handlers' : {
        #'console':{
        #    'class' : 'logging.StreamHandler',
        #    'level': 'INFO',
        #    'formatter': 'dev_formatter',
        #    'stream': 'ext://sys.stdout',
        #},
        'file' : {
            'level' : os.environ.get("LOGGING_LEVEL"), # to be received from .env file
            'class' : 'logging.FileHandler',
            'filename' : '{}.log'.format(os.environ.get("LOG_FILE_NAME")),  #filename to be received from .env
            'formatter' : 'dev_formatter',
        },

       'file_prod' : {
            'level' : os.environ.get("LOGGING_LEVEL_PROD"), # to be received from .env file
            'class' : 'logging.FileHandler',
            'filename' : '{}.log'.format(os.environ.get("LOG_FILE_NAME_PROD")),  #filename to be received from .env
            'formatter' : 'dev_formatter',
        },
    #     'fluentinfo':{
    #         'level':'INFO',
    #         'class':'fluent.handler.FluentHandler',
    #         'formatter': 'fluent_fmt',
    #         'tag':'django.info',
    #         'host':'fluentd',
    #         'port':24224,
    #         # 'timeout':3.0,
    #         # 'verbose': False
    #         },
    #    'fluentdebug':{
    #         'level':'DEBUG',
    #         'class':'fluent.handler.FluentHandler',
    #         'formatter': 'fluent_fmt',
    #         'tag':'django.debug',
    #         'host':'fluentd',
    #         'port':24224,
    #         # 'timeout':3.0,
    #         # 'verbose': True
    #     },

        # 'mail_admins' : {
        #     'level' : 'ERROR',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'formatter' : 'dev_formatter',
        # }
    },


}



# SILKY_PYTHON_PROFILER = True

# SILKY_DYNAMIC_PROFILING = [{
#     'module': 'ai_staff.api_views',
#     'function': 'CurrenciesView.get'
# }]


RUST_BACKTRACE=1


# SILKY_AUTHENTICATION = True  # User must login
# SILKY_AUTHORISATION = True  # User must have permissions

# INTERNAL_IPS = [
#     # ...
#    ALLOWED_HOSTS
#     # ...
# ]

# def show_toolbar(request):
#     return True
# DEBUG_TOOLBAR_CONFIG = {
#     "SHOW_TOOLBAR_CALLBACK" : show_toolbar,
# }

#STRIPE_API_HOST = "http://localhost:12111"  


#### ML Related

GOOGLE_APPLICATION_CREDENTIALS_OCR = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_OCR")
CONVERTIO_API = os.getenv("convertio_api")
OPENAI_API_KEY =  os.getenv("OPENAI_API_KEY")
OPENAI_MODEL  = os.getenv("OPENAI_MODEL")
EMBEDDING_MODEL=os.getenv("EMBEDDING_MODEL")
OPEN_AI_GPT_MODEL = os.getenv("OPEN_AI_GPT_MODEL")
OPEN_AI_GPT_MODEL_REPLACE = os.getenv("OPEN_AI_GPT_MODEL_REPLACE")
OPEN_AI_GPT_MODEL_CHAT = os.getenv("OPEN_AI_GPT_MODEL_CHAT")
OPENAI_EDIT_MODEL = os.getenv("OPENAI_EDIT_MODEL")
ADAPTIVE_LLM_MODEL = os.getenv("ADAPTIVE_LLM_MODEL")


#### FEDERAL 

HTML_MIME_FEDARAL = os.getenv("HTML_MIME_FEDARAL")
CMS_SESSION_ID = os.getenv("CMS-SESSION-ID")
FEDERAL_KEY = os.getenv("FEDERAL-KEY")
TRANSLATABLE_KEYS_FEDERAL = os.getenv("TRANSLATABLE_KEYS_FEDARAL")
STAGING_FEDERAL_KEY = os.getenv("STAGING-FEDERAL-KEY")
FEDERAL_URL = os.getenv("FEDERAL_URL")
KARNATAKA_FEDERAL_URL = os.getenv("KARNATAKA_FEDERAL_URL")
TELUGANA_FEDERAL_URL = os.getenv("TELUGANA_FEDERAL_URL")
HINDI_FEDERAL_URL = os.getenv("HINDI_FEDERAL_URL")
STAGINGFEDERAL_URL = os.getenv("STAGINGFEDERAL_URL")
TELANGANA_FEDERAL_KEY = os.getenv("TELUGANA-FEDARAL-KEY")
KARNATAKA_FEDERAL_KEY = os.getenv("KARNATAKA-FEDARAL-KEY")
HINDI_FEDERAL_KEY = os.getenv("HINDI-FEDERAL-KEY")


#### STRIPE

STRIPE_LIVE_SECRET_KEY = os.environ.get("STRIPE_LIVE_SECRET_KEY")
STRIPE_TEST_SECRET_KEY = os.getenv( "STRIPE_TEST_SECRET_KEY" )
STRIPE_LIVE_MODE = (True if os.getenv( "STRIPE_LIVE_MODE" ) == 'True' else False)  # Change to True in production
DJSTRIPE_WEBHOOK_SECRET = os.getenv( "DJSTRIPE_WEBHOOK_SECRET" )  # Get it from the section in the Stripe dashboard where you added the webhook endpoint
DJSTRIPE_USE_NATIVE_JSONFIELD = (True if os.getenv( "DJSTRIPE_USE_NATIVE_JSONFIELD" ) == 'True' else False)  # We recommend setting to True for new installations
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"  # Set to `"id"` for all new 2.4+ installations
STRIPE_DASHBOARD_URL = os.getenv("STRIPE_DASHBOARD_URL")

CAMPAIGN = os.getenv("CAMPAIGN")
TEAM_PLANS = os.getenv("TEAM_PLANS", "").split(',')



 

#### Ailaysa

AILAYSA_EMAILS = os.environ.get("AILAYSA_EMAILS")

########TAMIL_SPELLCHECKER_URL

TAMIL_SPELLCHECKER_URL = os.getenv('TAMIL_SPELLCHECKER_URL')


########### TERM EXTRACTION #####

TERM_EXTRACTION = os.getenv('TERM_EXTRACTION')

##### FINDING POS #####

IDENTIFY_POS = os.getenv('IDENTIFY_POS')

### FINDING LEMMA ####
IDENTIFY_LEMMA = os.getenv('IDENTIFY_LEMMA')
IDENTIFY_LEMMA_GLOSS = os.getenv('IDENTIFY_LEMMA_GLOSS')

### GEMINI API ####
GOOGLE_GEMINI_API = os.getenv('GOOGLE_GEMINI_API')
GOOGLE_GEMINI_MODEL = os.getenv('GOOGLE_GEMINI_MODEL')
GOOGLE_TERM_EXTRACTION = os.getenv('GOOGLE_TERM_EXTRACTION')

## ANTHROPIC_API_KEY
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_MODEL_NAME = os.getenv('ANTHROPIC_MODEL_NAME')

## DEEPL_API_KEY 
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')

### DEEPL_USERS_LIST
DEEPL_USER_LIST = os.getenv('DEEPL_USER_LIST')

NOTEBOOK_ARGUMENTS = [
"--ip",
"0.0.0.0",
"--port",
"8888",
"--allow-root",
"--no-browser",
]
COHERE_MODEL=os.getenv("COHERE_MODEL","")


## OPENAI 

OPENAI_MODEL_NAME_ADAPT = os.getenv('OPENAI_MODEL_NAME_ADAPT')
ADAPTIVE_INDIAN_LANGUAGE = os.getenv('ADAPTIVE_INDIAN_LANGUAGE')
ALTERNATE_GEMINI_MODEL = os.getenv('ALTERNATE_GEMINI_MODEL')
ADAPTIVE_STYLE_LLM_MODEL = os.getenv('ADAPTIVE_STYLE_LLM_MODEL')
ADAPTIVE_STYLE_LLM_PROVIDER = os.getenv('ADAPTIVE_STYLE_LLM_PROVIDER')
ADAPTIVE_TRANSLATE_LLM_PROVIDER = os.getenv('ADAPTIVE_TRANSLATE_LLM_PROVIDER')
ADAPTIVE_TRANSLATE_LLM_MODEL = os.getenv('ADAPTIVE_TRANSLATE_LLM_MODEL')
ADAPTIVE_SPLIT_INPUT_SIZE = int(os.getenv('ADAPTIVE_SPLIT_INPUT_SIZE', 250))
ADAPTIVE_RESPONSE_STREAM = (True if os.getenv('ADAPTIVE_RESPONSE_STREAM') == 'True' else False) 