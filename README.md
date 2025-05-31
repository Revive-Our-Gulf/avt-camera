# avt-camera

## Installation
```
mkdir ~/Repos
cd ~/Repos
git clone https://github.com/Revive-Our-Gulf/avt-camera.git
cd avt-camera
```
### Setup Virtual Environment
```
python -m venv 'venv'
source venv/bin/activate
````
### Install Requirements
```
pip install -r requirements.txt
```
### Setup service
```
sudo ./install.sh
```

## BlueOS Setup
Go to MAVLink Endpoints.
Create a new endpoint by clicking the plus button in the bottom right hand corner
Give it the following settings:

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
