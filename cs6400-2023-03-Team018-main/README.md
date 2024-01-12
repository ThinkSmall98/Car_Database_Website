# cs6400-2023-03-Team018
Overview 

This guide provides step-by-step instructions for setting up and running our website in a Conda environment using Python 3.10. 

The project dependencies are specified in the requirements.txt file.

## Prerequisites

- [Conda](https://docs.conda.io/en/latest/) installed on your system.

## Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.gatech.edu/cs6400-2023-03-fall/cs6400-2023-03-Team018.git
   cd cs6400-2023-03-Team018
   ```

2. **Create a Conda Environment:**
   ```bash
   conda create --name website-env python=3.10
   ```
3. **Activate the Conda Environment:**
   ```bash
   conda activate website-env
   conda install pip
   ```
4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Running the Website**
   If not already activated:
   ```bash
   conda activate website-env
   ```
   Export flask_app variable and run flask:
   ```bash
   export FLASK_APP=car_retail
   flask run
   ```

6. **Access the Website:**

   Open your web browser and navigate to http://127.0.0.1:5000 to view your website.
