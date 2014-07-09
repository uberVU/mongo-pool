from mongopool import MongoPool
from pkg_resources import get_distribution, DistributionNotFound
import os.path

__all__ = ['mongopool']

try:
    _dist = get_distribution('mongopool')
    if not __file__.startswith(os.path.join(_dist.location, 'mongopool')):
        # not installed, but there is another version that *is*
        raise DistributionNotFound
except DistributionNotFound:
    __version__ = 'Please install this project with setup.py'
else:
    __version__ = _dist.version
