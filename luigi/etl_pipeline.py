import os
import luigi
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Charger les variables d'environnement à partir du fichier.env
load_dotenv()

# Charger les variables d'environnement
moben_db_creds = {
    'host': os.getenv('POSTGRES_MOBEN_HOST'),
    'port': os.getenv('POSTGRES_MOBEN_PORT'),
    'user': os.getenv('POSTGRES_MOBEN_USER'),
    'password': os.getenv('POSTGRES_MOBEN_DBPASS'),
    'name': os.getenv('POSTGRES_MOBEN_DBNAME'),
    'type': os.getenv('POSTGRES_MOBEN_DBTYPE')
}

# Vérifier si la variable d'environnement 'POSTGRES_MOBEN_PORT' est un nombre entier
if moben_db_creds['port'] is None or not moben_db_creds['port'].isdigit():
    raise ValueError("La variable d'environnement 'POSTGRES_MOBEN_PORT' doit être un nombre entier.")

# Convertir le port en entier
moben_db_creds['port'] = int(moben_db_creds['port'])

# Construire l'URL de connexion
sqlalchemy_db_uri_conn = f"{moben_db_creds['type']}://{moben_db_creds['user']}:{moben_db_creds['password']}@{moben_db_creds['host']}:{moben_db_creds['port']}/{moben_db_creds['name']}"

# Créer l'engine de connexion
engine = create_engine(sqlalchemy_db_uri_conn)

# Tâche d'extraction des données
class ExtractData(luigi.Task):
    def run(self):
        # Extraire les données d'un fichier CSV
        input_file = rf"C:\Users\mylen\OneDrive\Documents\Veille\ETL\luigi\comorbidites.csv"
        data = pd.read_csv(input_file, sep=';', encoding="utf-8")
        output_file = 'extracted_data.csv'
        data.to_csv(output_file, index=False)

    def output(self):
        # Spécifier le fichier de sortie
        return luigi.LocalTarget('extracted_data.csv')

# Tâche de transformation des données
class TransformData(luigi.Task):
    def requires(self):
        # Dépendance de la tâche d'extraction
        return ExtractData()

    def run(self):
        # Lire les données extraites et effectuer des transformations
        input_file = self.input().path
        data = pd.read_csv(input_file)
        # Exemple de transformation : supprimer les doublons
        data = data.drop_duplicates()
        output_file = 'transformed_data.csv'
        data.to_csv(output_file, index=False)

    def output(self):
        # Spécifier le fichier de sortie transformé
        return luigi.LocalTarget('transformed_data.csv')

# Tâche de chargement des données
class LoadData(luigi.Task):
    def requires(self):
        # Dépendance de la tâche de transformation
        return TransformData()

    def run(self):
        # Se connecter à la base de données
        # Utiliser l'engine de connexion créé plus haut
        # Lire les données transformées et les charger dans la base de données
        input_file = self.input().path
        data = pd.read_csv(input_file)
        data.to_sql('your_table_name', engine, if_exists='replace', index=False)

    def output(self):
        # Spécifier le fichier de sortie pour marquer la tâche comme terminée
        return luigi.LocalTarget('loaded_data.txt')

if __name__ == '__main__':
    # Exécuter le pipeline ETL avec Luigi
    import sys
    sys.path.insert(0, './')
    import luigi
    luigi.run(['--module', 'etl_pipeline', 'LoadData', '--local-scheduler'])