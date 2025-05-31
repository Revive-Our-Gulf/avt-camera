# avt-camera

## Overview
Camera control system for the AVT G1 IMX304 GigE down camera

### Features
- Live camera preview and recording
- Camera parameter configuration
- File management for recordings
- MAVLink integration with BlueOS

## Access
The camera can be accessed through:
- http://camera.local
- http://192.168.2.3:80

### Pages
- Home: http://camera.local/
- Cockpit: http://camera.local/cockpit 
- Camera parameters: http://camera.local/parameters
- Application settings: http://camera.local/app_settings
- Files: http://camera.local/files
    - The file manager can also be accessed with http://192.168.2.3:8080 even if the camera service is not running


## Installation
1. Clone the repository:
```
mkdir ~/Repos
cd ~/Repos
git clone https://github.com/Revive-Our-Gulf/avt-camera.git
cd avt-camera
```
2. Setup Python virtual environment:
```
python -m venv 'venv'
source venv/bin/activate
````
3. Install required packages:
```
pip install -r requirements.txt
```
4. Install the avt-camera service:
```
sudo ./install.sh
```

## BlueOS Setup
BlueOS MAVLink Setup
1. Navigate to MAVLink Endpoints in BlueOS
2. Create a new endpoint (click + button in bottom right corner)
3. Use the following settings:

![BlueOS MAVLink Endpoint Setup](docs/images/blueos-mavlink-endpoint.png)


## Restarting Service
```
sudo systemctl restart avt-camera.service
```

## Manually Running Code
```
sudo systemctl stop avt-camera.service
cd ~/Repos/avt-camera
source venv/bin/activate
authbind -deep python app/main.py
```
