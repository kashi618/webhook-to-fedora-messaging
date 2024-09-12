#!/bin/bash

# SPDX-FileCopyrightText: Contributors to the Fedora Project
#
# SPDX-License-Identifier: GPL-3.0-or-later

exec uvicorn \
	--host 0.0.0.0 --port 8080 \
	--log-config /etc/webhook-to-fedora-messaging/logging.yaml \
	--proxy-headers --forwarded-allow-ips='*' \
	--factory webhook_to_fedora_messaging.main:create_app
