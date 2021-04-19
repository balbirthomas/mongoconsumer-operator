#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import os
import json
import logging
import pymongo

from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    WaitingStatus,
    MaintenanceStatus
)

from oci_image import OCIImageResource, OCIImageResourceError
from charms.mongodb.v1.mongodb import MongoConsumer

logger = logging.getLogger(__name__)


class MongoconsumerCharm(CharmBase):
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.mongo_consumer = MongoConsumer(self, 'database',
                                            self.consumes)
        self.image = OCIImageResource(self, "busybox-image")
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        self.framework.observe(self.mongo_consumer.on.available, self.on_db_available)
        self.framework.observe(self.mongo_consumer.on.invalid, self.on_provider_invalid)
        self.framework.observe(self.mongo_consumer.on.broken, self.on_provider_broken)
        self._stored.set_default(events=[])
        self._stored.set_default(num_dbs=2)
        self._stored.set_default(requested_dbs=0)

    def on_stop(self, _):
        """Mark terminating unit as inactive
        """
        if self.model.config['record_events']:
            self._stored.events.append("config_chagned")

        self.unit.status = MaintenanceStatus('Pod is terminating.')

    def on_config_changed(self, _):
        if self.model.config['record_events']:
            self._stored.events.append("config_chagned")

        if not self.unit.is_leader():
            self.unit.status = ActiveStatus()
            return

        self.configure_pod()

    def on_db_available(self, event):
        if self.model.config['record_events']:
            self._stored.events.append("db_available")

        logger.debug("Got Databases: " + str(self.mongo_consumer.databases()))
        if self._stored.requested_dbs < self._stored.num_dbs:
            num_dbs = self._stored.num_dbs - self._stored.requested_dbs
            logger.debug("Requesting additional {} databases".format(num_dbs))
            for i in range(num_dbs):
                self.mongo_consumer.new_database()
                self._stored.requested_dbs += 1
        else:
            self.test_databases()

    def on_provider_invalid(self, _):
        if self.model.config['record_events']:
            self._stored.events.append("provider_invalid")

        logger.debug("Failed to get a valid provider")

    def on_provider_broken(self, _):
        logger.debug("Database provider relation broken")

    def test_databases(self):
        for id in self.mongo_consumer.provider_ids():
            creds = self.mongo_consumer.credentials(id)
            uri = creds['replica_set_uri']
            client = pymongo.MongoClient(uri)
            for dbname in self.mongo_consumer.databases(id):
                post = {"test": "A test post"}
                logger.debug("writing {} to {}".format(post, dbname))
                db = client[dbname]
                tbl = db["test"]
                tbl.insert_one(post)
                posts = list(tbl.find())
                logger.debug("read {} from {}".format(posts, dbname))

    def configure_pod(self):
        logger.debug(str(sorted(os.environ.items())))
        # Fetch image information
        try:
            self.unit.status = WaitingStatus("Fetching image information")
            image_info = self.image.fetch()
        except OCIImageResourceError:
            self.unit.status = BlockedStatus(
                "Error fetching image information")
            return

        # Build Pod spec
        self.unit.status = WaitingStatus("Assembling pod spec")

        pod_spec = {
            "version": 3,
            "containers": [
                {
                    "name": self.app.name,
                    "imageDetails": image_info,
                    "command": ["sh"],
                    "args": ["-c", "while true; do date; sleep 60;done"],
                    "imagePullPolicy": "Always",
                    "ports": [{
                        "name": self.app.name,
                        "containerPort": 80,
                        "protocol": "TCP"
                    }]
                }
            ]
        }

        if self.unit.is_leader():
            self.model.pod.set_spec(pod_spec)
            self.unit.status = ActiveStatus()

    @property
    def consumes(self):
        return json.loads(self.model.config['consumes'])


if __name__ == "__main__":
    main(MongoconsumerCharm)
