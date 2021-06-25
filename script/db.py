
from models import *
from liquid.models import *

def create_table(**kwargs):
    Model.metadata.create_all()