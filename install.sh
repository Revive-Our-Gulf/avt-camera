#!/bin/bash

sudo cp avt-camera.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable avt-camera.service

sudo systemctl start avt-camera.service
sudo systemctl status avt-camera.service