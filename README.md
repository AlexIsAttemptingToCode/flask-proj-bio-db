# BioDB Explorer

**BioDB Explorer** is a Flask-based web application that serves as a custom structural biology database.

The web interface shows data from UniProt and RCSB PDB, including sequence and a table of the available 3D structures.

It incorporates a Lazy Loading function, if the protein is not found within thee database an attempt will be made to retrieve the corresponding data from UniProt API.

**REST API** is available for example via: /api/protein/P0DTC2


* **Backend:** Python 3, Flask
* **Database:** MySQL
* **Frontend:** HTML5, CSS3, Bootstrap 5, Chart.js, FontAwesome
* **External APIs:** UniProt REST API
  
## Installation & Setup

### Prerequisites
* Python 3.8 or higher
* MySQL Server

An environment via conda can be created using the **environment.yml** file via:
```
conda env create -f environment.yml -n <desired_name>
```
The required packages can be viewed in the same file otherwise.


## IMPORTANT!
Th database can be crated using the associated dumpfile within the repository in MySQL.

The db_config may need to be modified within **app.py** if anything varies such as user or password:
```
db_config = {

    'host': '127.0.0.1',  # Hostname also commonnly 'host'
    
    'user': 'root',       # Your MySQL username
    
    'password': '',       # Your MySQL password
    
    'database': 'bio_project'
}
```
