# -*- coding: utf-8 -*-
from enum import Enum
from typing import NamedTuple

from .. import mgr


class ClusterCapacity(NamedTuple):
    total_avail_bytes: int
    total_bytes: int
    total_used_raw_bytes: int
    total_objects: int
    total_pool_bytes_used: int
    average_object_size: int


class ClusterModel:

    class Status(Enum):
        INSTALLED = 0
        POST_INSTALLED = 1

    status: Status

    def __init__(self, status=Status.POST_INSTALLED.name):
        """
        :param status: The status of the cluster. Assume that the cluster
            is already functional by default.
        :type status: str
        """
        self.status = self.Status[status]

    def dict(self):
        return {'status': self.status.name}

    def to_db(self):
        mgr.set_store('cluster/status', self.status.name)

    @classmethod
    def from_db(cls):
        """
        Get the stored cluster status from the configuration key/value store.
        If the status is not set, assume it is already fully functional.
        """
        return cls(status=mgr.get_store('cluster/status', cls.Status.POST_INSTALLED.name))

    @classmethod
    def get_capacity(cls) -> ClusterCapacity:
        df = mgr.get('df')
        total_objects = 0
        total_pool_bytes_used = 0
        average_object_size = 0
        rgw_pools = cls.get_rgw_pools()
        for pool in df['pools']:
            if pool['name'] in rgw_pools:
                total_objects = total_objects + pool['stats']['objects']
                total_pool_bytes_used = total_pool_bytes_used + pool['stats']['bytes_used']
        if total_objects != 0:
            average_object_size = total_pool_bytes_used / total_objects
        return ClusterCapacity(total_avail_bytes=df['stats']['total_avail_bytes'],
                               total_bytes=df['stats']['total_bytes'],
                               total_used_raw_bytes=df['stats']['total_used_raw_bytes'],
                               total_objects=total_objects,
                               total_pool_bytes_used=total_pool_bytes_used,
                               average_object_size=average_object_size)._asdict()

    @classmethod
    def get_rgw_pools(cls):
        rgw_pool_names = []
        osd_map = mgr.get('osd_map')
        for pool in osd_map['pools']:
            if 'rgw' in pool.get('application_metadata', {}):
                rgw_pool_names.append(pool['pool_name'])
        return rgw_pool_names
