import logging
from ecms_admin_portal.server import make_app

logging.root.setLevel(logging.NOTSET)

application=make_app()