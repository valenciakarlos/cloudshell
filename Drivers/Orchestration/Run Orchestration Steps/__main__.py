import os
from steps import go

go(False, include_ranges=os.environ['INCLUDE_RANGES'], exclude_ranges=os.environ['EXCLUDE_RANGES'])