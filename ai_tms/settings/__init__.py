from .base import *
import os


if os.environ.get("ENV_NAME") == 'Production':
    from .production import *
elif os.environ.get("ENV_NAME") == 'Staging':
    from .staging import *
elif os.environ.get("ENV_NAME") == 'Testing':
    from .testing import *
else:
    from .local import *