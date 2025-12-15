from flask import Flask, render_template, request, jsonify
import mysql.connector
from mysql.connector import Error as MySQLError
import requests
import json

app = Flask(__name__)

# Database config
db_config = {
    'host': '127.0.0.1',
    'user': 'root', 
    'password': '',     # MySQL password (need to change accordingly)
    'database': 'bio_project'
}

# Database connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Fetch daata from UniProt API
def fetch_uniprot_data(uniprot_id):
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}?format=json"
    print(f"  Fetching {uniprot_id} from {url}...")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        name = data.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', 'Unknown')
        sequence = data.get('sequence', {}).get('value', '')
        
        pdb_refs = []
        
        if 'uniProtKBCrossReferences' in data:
            for ref in data['uniProtKBCrossReferences']:
                if ref['database'] == 'PDB':
                    pdb_id = ref['id']
                    
                    # Default values
                    method = 'N/A'
                    resolution = 0.0
                    
                    properties_list = ref.get('properties', [])
                    for prop in properties_list:
                        if prop.get('key') == 'Method':
                            method = prop.get('value', 'N/A')
                        
                        if prop.get('key') == 'Resolution':
                            resolution_str = prop.get('value', '0.0 A').split(' ')[0]
                            try:
                                resolution = float(resolution_str)
                            except ValueError:
                                resolution = 0.0
                    
                    pdb_refs.append({
                        'id': pdb_id,
                        'method': method,
                        'resolution': resolution,
                        'title': f"Structure of {name}"
                    })
        
        return {
            'uniprot_id': uniprot_id,
            'name': name,
            'sequence': sequence,
            'pdb_refs': pdb_refs
        }

    except requests.exceptions.RequestException as e:
        print(f"  ERROR fetching {uniprot_id}: {e}")
        return None

# Load data to MySQL db
def load_data_to_db(protein_data):
    if not protein_data:
        return

    print(f"  Loading {protein_data['uniprot_id']} into database...")
    
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Load into protein table
        sql_protein = "INSERT IGNORE INTO protein (uniprot_id, name, sequence) VALUES (%s, %s, %s)"
        val_protein = (protein_data['uniprot_id'], protein_data['name'], protein_data['sequence'])
        c.execute(sql_protein, val_protein)
        
        # Load into pdb_structure/map table
        for pdb in protein_data['pdb_refs']:
            sql_pdb = "INSERT IGNORE INTO pdb_structure (pdb_id, method, resolution, title) VALUES (%s, %s, %s, %s)"
            val_pdb = (pdb['id'], pdb['method'], pdb['resolution'], pdb['title'])
            c.execute(sql_pdb, val_pdb)
            
            sql_map = "INSERT IGNORE INTO protein_structure_map (uniprot_id, pdb_id) VALUES (%s, %s)"
            val_map = (protein_data['uniprot_id'], pdb['id'])
            c.execute(sql_map, val_map)

        conn.commit()
        print(f"  Successfully loaded {protein_data['uniprot_id']}.")

    except MySQLError as e:
        print(f"  Database error: {e}")
        conn.rollback()
    finally:
        if 'conn' in locals() and conn.is_connected():
            c.close()
            conn.close()

# Routes --------------------------------------------------

# Homepage, small intro, search bar, "featured examples", some basic stats etc.
@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) 
    
    # Homepage stats
    
    # Count proteins and structures
    cursor.execute("SELECT COUNT(*) as count FROM protein")
    res_p = cursor.fetchone()
    protein_count = res_p['count'] if res_p else 0
    
    cursor.execute("SELECT COUNT(*) as count FROM pdb_structure")
    res_s = cursor.fetchone()
    structure_count = res_s['count'] if res_s else 0
    
    # Select 10 random proteins for "featured examples"
    cursor.execute("SELECT uniprot_id, name FROM protein ORDER BY RAND() LIMIT 10")
    example_proteins = cursor.fetchall()
    
    conn.close()
    
    return render_template('home.html', 
                           p_count=protein_count, 
                           s_count=structure_count, 
                           examples=example_proteins)



# Search results: including stats, along with auto update functionality should the db not contain thee search
@app.route('/search')
def search():
    """Search result page """
    query = request.args.get('query', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Intial Search
    sql = """
    SELECT p.uniprot_id, p.name, p.sequence, s.pdb_id, s.method, s.resolution 
    FROM protein p
    JOIN protein_structure_map m ON p.uniprot_id = m.uniprot_id
    JOIN pdb_structure s ON m.pdb_id = s.pdb_id
    WHERE p.name LIKE %s OR p.uniprot_id LIKE %s
    """
    search_term = f"%{query}%"
    cursor.execute(sql, (search_term, search_term))
    results = cursor.fetchall()
    
    # Auto update if not in db
    if not results and len(query) >= 6:
        print(f"Protein '{query}' not found in DB. Attempting to fetch from web...")
        new_data = fetch_uniprot_data(query)
        if new_data:
            load_data_to_db(new_data)
            conn.commit()
            # Search again to get the new data
            cursor.execute(sql, (search_term, search_term))
            results = cursor.fetchall()
    
    # Logic for chart stats
    method_stats = {}
    for row in results:
        m = row['method']
        if not m:
            m = "Unknown"
        method_stats[m] = method_stats.get(m, 0) + 1
        
    conn.close()
    
    return render_template('result.html', results=results, query=query, stats=method_stats)

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/api/protein/<uniprot_id>')
def api_get_protein(uniprot_id):
    """REST API Endpoint"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM protein WHERE uniprot_id = %s", (uniprot_id,))
    protein = cursor.fetchone()
    
    conn.close()
    
    if protein:
        return jsonify(protein)
    else:
        return jsonify({"error": "Protein not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)