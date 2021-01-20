#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import os
import logging

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
from mongoclient import MongoConsumer

logger = logging.getLogger(__name__)


class MongoconsumerCharm(CharmBase):
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.mongodb = MongoConsumer(self, 'database',
                                     self.model.config['consumes'])
        self.image = OCIImageResource(self, "busybox-image")
        self.framework.observe(self.on.config_changed, self.on_config_changed)
        self.framework.observe(self.mongodb.on.db_available, self.on_db_available)
        self.framework.observe(self.mongodb.on.provider_invalid, self.on_provider_invalid)
        self._stored.set_default(events=[])

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
        logger.debug("GOTDB: " + str(event.config))

    def on_provider_invalid(self, _):
        logger.debug("FAILEDDB")

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
                    "args": ["-c", "while true; do env && date; sleep 5;done"],
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


if __name__ == "__main__":
    main(MongoconsumerCharm)
