import logging
from ecms_applicant_portal.server import make_app

logging.root.setLevel(logging.NOTSET)

application=make_app()