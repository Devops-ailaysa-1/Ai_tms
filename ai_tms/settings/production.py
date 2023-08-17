# Django Production Settings
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import newrelic.agent
from newrelic.agent import NewRelicContextFormatter
newrelic.agent.initialize('newrelic.ini')
# from fluent import sender
# from fluent import event
# sender.setup('django', host='fluentd', port=24224)
# event.Event('follow', {
#   'from': 'userA',
#   'to':   'userB'
# })

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# TEMPLATE_DIR = os.path.join(BASE_DIR,'ai_staff','templates')
# TEMPLATE_DIR_2 = os.path.join(BASE_DIR,'ai_vendor','templates')
# TEMPLATE_DIR_3 = os.path.join(BASE_DIR,'ai_marketplace','templates')
# TEMPLATE_DIR_4 = os.path.join(BASE_DIR,'ai_auth','templates')
# TEMPLATE_DIR_5 = os.path.join(BASE_DIR,'ai_tms','templates')
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = os.getenv("django_secret_key", "fwevbsuio")

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = (True if os.getenv( "Debug" ) == 'True' else False)

# ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split()

# ALLOWED_HOSTS += ["11e41bb54bb45b.lhrtunnel.link", "d96ada36139e0b.lhrtunnel.link","8efe68d97d25ee.lhrtunnel.link"]
# #                   "c3c0df83ac1b86.lhrtunnel.link", 'acb69157d8c89a.lhrtunnel.link',
# #                   "414004b4a51963.lhrtunnel.link", "2b80a8d1a40052.lhrtunnel.link",
# #                   "d5db75cdd4b431.lhrtunnel.link", "68a4a1352f7fdb.lhrtunnel.link"]

# SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE')
# CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE')
# SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT")

# CORS_ORIGIN_ALLOW_ALL= False

# CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split()

# CORS_ORIGIN_WHITELIST = os.getenv("CORS_ORIGIN_WHITELIST", "").split()

# CORS_ALLOW_CREDENTIALS = (True if os.getenv( "CORS_ALLOW_CREDENTIALS" ) == 'True' else False)


# JWT_AUTH_COOKIE_USE_CSRF= True

# CORS_ORIGIN_ALLOW_ALL = True
# CORS_ORIGIN_WHITELIST = [
#     "http://localhost:3000" , "http://167.71.235.214:3000","http://157.245.99.128:3010","http://157.245.99.128:3020"
# ]
# CORS_ALLOWED_ORIGINS = ["http://localhost:3000" , "http://167.71.235.214","http://157.245.99.128:3010","http://157.245.99.128:3020" ]

# CORS_ALLOW_METHODS = [
#      'DELETE',
#      'GET',
#      'OPTIONS',
#      'PATCH',
#      'POST',
#      'PUT',
# ]

# CORS_ALLOW_HEADERS = [
#      'accept',
#      'accept-encoding',
#      'authorization',
#      'content-type',
#      'dnt',
#      'origin',
#      'user-agent',
#      'x-csrftoken',
#      'x-requested-with',
#      'Access-Control-Allow-Origin',
#      'Access-Control-Allow-Credentials',
#      'Access-Control-Allow-Headers',
#      'cache',
#      'cookie',
#      'Access-Control-Expose-Headers',
#      'responseType',
#      'redirect',
# ]

CSRF_TRUSTED_ORIGINS =+ [
 "http://localhost:3000",  "http://localhost:4200"
]

#SESSION_COOKIE_SAMESITE = None
#CSRF_COOKIE_SAMESITE = None
# Application definition

INSTALLED_APPS += [
    'dbbackup',
]


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

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


# if os.environ.get("email_creds_avail", False):
# EMAIL_BACKEND = 'ai_auth.email_backend.AiEmailBackend'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv( "EMAIL_HOST" )
EMAIL_PORT = int(os.getenv( "EMAIL_PORT" )) if os.getenv("EMAIL_PORT") else None
EMAIL_USE_TLS = (True if os.getenv( "EMAIL_TLS" ) == 'True' else False)
EMAIL_HOST_USER = os.getenv( "EMAIL_HOST_USER" )
EMAIL_HOST_PASSWORD = os.getenv( "EMAIL_HOST_PASSWORD" )


#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CACHEOPS_REDIS = os.getenv("CACHEOPS_REDIS_HOST")

CACHEOPS_ENABLED = True

CACHEOPS_DEGRADE_ON_FAILURE = True 

CACHEOPS_DEFAULTS = {
    'timeout': 60 * 60,  # Default cache timeout (1 hour)
}

CACHEOPS = {
   # 'ai_workspace.*': {'ops': 'all', 'timeout': 60 * 30},
    'ai_staff.*': {'ops': 'all', 'timeout': 60*60},
    #'ai_worksapce.task':{'ops':'all','timeout': 60 * 15},
    
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

# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#           'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
#         #'rest_framework_simplejwt.authentication.JWTAuthentication',
#     ],
#     'DEFAULT_PAGINATION_CLASS':
#         'rest_framework.pagination.PageNumberPagination',
#     'PAGE_SIZE': 12,
#     'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.IsAuthenticated',
#     ],
#     # 'DEFAULT_THROTTLE_CLASSES': [
#     # 'rest_framework.throttling.AnonRateThrottle',
#     # 'rest_framework.throttling.UserRateThrottle'
#     # ],
#     # 'DEFAULT_THROTTLE_RATES': {
#     #     'anon': '50/minute',
#     #     'user': '100/minute'
#     # }
# }


# SOCIALACCOUNT_ADAPTER="ai_auth.ai_adapter.SocialAdapter"

# SOCIALACCOUNT_PROVIDERS = {
#     'github': {
#         'SCOPE': [
#             'user',
#             'repo',
#             'read:org',
#         ],
#     },
#     'google': {
#         'SCOPE': [
#             'profile',
#             'email',
#         ],
#         'AUTH_PARAMS': {
#             'access_type': 'offline',
#         }
# }
# }





# OLD_PASSWORD_FIELD_ENABLED = True

# SIMPLE_JWT = {
#     'ACCESS_TOKEN_LIFETIME': timedelta(hours=5),
#     'REFRESH_TOKEN_LIFETIME': timedelta(days=1),}
#     'ROTATE_REFRESH_TOKENS': False,
#     'BLACKLIST_AFTER_ROTATION': True,
#     'UPDATE_LAST_LOGIN': False,

    # 'ALGORITHM': 'HS256',
    # 'SIGNING_KEY': os.getenv( "JWT_SECRET_KEY" ),
#     'VERIFYING_KEY': None,
#     'AUDIENCE': None,
#     'ISSUER': None,

#     'AUTH_HEADER_TYPES': ('Bearer',),
#     'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
#     'USER_ID_FIELD': 'id',
#     'USER_ID_CLAIM': 'user_id',
#     'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

#     'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
#     'TOKEN_TYPE_CLAIM': 'token_type',

#     'JTI_CLAIM': 'jti',

#     'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
#     'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
#     'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),

#     # new added
#     'AUTH_COOKIE': 'access_token',  # Cookie name. Enables cookies if value is set.
#     'AUTH_COOKIE_DOMAIN': None,     # A string like "example.com", or None for standard domain cookie.
#     'AUTH_COOKIE_SECURE': False,    # Whether the auth cookies should be secure (https:// only).
#     'AUTH_COOKIE_HTTP_ONLY' : True, # Http only cookie flag.It's not fetch by javascript.
#     'AUTH_COOKIE_PATH': '/',        # The path of the auth cookie.
#     'AUTH_COOKIE_SAMESITE': 'Lax',  # Whether to set the flag restricting cookie leaks on cross-site requests.
#                                 # This can be 'Lax', 'Strict', or None to disable the flag.
# CELERY_BROKER_URL = "redis://:ainlp2022@redis:6379/0"
# export CELERY_BROKER_URL = 'redis://localhost:6379/0'
# export CELERY_BACKEND_URL = 'redis://redis:6379/0'


CACHEOPS_REDIS = os.getenv("CACHEOPS_REDIS_HOST")

# CACHEOPS_DEFAULTS = {
#     'timeout': 60*60
# }

# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": os.getenv("CACHEOPS_REDIS_HOST"),
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         }
#     }
#     }

CACHEOPS = {

    # Cache all queries to Permission
    # 'all' is an alias for {'get', 'fetch', 'count', 'aggregate', 'exists'}
    'ai_staff.*': {'ops': 'all', 'timeout': 60*60},


    # # And since ops is empty by default you can rewrite last line as:
    # '*.*': {'timeout': 60*60},

    # # NOTE: binding signals has its overhead, like preventing fast mass deletes,
    # #       you might want to only register whatever you cache and dependencies.

    # # Finally you can explicitely forbid even manual caching with:
    # 'some_app.*': None,
}




# DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE ='storages.backends.s3boto3.S3Boto3Storage'

DBBACKUP_STORAGE_OPTIONS = {
    'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
    'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
    'bucket_name': os.getenv('AWS_STORAGE_BUCKET_NAME'),
    'endpoint_url': 'https://ams3.digitaloceanspaces.com',
    'default_acl': 'private',
    'location': os.getenv('MEDIA_BACKUP_LOCATION')

}



LOGGING = {
    'version' : 1,
    'disable_existing_loggers' : False,

    'formatters' : {
        'dev_formatter' : {
            'format' : '{levelname} {asctime} {pathname} {message}',
            'style' : '{',
        },
        'newrelic_formatter': {
            '()': NewRelicContextFormatter,
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
            'handlers' : ['file_prod','newrelic'],
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
        'newrelic': {
            'level': os.environ.get("LOGGING_LEVEL_NEW_RELIC"),
            'class': 'logging.StreamHandler',
            'formatter' : 'newrelic_formatter',
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


sentry_sdk.init(
    dsn = os.getenv("dsn"),
    integrations=[DjangoIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate = os.getenv("traces_sample_rate"),

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii = os.getenv("send_default_pii")
)



DBBACKUP_CLEANUP_KEEP_MEDIA = int(os.getenv("DBBACKUP_CLEANUP_KEEP_MEDIA"))