# Biosensing API

[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/powered-by-coffee.svg)](https://forthebadge.com)

## Description
The Biosensing API is an API that streams real-time data from Polar heart rate sensors. It transmits real-time data such as heartbeats, RR peaks, and HRV.

## Installation

1. Clone the repository
```bash
   git clone https://github.com/tu-usuario/tu-aplicacion.git
```
2. Create an enviroment (optional but recommended)
```bash
   python3 -m venv venv
```

3. Activate the virtual environment
```bash
   source venv/bin/activate
```

4. Install requirements
```bash
   pip3 install -r requirements.txt
```

## Running the API
```bash
   uvicorn app:app --reload
```


## License

Licensed under the MIT License, Copyright © 2023-present Servir